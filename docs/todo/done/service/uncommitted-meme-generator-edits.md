---
title: "Decide on the uncommitted meme-caption generator edits"
status: done
area: service
due: null
updated: 2026-10-17
owner: agent
brief: "Done 2026-10-17: Sam chose discard; the 5 files (+348/-27) were restored to HEAD with git restore, working tree clean"
refs:
  - "generate.py"
  - "prompts.py"
  - "gallery.py"
  - "README.md"
  - "docs/superpowers/specs/2026-05-02-always-on-service-design.md"
test: null
---

- **State (2026-10-17, `git diff --stat`):** `generate.py` +158, `prompts.py` +179, `gallery.py` +12, `README.md` 19 changed, the always-on service spec 7 changed; 348 insertions / 27 deletions. File mtimes: `prompts.py`, `gallery.py`, spec 2026-05-13; `generate.py` 2026-09-14; `README.md` 2026-10-04. The 2026-10-04 dataset sessions deliberately preserved these edits without committing them.
- **What they do:** `DEFAULT_CATEGORY = "meme"`; `Prompt` gains `top_text`, `bottom_text`, `meme_format`; `apply_meme_caption_overlay()` draws classic top/bottom captions after diffusion; `meme_extra()` writes caption data to the JSON sidecar `extra.meme`; the gallery shows the caption. The disabled login service ran this uncommitted code on 2026-10-16/17 (see `docs/todo/done/service/zombie-run-cleanup-2026-10-17.md`).
- **Gotcha:** nobody has run tests or a lint pass on these edits in a recorded session. Do not discard or commit them without Sam's decision; agents committing only TODO files must `git add` exact paths, never `-A`.
- **Done when:** Sam chooses commit (then lint, generate 2 images, check the captions render, commit, push) or discard (`git restore` the five files), and the working tree is clean.
- **Result (2026-10-17):** Sam chose **discard**. `git restore` on the five files returned them to HEAD; `git status` clean. No backup patch was kept. The committed generator has no meme-caption overlay; `DEFAULT_CATEGORY` and the `Prompt` fields are back to their committed state.
