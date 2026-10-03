---
title: "FLUX.1-dev pipeline"
status: idea
area: models
due: null
updated: 2026-10-03
owner: agent
brief: "Optional: FLUX.1-dev (non-schnell) for higher FLUX quality at the cost of speed"
refs:
  - "generate.py"
  - "README.md"
test: null
---

- **What:** add a `--model` choice that loads FLUX.1-dev instead of FLUX.1-schnell.
- **Why:** optional; higher FLUX quality at the cost of speed. The README records `flux` (schnell) at ~16 s / image with sequential CPU offload on 24 GB.
- **Next:** add a branch beside the `flux` branch in `load_pipelines()`, measure s/image on the RTX 4090, and check the FLUX.1-dev license before use (it differs from schnell's Apache 2.0); update the README model table and license line.

<!-- Migrated verbatim from TODO.md @ bc8555b, lines 6-6, on 2026-10-03. -->
- [ ] Optional: wire up FLUX.1-dev (non-schnell) for higher FLUX quality at the cost of speed.
