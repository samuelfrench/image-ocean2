"""Write the Hugging Face dataset card (README.md) and its image assets.

usage: python scripts/hf_dataset/make_card.py --out OUTDIR --png-dir DIR --repo-id USER/NAME
           [--sweep-prompt-id N]

Reads OUTDIR/metadata/metadata.parquet and OUTDIR/build-report.json (written by
build_shards.py) and writes OUTDIR/README.md plus OUTDIR/assets/:
  sample-grid.jpg     one high-scoring image per category
  seed-sweep.jpg      one prompt, 8 seeds spread across its aesthetic-score range
  category-counts.png images per category
  seed-spread.png     per-prompt LAION aesthetic range across seeds
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

SURFACE = "#fcfcfb"
SERIES = "#2a78d6"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
TILE = 400


def font(size: int) -> ImageFont.ImageFont:
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def tile(png: Path, label: str) -> Image.Image:
    im = Image.open(png).convert("RGB")
    s = min(im.size)
    left, top = (im.width - s) // 2, (im.height - s) // 2
    im = im.crop((left, top, left + s, top + s)).resize((TILE, TILE), Image.LANCZOS)
    d = ImageDraw.Draw(im, "RGBA")
    f = font(17)
    w = d.textlength(label, font=f)
    d.rectangle((0, TILE - 30, w + 16, TILE), fill=(0, 0, 0, 170))
    d.text((8, TILE - 26), label, font=f, fill=(255, 255, 255, 255))
    return im


def grid(tiles: list[Image.Image], cols: int) -> Image.Image:
    rows = (len(tiles) + cols - 1) // cols
    g = Image.new("RGB", (cols * TILE + (cols - 1) * 4, rows * TILE + (rows - 1) * 4), SURFACE)
    for i, t in enumerate(tiles):
        g.paste(t, ((i % cols) * (TILE + 4), (i // cols) * (TILE + 4)))
    return g


def style(ax) -> None:
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelcolor=INK_2)


def category_chart(m: pd.DataFrame, path: Path) -> None:
    c = m["category"].value_counts().sort_values()
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=150, facecolor=SURFACE)
    style(ax)
    bars = ax.barh(c.index, c.values, color=SERIES, height=0.62)
    ax.bar_label(bars, labels=[f"{v:,}" for v in c.values], padding=4, color=INK_2, fontsize=9)
    ax.set_xlabel("Images", color=INK_2)
    ax.set_title(f"Images per category (n = {len(m):,})", color=INK, loc="left", fontsize=12)
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_xlim(0, c.max() * 1.15)
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def spread_chart(m: pd.DataFrame, path: Path) -> pd.DataFrame:
    g = m.groupby("prompt_id")["laion_aesthetic"]
    s = pd.DataFrame({"n": g.size(), "p10": g.quantile(0.1), "p50": g.median(), "p90": g.quantile(0.9)})
    s = s[s["n"] >= 20].sort_values("p50").reset_index()
    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=150, facecolor=SURFACE)
    style(ax)
    x = range(len(s))
    ax.vlines(x, s["p10"], s["p90"], color=SERIES, alpha=0.45, linewidth=2)
    ax.scatter(x, s["p50"], s=8, color=SERIES, zorder=3)
    ax.set_xticks([])
    ax.set_xlabel(f"{len(s)} prompts with 20+ seeds, sorted by median score", color=INK_2)
    ax.set_ylabel("LAION aesthetic score (v2)", color=INK_2)
    ax.set_title(
        "Same prompt, different seeds: 10th–90th percentile score range (line) and median (dot)",
        color=INK, loc="left", fontsize=11,
    )
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)
    return s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--png-dir", required=True, type=Path)
    ap.add_argument("--repo-id", required=True)
    ap.add_argument("--sweep-prompt-id", type=int, help="prompt for the seed-sweep grid (default: auto)")
    args = ap.parse_args()

    m = pd.read_parquet(args.out / "metadata" / "metadata.parquet")
    report = json.loads((args.out / "build-report.json").read_text())
    assets = args.out / "assets"
    assets.mkdir(exist_ok=True)
    base = f"https://huggingface.co/datasets/{args.repo_id}/resolve/main/assets"

    # One image per category: its best-scoring image, skipping burned-in captions.
    nocap = m[m["caption_top"].isna()]
    picks = nocap.loc[nocap.groupby("category")["laion_aesthetic"].idxmax()].sort_values("category")
    rest = nocap.drop(picks.index).sort_values("laion_aesthetic", ascending=False)
    picks = pd.concat([picks, rest.head(-len(picks) % 4)])  # fill the last row with the next-best images
    tiles = [tile(args.png_dir / f"{r.id}.png", r.category.replace("_", "-")) for r in picks.itertuples()]
    grid(tiles, 4).save(assets / "sample-grid.jpg", quality=90, optimize=True)

    spread = spread_chart(m, assets / "seed-spread.png")
    category_chart(m, assets / "category-counts.png")

    if args.sweep_prompt_id is None:
        cand = spread[spread["n"] >= 200].copy()
        cand["range"] = cand["p90"] - cand["p10"]
        sweep_pid = int(cand.sort_values("range", ascending=False).iloc[0]["prompt_id"])
    else:
        sweep_pid = args.sweep_prompt_id
    sw = m[m["prompt_id"] == sweep_pid].sort_values("laion_aesthetic").reset_index(drop=True)
    picks = sw.iloc[[round(i * (len(sw) - 1) / 7) for i in range(8)]]
    grid(
        [tile(args.png_dir / f"{r.id}.png", f"seed {r.seed} · {r.laion_aesthetic:.2f}") for r in picks.itertuples()],
        4,
    ).save(assets / "seed-sweep.jpg", quality=90, optimize=True)
    sweep_subject = sw["prompt_subject"].iloc[0]

    cats = (
        m.groupby("category")
        .agg(images=("id", "size"), prompts=("prompt_id", "nunique"), median_aesthetic=("laion_aesthetic", "median"))
        .sort_values("images", ascending=False)
    )
    # itertuples keeps per-column dtypes; iterrows upcasts the int counts to float ("18,571.0").
    cat_rows = "\n".join(
        f"| {r.Index} | {int(r.images):,} | {int(r.prompts):,} | {r.median_aesthetic:.2f} |"
        for r in cats.itertuples()
    )
    sizes = m.groupby(["width", "height"]).size().sort_values(ascending=False)
    size_rows = "\n".join(f"| {w} × {h} | {n:,} |" for (w, h), n in sizes.items())
    per_prompt = m.groupby("prompt_id").size()
    v2 = m[m["pipeline_version"] == 2]
    spread_med = float((spread["p90"] - spread["p10"]).median())
    ex = report["excluded_counts"]
    # GiB, labelled "GB" to match the Hub's own size display (81.3e9 bytes -> "~76 GB").
    gb = report["shard_bytes"] / 2**30
    first, last = m["created_at"].min()[:10], m["created_at"].max()[:10]
    n = len(m)

    card = f"""---
