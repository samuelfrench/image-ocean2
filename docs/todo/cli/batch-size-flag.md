---
title: "--batch-size flag for N variations per prompt"
status: idea
area: cli
due: null
updated: 2026-10-03
owner: agent
brief: "Optional: N variations per prompt while keeping the seed + index schedule"
refs:
  - "generate.py"
test: null
---

- **What:** add `--batch-size N` to `generate.py` to produce N variations of one prompt with the same seed schedule.
- **Why:** optional; listed as an open idea in the hand-maintained TODO.md before 2026-10-03. No measured need recorded.
- **Next:** keep the existing `--seed` contract (`Base seed. Each image gets seed + index.`) so a batch is reproducible; check 24 GB VRAM headroom per model before batching on-device (FLUX already needs sequential CPU offload).

<!-- Migrated verbatim from TODO.md @ bc8555b, lines 5-5, on 2026-10-03. -->
- [ ] Optional: add a `--batch-size` flag to produce N variations per prompt with the same seed schedule.
