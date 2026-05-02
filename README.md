# image-ocean2

A tiny CLI that generates **super high quality random images locally** on an RTX 4090 using SDXL (base + refiner), Juggernaut-XL v9, or FLUX.1-schnell. Mostly fun prompts, some serious, all PG.

No cloud API keys. No subscriptions. Just your GPU and a checkpoint file.

## Quality stack

Every SDXL-based pipeline (`sdxl-refined`, `sdxl-base`, `juggernaut`) runs through:

- **fp16-fix VAE** (`madebyollin/sdxl-vae-fp16-fix`) — kills the washed-out colors and occasional NaN latents the stock SDXL VAE produces under fp16 inference.
- **DPM++ 2M Karras scheduler** — better convergence per step than the default Euler. Modern SDXL default in Automatic1111 / ComfyUI.
- **FreeU** with SDXL-tuned values (b1=1.3, b2=1.4, s1=0.9, s2=0.2) — free quality boost from rebalancing U-Net skip connections.
- **Aesthetic scoring on the refiner** (`aesthetic_score=6.0`) — uses the score conditioning SDXL was actually trained with.
- **Per-category SDXL bucket resolutions** — landscapes go to 1344×768, portraits to 832×1216, animals to 1152×896, the rest to 1024×1024. Matches the shapes SDXL was bucket-trained on.

CFG defaults to 7.0 (was 7.5) — closer to the SDXL sweet spot.

## What it makes

Random draws from a curated prompt bank across ten categories — weighted heavily toward fun:

- `whimsical` — raccoons in pinstripe suits, octopus baristas, corgi astronauts
- `fantasy` — tiny dragons, floating island cities, hobbit burrows
- `sci_fi` — friendly robots, retro rockets, space diners
- `animals` — red fox in ferns, dolphins at sunset
- `nature` — alpine lakes, bioluminescent bays, sequoia groves
- `architecture` — Tokyo night markets, Moroccan riads, Venice canals
- `portraits` — fishermen, jazz trumpeters, watchmakers
- `food` — sourdough boards, shakshuka, flat-lay Buddha bowls
- `abstract` — Escher stairs, paper-craft dioramas
- `vehicles` — vintage convertibles, airships, wooden sailboats

Run `python generate.py --list-categories` to see the list.

## Hardware / software

Built and tested on:

- **NVIDIA RTX 4090 (24 GB VRAM)**, CUDA 12.4
- Python **3.12** in the ComfyUI venv
- `torch 2.6 + cu124`, `diffusers 0.35`, `transformers 4.57`, `accelerate 1.12`

Any SDXL-capable GPU with ~12 GB VRAM should work (drop to `--model sdxl-base` if memory is tight).

## Models

Checkpoints are not bundled — they're multi-gigabyte files. The script expects a ComfyUI-style layout by default (`../ComfyUI/models/checkpoints/...`) but you can point anywhere with `--models-root`.

| Model flag       | File                                               | Size   | Notes                              |
| ---------------- | -------------------------------------------------- | ------ | ---------------------------------- |
| `sdxl-refined`   | `sd_xl_base_1.0.safetensors` + `sd_xl_refiner_1.0.safetensors` | 6.5 + 5.7 GB | **Default.** Best classic SDXL quality. |
| `sdxl-base`      | `sd_xl_base_1.0.safetensors`                       | 6.5 GB | Faster, slightly less polished.    |
| `juggernaut`     | `Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors`| 6.7 GB | Photoreal SDXL fine-tune.          |
| `flux`           | `black-forest-labs/FLUX.1-schnell` (HF cache)      | ~33 GB | Different aesthetic, slower (CPU offload on 24 GB). |

Grab SDXL base + refiner from Hugging Face (`stabilityai/stable-diffusion-xl-base-1.0` and `stabilityai/stable-diffusion-xl-refiner-1.0`), Juggernaut-XL from Civitai, FLUX from `black-forest-labs/FLUX.1-schnell`.

## Install

```sh
# In any Python 3.10+ env with CUDA-capable torch installed.
pip install -r requirements.txt
```

