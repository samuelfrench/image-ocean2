"""Build Hugging Face Parquet shards from the image-ocean2 output archive.

usage: python scripts/hf_dataset/build_shards.py --png-dir DIR --meta-dir DIR \
           --scores scores.parquet --out OUTDIR [--nsfw-threshold 0.5] [--exclude ids.txt]

Writes:
  OUTDIR/data/train-XXXXX-of-NNNNN.parquet   image (lossless WebP, pixel-identical to
                                              the original PNG) + full generation recipe
  OUTDIR/metadata/metadata.parquet           the same rows without image bytes
  OUTDIR/build-report.json                   counts, exclusions, shard sizes

Rows are in generation order (the id starts with the local timestamp), so the
first rows of the Dataset Viewer mix categories the way the generator did.
Images without a JSON sidecar, unreadable images, and images with
nsfw_prob >= --nsfw-threshold (or listed in --exclude) are left out and listed
in the report.
"""
from __future__ import annotations

import argparse
import io
import json
import math
from multiprocessing import Pool
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from PIL import Image

ROWS_PER_SHARD = 500  # ~500 MB per shard at ~1 MB per lossless WebP
ROW_GROUP_SIZE = 100  # small row groups keep the Dataset Viewer responsive

# (column, arrow type, datasets dtype)
COLUMNS = [
    ("id", pa.string(), "string"),
    ("created_at", pa.string(), "string"),
    ("category", pa.string(), "string"),
    ("prompt_id", pa.int32(), "int32"),
    ("prompt_subject", pa.string(), "string"),
    ("prompt", pa.string(), "string"),
    ("negative_prompt", pa.string(), "string"),
    ("seed", pa.int64(), "int64"),
    ("width", pa.int32(), "int32"),
    ("height", pa.int32(), "int32"),
    ("steps", pa.int32(), "int32"),
    ("refiner_steps", pa.int32(), "int32"),
    ("high_noise_frac", pa.float64(), "float64"),
    ("guidance_scale", pa.float64(), "float64"),
    ("scheduler", pa.string(), "string"),
    ("vae", pa.string(), "string"),
    ("freeu_b1", pa.float64(), "float64"),
    ("freeu_b2", pa.float64(), "float64"),
    ("freeu_s1", pa.float64(), "float64"),
    ("freeu_s2", pa.float64(), "float64"),
    ("refiner_aesthetic_score", pa.float64(), "float64"),
    ("refiner_negative_aesthetic_score", pa.float64(), "float64"),
    ("model_repo", pa.string(), "string"),
    ("pipeline_version", pa.int32(), "int32"),
    ("elapsed_seconds", pa.float64(), "float64"),
    ("caption_top", pa.string(), "string"),
    ("caption_bottom", pa.string(), "string"),
    ("caption_format", pa.string(), "string"),
    ("laion_aesthetic", pa.float32(), "float32"),
    ("nsfw_prob", pa.float32(), "float32"),
]
IMAGE_TYPE = pa.struct([("bytes", pa.binary()), ("path", pa.string())])


def features(with_image: bool) -> dict:
    f = {"image": {"_type": "Image"}} if with_image else {}
    f.update({name: {"dtype": dt, "_type": "Value"} for name, _, dt in COLUMNS})
    return f


def schema(with_image: bool) -> pa.Schema:
    fields = [pa.field("image", IMAGE_TYPE)] if with_image else []
    fields += [pa.field(name, t) for name, t, _ in COLUMNS]
    meta = {b"huggingface": json.dumps({"info": {"features": features(with_image)}}).encode()}
    return pa.schema(fields, metadata=meta)


def row_from_meta(img_id: str, d: dict, prompt_ids: dict, scores: dict) -> dict:
    ts = img_id.split("_", 1)[0]  # YYYYMMDD-HHMMSS, generator's local time (US Central)
    freeu = d.get("freeu") or {}
    meme = (d.get("extra") or {}).get("meme") or {}
    sc = scores.get(img_id, {})
    return {
        "id": img_id,
        "created_at": f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]}T{ts[9:11]}:{ts[11:13]}:{ts[13:15]}",
        "category": d.get("category"),
        "prompt_id": prompt_ids[d.get("prompt_subject")],
        "prompt_subject": d.get("prompt_subject"),
        "prompt": d.get("prompt_full"),
        "negative_prompt": d.get("negative_prompt"),
        "seed": d.get("seed"),
        "width": d.get("width"),
        "height": d.get("height"),
        "steps": d.get("steps"),
        "refiner_steps": d.get("refiner_steps"),
        "high_noise_frac": d.get("high_noise_frac"),
        "guidance_scale": d.get("guidance_scale"),
        "scheduler": d.get("scheduler"),
        "vae": d.get("vae"),
        "freeu_b1": freeu.get("b1"),
        "freeu_b2": freeu.get("b2"),
        "freeu_s1": freeu.get("s1"),
        "freeu_s2": freeu.get("s2"),
        "refiner_aesthetic_score": d.get("aesthetic_score"),
        "refiner_negative_aesthetic_score": d.get("negative_aesthetic_score"),
        "model_repo": d.get("model_repo"),
        "pipeline_version": d.get("pipeline_version"),
        "elapsed_seconds": d.get("elapsed_seconds"),
        "caption_top": meme.get("top_text"),
        "caption_bottom": meme.get("bottom_text"),
        "caption_format": meme.get("format"),
        "laion_aesthetic": sc.get("laion_aesthetic"),
        "nsfw_prob": sc.get("nsfw_prob"),
    }


