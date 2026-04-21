# image-ocean2

A tiny CLI that generates **super high quality random images locally** on an RTX 4090 using SDXL (base + refiner), Juggernaut-XL v9, or FLUX.1-schnell. Mostly fun prompts, some serious, all PG.

No cloud API keys. No subscriptions. Just your GPU and a checkpoint file.

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
```

Everything lands in `output/` as `TIMESTAMP_category_slug_sSEED.png` plus a JSON sidecar containing the exact prompt, seed, model, and steps for reproducibility.

### All flags

```
--count N               How many images (default 1)
--model {sdxl-refined,sdxl-base,juggernaut,flux}
--category NAME         Restrict to a single category
--prompt "…"            Skip the prompt bank entirely
--seed N                Base seed (default random)
--steps 40              Base pipeline inference steps
--refiner-steps 15      Refiner steps (sdxl-refined only)
--guidance 7.5          CFG scale
--width 1024            Must be a multiple of 8
--height 1024           Must be a multiple of 8
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

On a 24 GB RTX 4090 at 1024×1024:

- `sdxl-refined` — **~5 s / image** after load (40 base + 15 refiner steps, fp16)
- `sdxl-base` — ~4 s / image
- `juggernaut` — ~4 s / image
- `flux` — ~16 s / image (sequential CPU offload required)

Model load adds one-off overhead (~3–8 s for SDXL, ~60 s+ for FLUX).

## License

MIT. The prompt bank and this code are free to use; model weights have their own licenses (SDXL 1.0 CreativeML Open RAIL++-M, Juggernaut-XL non-commercial, FLUX-schnell Apache 2.0) — please respect them.
