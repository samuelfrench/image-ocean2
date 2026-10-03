# Project Codex Loader

Before substantial work, read `/home/sam/.codex/memories/MEMORY.md`.

Then read local project context when present:
- `CLAUDE.md`
- `TODO.md` (generated; see "TODO.md is generated" below)
- `/home/sam/.codex/memories/project-context-index.md`

For deeper history, follow the matching Claude memory path listed in `/home/sam/.codex/memories/project-context-index.md`.
Do not reveal secrets from historical memory or export files.

## TODO.md is generated

- `TODO.md` is generated from one file per task under `docs/todo/` (since 2026-10-03). **Never hand-edit `TODO.md`.** Read it at session start, then work in the task files.
- To add, update or close a task: edit `docs/todo/<area>/<slug>.md` (areas `models` `cli` `gallery` `service` `data` `docs` `ci` `process`; frontmatter, statuses and rules in `docs/todo/README.md`), run `node scripts/todo/build.mjs`, and commit the task file, `TODO.md` and `docs/todo/index.json` together in one commit.
- Look tasks up with `node scripts/todo/query.mjs` (`--status now,waiting-sam`, `--area models`, `--due-before <YYYY-MM-DD>`, `--test <name>`, `--grep <text> --all`).
- Before pushing: `node scripts/todo/build.mjs --check` and `node --test scripts/todo/__tests__/*.test.mjs`. CI (`.github/workflows/todo.yml`, GitHub-hosted `ubuntu-latest`) runs both; never move it to a self-hosted runner (public repo).
- Finished history: `docs/todo/done/` and `TODO-archive.md` (append-only). Record known-but-unfixed failures as `status: known-failure` task files. This repo is public: no credentials, bucket names or private infrastructure details in task files.
