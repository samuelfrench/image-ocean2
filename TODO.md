# image-ocean2 — TODO

## Open
- [ ] Add a `gallery.py` helper that builds a static HTML gallery of everything in `output/` (thumbnails + prompt shown on hover).
- [ ] Optional: add SDXL LoRA support (`--lora path.safetensors --lora-weight 0.8`).
- [ ] Optional: add a `--batch-size` flag to produce N variations per prompt with the same seed schedule.
- [ ] Optional: wire up FLUX.1-dev (non-schnell) for higher FLUX quality at the cost of speed.
- [ ] Add a small sample grid to `samples/` so the README has reference outputs committed to the repo.

## Done
- [x] 2026-04-20 — Initial project: `prompts.py`, `generate.py`, README, requirements, .gitignore.
- [x] 2026-04-20 — SDXL base + refiner two-stage pipeline at 5.3s / 1024×1024 on RTX 4090.
- [x] 2026-04-20 — Juggernaut-XL v9 and FLUX.1-schnell pipelines wired behind `--model` flag.
- [x] 2026-04-20 — Repo pushed to GitHub as public.
- [x] 2026-04-20 — `--forever` flag with graceful Ctrl-C handling; fresh seed per image when unseeded.
- [x] 2026-05-02 — Quality upgrade pass: fp16-fix VAE, DPM++ 2M Karras scheduler, FreeU (b1=1.3, b2=1.4, s1=0.9, s2=0.2), refiner aesthetic scoring, per-category SDXL bucket resolutions, default CFG 7.5 → 7.0. ~4 s / image (faster than 5.3 s baseline because DPM++ 2M Karras converges in fewer real steps).
