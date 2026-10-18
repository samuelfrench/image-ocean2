---
title: "Stop the login-enabled generator service and clear its unplanned run"
status: done
area: service
due: null
updated: 2026-10-17
owner: agent
brief: "Done 2026-10-17: image-ocean2.service stopped + disabled; its 31 h Oct 16-17 run (21,140 meme PNG + JSON, 23 GB) deleted on Sam's go"
refs:
  - "generate.py"
  - "docs/superpowers/specs/2026-05-02-always-on-service-design.md"
test: null
---

- **What happened:** the user unit `image-ocean2.service` (`generate.py --forever --category meme`, `Restart=no`, `Nice=19`, `IOSchedulingClass=idle`) had been enabled at login since 2026-05-13. `Nice=19` yields CPU only; the run held the 4090 at 100% / 16.5 GB VRAM. From about 2026-09-06 it crashed ~6 s after every login (Hugging Face Hub `RuntimeError: Cannot send a request, as the client has been closed.` while loading the fp16-fix VAE), so it looked dead. On the 2026-10-16 14:17 CT boot the request succeeded and it ran 31 h.
- **Run contents (measured before deletion):** 21,140 PNG + 21,140 JSON sidecars (23 GB), all `category: meme`, `pipeline_version: 2`, `sdxl-refined`, 25 prompt subjects x ~850 seeds each. The stop left one partial `.png.tmp` and its orphan JSON sidecar.
- **Result (2026-10-17):** Sam had the service stopped and disabled (`systemctl --user status image-ocean2` -> `disabled`, `inactive (dead)`). On Sam's go, every file from the run was deleted at 21:45 CT and `output/` was recreated empty (the old directory inode had grown to 26 MB). Nothing from this run was kept or uploaded; the public Hugging Face dataset is unaffected.
- **Do not re-enable** the unit without Sam asking. Manual run: `systemctl --user start image-ocean2`. Guard idea before any re-enable: `docs/todo/service/forever-run-guard.md`.
