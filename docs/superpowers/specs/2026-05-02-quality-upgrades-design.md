# 2026-05-02 — image-ocean2 quality upgrades

## Goal

Apply the highest-impact, well-supported "high-quality SDXL" learnings to the existing pipelines without breaking the `--forever` loop or the JSON sidecar contract.

User explicitly authorized full autonomous execution and skipped the standard approval gate ("go full autonomous, I won't be able to approve anything"). This document is recorded for the audit trail.

## Scope

In: SDXL-based pipelines (`sdxl-refined`, `sdxl-base`, `juggernaut`).

Out: FLUX. It already works at ~16 s/image with sequential CPU offload — different stack, different VAE, different bottlenecks. Don't risk regressing it.

## Changes

### 1. fp16-numerically-stable VAE

The default SDXL VAE has known fp16 precision issues that cause washed-out colors and occasional NaN latents. Swap in `madebyollin/sdxl-vae-fp16-fix`, which retrains the decoder layers in fp32 then quantizes — visually identical at full precision, numerically stable at fp16.

- Loaded once and shared across base + refiner (already done for the existing default VAE — keep that VRAM-saving pattern).
- Applied to all three SDXL pipelines.

### 2. DPM++ 2M Karras scheduler

Replace the default Euler scheduler with `DPMSolverMultistepScheduler` configured `algorithm_type="dpmsolver++"`, `use_karras_sigmas=True`. Better convergence per step on SDXL; community-validated default in modern UIs (Automatic1111, ComfyUI's `KSampler` "dpmpp_2m_karras").

Steps stay at 40 base + 15 refiner — speed isn't the goal, quality is.

### 3. FreeU

Free quality boost. Reweights the U-Net's skip connections so high-frequency detail isn't washed out. SDXL-tuned values from the FreeU paper (Si et al. 2024): `b1=1.3, b2=1.4, s1=0.9, s2=0.2`.

Applied to base and refiner.

### 4. Aesthetic scoring on the refiner

The SDXL refiner was conditioned on aesthetic score during training. The default diffusers values (6.0 / 2.5) are fine but were not being passed explicitly — the pipeline uses defaults. Pass `aesthetic_score=6.0, negative_aesthetic_score=2.5` explicitly so the contract is visible in the JSON sidecar via the call signature.

(Marginal but free.)

### 5. Per-category SDXL bucket resolutions

SDXL was trained at multiple aspect ratios. 1024×1024 is one of many; landscapes look better wide, portraits look better tall. Add a `CATEGORY_RESOLUTIONS` map in `prompts.py`:

| Category      | Resolution | Reason                             |
| ------------- | ---------- | ---------------------------------- |
| nature        | 1344×768   | wide vistas                        |
| architecture  | 1344×768   | wide buildings, streetscapes       |
| vehicles      | 1344×768   | cars, ships, planes are horizontal |
| sci_fi        | 1344×768   | landscape-y space scenes           |
| portraits     | 832×1216   | classic portrait orientation       |
| animals       | 1152×896   | slightly wide, animal-friendly     |
| whimsical     | 1024×1024  | square works for character shots   |
| fantasy       | 1024×1024  | square                             |
| food          | 1024×1024  | flat-lays / square plating         |
| abstract      | 1024×1024  | square                             |

All values are SDXL bucket-trained sizes from Stability's training paper.

`generate.py` consumes this only when the user did **not** pass `--width`/`--height`. If they do, their values win (existing behavior).

### 6. Default CFG nudge: 7.5 → 7.0

SDXL behaves better with slightly lower CFG than SD 1.5. 7.0 is a tiny conservative step toward the 5–8 sweet spot that the SDXL paper / community settled on. (Could go lower, but 7.0 is a safe move from 7.5.)

## Non-goals

- **Compel for >77 token prompts.** Adds a dependency. Subject + suffix is well under the 77-token limit per encoder; revisit only if a new prompt overflows.
- **Prompt 2 differentiation** (separate prompt for OpenCLIP-G). Modest gain; not worth the prompt-bank refactor right now.
- **FLUX changes.** See "out of scope" above.
- **New CLI flags** (`--scheduler`, `--no-freeu`). YAGNI. Apply the best defaults; users can fork if they disagree.

## Risks / mitigations

- **fp16-fix VAE download (~335 MB).** First run will pull from HF. Disk has 789 GB free; not a concern. Network failure → diffusers raises a clear error.
- **VRAM.** SDXL + new VAE + FreeU adds maybe 100 MB. RTX 4090 has 23.7 GB free; not a concern.
- **Scheduler config compatibility.** `from_config()` keeps any non-overridden settings; the standard SDXL config maps cleanly to DPM++.
- **Per-category resolution unexpectedly skipping user override.** Mitigation: argparse defaults to `None`; explicit user values are only ignored when both are `None`.

## Validation

- Smoke test: run `--count 2 --model sdxl-refined` end to end. Verify both images written, JSON sidecar present, no warnings about NaN or VAE issues, total wall-clock <30 s.
- Then start `--forever` for the user.

## Files touched

- `generate.py` — VAE swap, scheduler swap, FreeU enable, aesthetic score args, resolution-default branch.
- `prompts.py` — `CATEGORY_RESOLUTIONS` map + `get_default_resolution()`.
- `README.md` — document the upgrades in the performance / models sections.
- `TODO.md` — log the upgrade as done.