license: cc0-1.0
pretty_name: "Image Ocean 2: 82k SDXL images, 225 prompts, one fixed recipe"
language:
- en
task_categories:
- text-to-image
- image-to-text
tags:
- synthetic
- ai-generated
- sdxl
- stable-diffusion
- seed-variance
- aesthetic-scores
- lora-training
size_categories:
- 10K<n<100K
configs:
- config_name: default
  default: true
  data_files:
  - split: train
    path: data/train-*.parquet
- config_name: metadata
  data_files:
  - split: train
    path: metadata/metadata.parquet
---

# Image Ocean 2: {n:,} SDXL images, {per_prompt.size} prompts, one fixed recipe

**{n:,} images** generated with **Stable Diffusion XL 1.0 base + refiner** on one RTX 4090 between {first} and {last}. **{per_prompt.size} prompts**, a median of **{int(per_prompt.median())} seeds per prompt**, and **one fixed sampler recipe** for {len(v2):,} of them. Every row carries the full recipe (prompt, negative prompt, seed, steps, CFG, scheduler, VAE, FreeU, refiner settings) plus a LAION aesthetic score and an NSFW probability.

- **Seed sweeps at scale.** Hundreds of seeds per prompt with everything else held constant. Useful for measuring seed variance, best-of-N selection, reward-model and preference work, and diversity studies.
- **Lossless.** Images are stored as lossless WebP, pixel-identical to the original PNG output (no JPEG artifacts — matters for synthetic-image detection research).
- **Reproducible.** Seeds and settings are exact; the generator code is public at [samuelfrench/image-ocean2](https://github.com/samuelfrench/image-ocean2).
- **Public domain (CC0).** Use it for anything, no attribution required.

![One high-scoring image per category]({base}/sample-grid.jpg)

## Same prompt, eight seeds

*"{sweep_subject}"* — {len(sw):,} seeds of this prompt are in the dataset. These eight span its score range, lowest to highest (label: seed · LAION aesthetic score):

![Eight seeds of one prompt sorted by aesthetic score]({base}/seed-sweep.jpg)

Seed choice alone moves the aesthetic score a lot. Across the {len(spread)} prompts with 20+ seeds, the median gap between a prompt's 10th- and 90th-percentile seed is **{spread_med:.2f} points**:

![Per-prompt aesthetic score range across seeds]({base}/seed-spread.png)

## Quick start

```python
from datasets import load_dataset

# stream without downloading all ~{gb:.0f} GB
ds = load_dataset("{args.repo_id}", split="train", streaming=True)
row = next(iter(ds))
row["image"]          # PIL.Image, lossless
row["prompt"], row["seed"], row["laion_aesthetic"]

# metadata only (no image bytes, a few MB): filter first, then fetch what you need
meta = load_dataset("{args.repo_id}", "metadata", split="train").to_pandas()
best = meta[meta.laion_aesthetic >= 6.5]
```

Reproduce any image with diffusers: SDXL base for `steps` steps up to `high_noise_frac`, then the refiner for the rest, with the listed `scheduler`, `vae`, `guidance_scale`, FreeU (`freeu_b1`, `freeu_b2`, `freeu_s1`, `freeu_s2`) and refiner aesthetic conditioning (`refiner_aesthetic_score`, `refiner_negative_aesthetic_score`). The exact code is [`generate.py`](https://github.com/samuelfrench/image-ocean2/blob/master/generate.py).

## What is in it

| Category | Images | Prompts | Median LAION aesthetic |
|---|---:|---:|---:|
{cat_rows}

![Images per category]({base}/category-counts.png)

| Resolution | Images |
|---|---:|
{size_rows}

Files: `data/` holds {report["shards"]} Parquet shards (~{gb:.0f} GB total, ~500 rows each) in generation order; `metadata/metadata.parquet` holds the same rows without image bytes.

## Columns

| Column | Type | Meaning |
|---|---|---|
| `image` | image | lossless WebP, pixel-identical to the generated PNG |
| `id` | string | original filename stem: `<local timestamp>_<model>_<category>_<prompt slug>_s<seed>` |
| `created_at` | string | generation time, US Central local time |
| `category` | string | prompt category (11 values) |
| `prompt_id` | int32 | stable integer id of `prompt_subject` (0–{per_prompt.size - 1}) |
| `prompt_subject` | string | the scene description |
| `prompt` | string | full positive prompt sent to the model (subject + quality suffix) |
| `negative_prompt` | string | full negative prompt |
| `seed` | int64 | torch generator seed |
| `width`, `height` | int32 | output size (SDXL training buckets chosen per category) |
| `steps`, `refiner_steps` | int32 | base and refiner inference steps |
| `high_noise_frac` | float64 | fraction of denoising done by the base model before the refiner |
| `guidance_scale` | float64 | CFG scale |
| `scheduler`, `vae` | string | sampler and VAE used |
| `freeu_b1` … `freeu_s2` | float64 | FreeU parameters (null for pipeline v1) |
| `refiner_aesthetic_score`, `refiner_negative_aesthetic_score` | float64 | refiner aesthetic **conditioning inputs** (null for v1) — not a measured score |
| `model_repo` | string | checkpoints used |
| `pipeline_version` | int32 | 1 = first 8 images (Euler, default VAE, CFG 7.5, no FreeU); 2 = everything else |
| `elapsed_seconds` | float64 | wall time to generate the image on an RTX 4090 |
| `caption_top`, `caption_bottom`, `caption_format` | string | meme caption burned into the image with Pillow ({int(m["caption_top"].notna().sum())} images; null otherwise) |
| `laion_aesthetic` | float32 | [LAION improved aesthetic predictor](https://github.com/christophschuhmann/improved-aesthetic-predictor) v2 (`sac+logos+ava1-l14-linearMSE`, CLIP ViT-L/14), measured after generation |
| `nsfw_prob` | float32 | probability of the `nsfw` label from [Falconsai/nsfw_image_detection](https://huggingface.co/Falconsai/nsfw_image_detection) |

## How it was made

Pipeline v2 (all but 8 images): SDXL 1.0 base → refiner handoff at {v2["high_noise_frac"].iloc[0]:g}, {int(v2["steps"].iloc[0])} + {int(v2["refiner_steps"].iloc[0])} steps, DPM++ 2M Karras, CFG {v2["guidance_scale"].iloc[0]:g}, `madebyollin/sdxl-vae-fp16-fix`, FreeU (b1 {v2["freeu_b1"].iloc[0]:g}, b2 {v2["freeu_b2"].iloc[0]:g}, s1 {v2["freeu_s1"].iloc[0]:g}, s2 {v2["freeu_s2"].iloc[0]:g}), refiner aesthetic conditioning {v2["refiner_aesthetic_score"].iloc[0]:g} / {v2["refiner_negative_aesthetic_score"].iloc[0]:g}. The generator ran unattended, picking a random category and prompt for each image with a fresh random seed; nothing was cherry-picked or removed for quality.

Removed before publishing: {ex["nsfw"]} images with `nsfw_prob` ≥ {report["nsfw_threshold"]}, {ex["manual"]} removed after manual review, {ex["no_sidecar"]} images whose metadata sidecar was missing.

## Limitations

- **Narrow prompt set.** {per_prompt.size} prompts written for a "random pretty picture" generator: animals, fantasy, landscapes, food, vehicles, office-humor scenes. Not a general-purpose text-to-image training set.
- **Uneven coverage.** Seeds per prompt range from {per_prompt.min()} to {per_prompt.max()}; the meme and whimsical categories dominate.
- **Model biases.** Everything SDXL 1.0 gets wrong is here too: hands, text, anatomy, Western-default people and places. The quality suffix (`masterpiece, best quality, … 8k`) pushes toward a glossy, high-contrast look.
- **Scores are model outputs.** `laion_aesthetic` and `nsfw_prob` are classifier predictions, not human ratings.

## License

**CC0 1.0** — public domain dedication. No attribution required. The images were generated with Stable Diffusion XL 1.0 (CreativeML Open RAIL++-M), whose license places no restrictions on outputs beyond its use-based restrictions; in the US, purely AI-generated images are not eligible for copyright. Please do not use it to impersonate real people or to pass AI-generated images off as photographs.

## Citation

```bibtex
@misc{{image_ocean2_sdxl_82k,
  title  = {{Image Ocean 2: {n:,} SDXL images, {per_prompt.size} prompts, one fixed recipe}},
  author = {{French, Sam}},
  year   = {{2026}},
  url    = {{https://huggingface.co/datasets/{args.repo_id}}}
}}
```
"""
    (args.out / "README.md").write_text(card)
    print(f"wrote README.md and {len(list(assets.iterdir()))} assets; sweep prompt {sweep_pid}: {sweep_subject}")


if __name__ == "__main__":
    main()