def encode(png: Path) -> bytes:
    im = Image.open(png)
    im.load()
    buf = io.BytesIO()
    im.save(buf, format="WEBP", lossless=True, quality=100, method=4)
    return buf.getvalue()


def write_shard(job: tuple) -> dict:
    idx, total, rows, png_dir, out_dir = job
    path = Path(out_dir) / "data" / f"train-{idx:05d}-of-{total:05d}.parquet"
    if path.exists():  # resumable
        return {"shard": path.name, "rows": pq.ParquetFile(path).metadata.num_rows, "bytes": path.stat().st_size}
    images = [{"bytes": encode(Path(png_dir) / f"{r['id']}.png"), "path": f"{r['id']}.webp"} for r in rows]
    table = pa.Table.from_pylist([{"image": im, **r} for im, r in zip(images, rows)], schema=schema(True))
    tmp = path.with_suffix(".tmp")
    pq.write_table(table, tmp, row_group_size=ROW_GROUP_SIZE, compression="zstd")
    tmp.rename(path)
    return {"shard": path.name, "rows": len(rows), "bytes": path.stat().st_size}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--png-dir", required=True, type=Path)
    ap.add_argument("--meta-dir", required=True, type=Path)
    ap.add_argument("--scores", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--nsfw-threshold", type=float, default=0.5)
    ap.add_argument("--exclude", type=Path, help="file of ids to leave out (one per line)")
    ap.add_argument("--workers", type=int, default=28)
    args = ap.parse_args()

    pngs = {p.stem for p in args.png_dir.glob("*.png")}
    metas = {p.stem: p for p in args.meta_dir.glob("*.json")}
    scores = pd.read_parquet(args.scores).set_index("id").to_dict("index")
    manual = set(Path(args.exclude).read_text().split()) if args.exclude else set()

    excluded = {"no_sidecar": sorted(pngs - set(metas)), "not_scored": [], "nsfw": [], "manual": []}
    rows = []
    loaded = {}
    for img_id in sorted(pngs & set(metas)):
        if img_id in manual:
            excluded["manual"].append(img_id)
            continue
        sc = scores.get(img_id)
        if sc is None:
            excluded["not_scored"].append(img_id)
            continue
        if sc["nsfw_prob"] >= args.nsfw_threshold:
            excluded["nsfw"].append(img_id)
            continue
        loaded[img_id] = json.loads(metas[img_id].read_text())
    prompt_ids = {s: i for i, s in enumerate(sorted({d["prompt_subject"] for d in loaded.values()}))}
    rows = [row_from_meta(i, d, prompt_ids, scores) for i, d in loaded.items()]

    (args.out / "data").mkdir(parents=True, exist_ok=True)
    (args.out / "metadata").mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.Table.from_pylist(rows, schema=schema(False)),
        args.out / "metadata" / "metadata.parquet",
        compression="zstd",
    )

    total = math.ceil(len(rows) / ROWS_PER_SHARD)
    jobs = [
        (i, total, rows[i * ROWS_PER_SHARD : (i + 1) * ROWS_PER_SHARD], str(args.png_dir), str(args.out))
        for i in range(total)
    ]
    done = []
    with Pool(args.workers) as pool:
        for n, res in enumerate(pool.imap_unordered(write_shard, jobs), 1):
            done.append(res)
            if n % 10 == 0 or n == total:
                print(f"{n}/{total} shards", flush=True)

    report = {
        "rows": len(rows),
        "prompts": len(prompt_ids),
        "shards": total,
        "shard_bytes": sum(r["bytes"] for r in done),
        "nsfw_threshold": args.nsfw_threshold,
        "excluded_counts": {k: len(v) for k, v in excluded.items()},
        "excluded": excluded,
    }
    (args.out / "build-report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "excluded"}, indent=2), flush=True)


if __name__ == "__main__":
    main()
