# docs/todo — one file per task

`TODO.md` at the repo root is **generated**. The tasks live here, one Markdown file each, and
`node scripts/todo/build.mjs` turns them into the one-screen `TODO.md` plus the machine-readable
`docs/todo/index.json`. Never hand-edit `TODO.md`; CI (`build.mjs --check`) fails on drift.

The tooling is copied from coffee-explorer's reference implementation (Node built-ins only, no
`npm install`). Adapted here: the area list and the `TODO.md` title in `scripts/todo/lib.mjs`.

## Layout

- `docs/todo/<area>/<slug>.md`: open tasks (any status except `done`).
- `docs/todo/done/<area>/<slug>.md`: finished tasks. `build.mjs` moves a file here when its status
  becomes `done`, and back out if it is reopened.
- `docs/todo/index.json`: generated; every task's frontmatter plus its path.
- `docs/todo/migration-2026-10-03.md`: where each line of the old hand-maintained TODO.md went
  (input metadata: `migration-2026-10-03-metas.json`).
- `TODO-archive.md` (repo root): append-only history. The old `## Done` list moved there verbatim
  on 2026-10-03. Move long finished history there with an `<a id="...">` anchor and list the anchor
  in the task's `refs`.

## A task file

```markdown
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
test: null
---

- **What:** one line on the task.
- **Why:** why it matters, with the number that says so.
- **Next:** the exact next step (command, file:line, date).

Detail below: measurements, commands, history, open `- [ ]` items.
```

| Field | Required | Values |
|---|---|---|
| `title` | yes | plain title, no `[STATUS]` prefix |
| `status` | yes | `now` · `waiting-sam` · `scheduled` · `next` · `idea` · `known-failure` · `done` |
| `area` | yes | `models` `cli` `gallery` `service` `data` `docs` `ci` `process` (the list and what each covers live in `scripts/todo/lib.mjs`) |
| `due` | yes | `YYYY-MM-DD` or `null`; required for `scheduled`. The earliest date an open item is due or may first be read |
| `updated` | yes | `YYYY-MM-DD` of the last status change |
| `owner` | yes | `sam` (Sam must act next) or `agent` |
| `brief` | yes | one line shown in TODO.md: current state or next step |
| `refs` | yes | list (may be `[]`): commits, files, run IDs, `TODO-archive.md#anchor` |
| `test` | for `known-failure` | the exact failing test, job or command |

Statuses, first match wins: `done` (nothing open) · `known-failure` (a red test/job we have
deliberately not fixed) · `waiting-sam` (needs Sam's decision, approval or account action) ·
`scheduled` (gated on a date) · `now` (in progress or top priority this week) · `next` (open, an
agent can do it) · `idea` (proposal, backlog, paused).

Keep a file at about 150 lines or fewer. When it grows past that, keep the summary, the open items
and the latest state, and move older history verbatim to `TODO-archive.md`.

This repo is public. Task files must not carry credentials, bucket names or other private
infrastructure details.

## Workflow

- **Start of session:** read `TODO.md` (generated, one screen). For detail open the linked file.
- **Add a task:** create `docs/todo/<area>/<slug>.md` with the frontmatter above and the
  What / Why / Next summary, run `node scripts/todo/build.mjs`, and commit the task file,
  `TODO.md` and `docs/todo/index.json` in **one** commit.
- **Update a task:** edit its file (status, `due`, `updated`, `brief`, body), rebuild, commit
  together. Update in the same working beat as the work, never batched for session end.
- **Close a task:** set `status: done`, write the result in the body, rebuild (the file moves to
  `docs/todo/done/<area>/`), commit.
- **Look things up:**
  - `node scripts/todo/query.mjs --status now,waiting-sam`
  - `node scripts/todo/query.mjs --area models --owner agent`
  - `node scripts/todo/query.mjs --due-before 2026-12-01` (due on or before; undated tasks excluded)
  - `node scripts/todo/query.mjs --test <name>` (known failures by test name)
  - `node scripts/todo/query.mjs --grep FLUX --all` (`--all` includes done; `--json` for JSON)
  - `jq '.[] | select(.status=="idea")' docs/todo/index.json`, or plain `grep -rl 'status: now' docs/todo`.
- **Check before pushing:** `node scripts/todo/build.mjs --check` (exit 1 on stale output, a missing
  or unknown field, a bad date, or a done file outside `done/`). Tests:
  `node --test scripts/todo/__tests__/*.test.mjs`.

## Known non-blocking failures — check here BEFORE diagnosing a red suite

These are task files with `status: known-failure`. The generated `TODO.md` lists them under this
exact heading, and `node scripts/todo/query.mjs --status known-failure` (or `--test <name>`) finds
them. Record a failure the moment you decide not to fix it now. Each file needs: the exact test or
command (`test:`), the observed failure text, the evidence that it is not a regression (it passed in
isolation, it reproduced on the parent commit, it was seen independently), the trigger condition, and
the real fix you are not doing. A real but deferred failure is recorded the same way, and it says so.

## Rules that carry over

- **Write ideas down when they occur**, in a task file (`status: idea`) or in the related task:
  defects you are not fixing, with the measurement that shows they are real; **ideas you rejected
  and the number that killed them**; what you were in the middle of when interrupted; follow-ups
  your own change creates.
- **Make entries executable without your context:** exact `file:line`, the measured value, the
  command that reproduces it, what done looks like, and the gotcha that will bite the next agent.
- **Checkpoint and commit mid-task** at every milestone. `.github/workflows/todo.yml` runs the todo
  tests and `build.mjs --check` on GitHub-hosted `ubuntu-latest` for every push and pull request
  that touches `TODO.md`, `docs/todo/**` or `scripts/todo/**`. The repo has no deploy workflow.
- **Never report a task's status from its file alone**. Files are snapshots; verify against the
  live artifact before saying something is done or pending.
