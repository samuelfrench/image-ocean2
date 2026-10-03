---
title: "Sample grid in samples/ for the README"
status: next
area: docs
due: null
updated: 2026-10-03
owner: agent
brief: "Commit a small sample grid to samples/ so the README shows reference outputs"
refs:
  - "README.md"
  - ".gitignore"
test: null
---

- **What:** commit a small grid of reference outputs to `samples/` and show it in the README.
- **Why:** the README describes the quality stack and models but commits no example output; `samples/` does not exist yet (checked 2026-10-03).
- **Next:** pick one image per model or category from `output/`, visually QA each, save as JPEG under `samples/` (`.gitignore` already allows `samples/*.png` and `samples/*.jpg`), keep the total small, and link it from the README.

<!-- Migrated verbatim from TODO.md @ bc8555b, lines 7-7, on 2026-10-03. -->
- [ ] Add a small sample grid to `samples/` so the README has reference outputs committed to the repo.
