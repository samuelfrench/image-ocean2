# TODO.md → task files: migration map (2026-10-03)

Source: `TODO.md` @ `bc8555b` (1 `## ` sections plus the preamble; the finished `## Done` section had already moved verbatim to `TODO-archive.md`). Produced by `node scripts/todo/migrate-monolith.mjs`. Every non-empty line of the old file is in a task file below or in the `[MIGRATED 2026-10-03]` appendix of `TODO-archive.md` (proof: `migrate-monolith.mjs verify`). Merged sections were duplicates or superseded versions of the same task.

| Section | Old lines | Old heading (first 110 chars) | New file | Note |
|---|---|---|---|---|
| S000 | 1-2 | (preamble before the first heading) | TODO-archive.md | retired (not a task) — archived verbatim |
| S001 | 3-8 | Open | 4 files | split: each line range routed to its own task (rows below); the heading line stays with the first range |
| S001 | 3-4 | Open | [models/sdxl-lora-support.md](models/sdxl-lora-support.md) |  |
| S001 | 5-5 | Open | [cli/batch-size-flag.md](cli/batch-size-flag.md) |  |
| S001 | 6-6 | Open | [models/flux-dev-pipeline.md](models/flux-dev-pipeline.md) |  |
| S001 | 7-7 | Open | [docs/readme-sample-grid.md](docs/readme-sample-grid.md) |  |