If you already run ComfyUI locally, just activate that venv:

```sh
source ../ComfyUI/venv/bin/activate
```

## Usage

```sh
# One random image (SDXL base + refiner, 1024x1024, 40+15 steps)
python generate.py

# Four random images
python generate.py --count 4

# Restrict to a category
python generate.py --category whimsical --count 3

# Custom prompt (quality suffix + negative prompt are still applied)
python generate.py --prompt "a fox reading a book in a mossy forest"

# Photoreal with Juggernaut-XL
python generate.py --model juggernaut --count 2

# FLUX.1-schnell (slower on 24 GB, but a different look)
python generate.py --model flux --count 1

# Reproducible — seed N is the base; image i gets seed N+i
python generate.py --seed 42 --count 4

# Run indefinitely. Every completed image is saved to disk immediately;
# press Ctrl-C at any time and keep whatever's already there.
python generate.py --forever
```

Everything lands in `output/` as `TIMESTAMP_category_slug_sSEED.png` plus a JSON sidecar containing the exact prompt, seed, model, and steps for reproducibility.

### Local gallery

```sh
python gallery.py
# image-ocean2 gallery: http://127.0.0.1:8765/
```

Stdlib-only web server (no extra deps). Renders a responsive thumbnail grid with category filter, prompt search, and a click-to-zoom lightbox. The index is rebuilt from disk on every request, so anything written by an in-flight `--forever` run shows up the moment you refresh.

Flags: `--port 9000`, `--host 0.0.0.0` (LAN, careful — there's no auth).

When `--forever` is on, each image gets a fresh random seed (so an overnight run keeps varying) unless you pass `--seed N`, in which case seeds are `N, N+1, N+2, …` — fully reproducible. On Ctrl-C the script prints `[interrupted] Stopped after N image(s)` and exits cleanly.

### All flags

```
--count N               How many images (default 1)
--forever               Generate indefinitely until Ctrl-C (overrides --count)
--model {sdxl-refined,sdxl-base,juggernaut,flux}
--category NAME         Restrict to a single category
--prompt "…"            Skip the prompt bank entirely
--seed N                Base seed (default random)
--steps 40              Base pipeline inference steps
--refiner-steps 15      Refiner steps (sdxl-refined only)
--guidance 7.0          CFG scale
--width N               Must be a multiple of 8 (default: per-category SDXL bucket)
--height N              Must be a multiple of 8 (default: per-category SDXL bucket)
--high-noise-frac 0.8   Fraction of steps handled by base before refiner kicks in
--out DIR               Output directory (default ./output)
--models-root PATH      Where to look for checkpoints (default ../ComfyUI/models)
--list-categories       Print categories and exit
```

## Prompt bank

See `prompts.py`. Every subject is decorated with a shared quality suffix:

```
masterpiece, best quality, ultra detailed, intricate detail,
sharp focus, professional photography, cinematic lighting,
dramatic composition, 8k, crisp, high dynamic range
```

…and a broad negative prompt that includes PG filters (no NSFW, gore, weapons, horror). The prompt bank itself is curated PG — adding new prompts means adding new entries to the category lists.

## Performance notes

On a 24 GB RTX 4090 with the upgraded quality stack:

- `sdxl-refined` — **~4 s / image** at 1024×1024 (DPM++ 2M Karras converges in fewer real steps than Euler did)
- `sdxl-refined` at 1344×768 — ~4.2 s / image
- `sdxl-base` / `juggernaut` — ~3–4 s / image
- `flux` — ~16 s / image (sequential CPU offload required, unchanged)

Model load adds one-off overhead (~3–8 s for SDXL, ~60 s+ for FLUX). The fp16-fix VAE adds a one-time HF download (~335 MB) on first run.

## License

MIT. The prompt bank and this code are free to use; model weights have their own licenses (SDXL 1.0 CreativeML Open RAIL++-M, Juggernaut-XL non-commercial, FLUX-schnell Apache 2.0) — please respect them.
