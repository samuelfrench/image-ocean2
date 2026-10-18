---
title: "Bound --forever runs before the service is ever re-enabled"
status: idea
area: service
due: null
updated: 2026-10-17
owner: agent
brief: "Unbounded --forever filled 23 GB in 31 h and held the GPU at 100%; add a max-images/max-bytes cap and a yield-when-GPU-busy check first"
refs:
  - "generate.py"
  - "docs/todo/done/service/zombie-run-cleanup-2026-10-17.md"
test: null
---

- **Measured:** one unattended `--forever --category meme` run produced 21,140 images / 23 GB in 31 h (~680 images/h, ~740 MB/h) and held the 4090 at 100% / 16.5 GB VRAM the whole time. `Nice=19` does not yield the GPU.
- **Idea:** before re-enabling, add `--max-images N` and/or `--max-gb N` (stop cleanly at the cap), and skip a cycle when another process holds GPU memory (`nvidia-smi --query-compute-apps=pid --format=csv,noheader` lists any non-self PID). A prompt pool of 25 subjects also makes long runs near-duplicates; cap seeds per subject.
- **Done when:** a `--forever` run stops at its cap, yields while another GPU job runs (verified with a second CUDA process), and the unit stays disabled unless Sam asks.
