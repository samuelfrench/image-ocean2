---
title: "SDXL LoRA support"
status: idea
area: models
due: null
updated: 2026-10-03
owner: agent
brief: "Optional: --lora <file.safetensors> --lora-weight 0.8 for the SDXL-based pipelines"
refs:
  - "generate.py"
test: null
---

- **What:** add `--lora path.safetensors --lora-weight 0.8` to `generate.py` so the SDXL-based pipelines (`sdxl-refined`, `sdxl-base`, `juggernaut`) can load one LoRA.
- **Why:** optional; listed as an open idea in the hand-maintained TODO.md before 2026-10-03. No measured need recorded.
- **Next:** in `load_pipelines()` (generate.py @ bc8555b line 227), load the LoRA after `_apply_sdxl_quality_upgrades()`; record the LoRA file and weight in the JSON sidecar so attribution stays complete. Decide whether `flux` rejects the flag or supports FLUX LoRAs.

<!-- Migrated verbatim from TODO.md @ bc8555b, lines 3-4, on 2026-10-03. -->
## Open
- [ ] Optional: add SDXL LoRA support (`--lora path.safetensors --lora-weight 0.8`).
