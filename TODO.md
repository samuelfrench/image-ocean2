# image-ocean2 — TODO

## Open
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
- [x] 2026-05-02 — `gallery.py`: stdlib-only local web server. Thumbnail grid, lightbox, category filter, prompt search, lazy-loaded images. Re-reads `output/` per request so live `--forever` runs surface immediately on refresh.
- [x] 2026-05-02 — Per-image attribution: filename now embeds the model (`TS_MODEL_CAT_SLUG_sSEED.png`) and the JSON sidecar records `model_repo`, `vae`, `scheduler`, `freeu`, aesthetic scores, and `pipeline_version`. Gallery shows a per-card model badge plus a model filter. `backfill_attribution.py` migrated all 1,893 pre-existing PNG/JSON pairs (8 pre-stack era → version 1, 1,885 post-stack → version 2).
