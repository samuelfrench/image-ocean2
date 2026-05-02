# image-ocean2 — Always-On Background Service

**Date:** 2026-05-02  
**Status:** Approved

## Goal

Run `generate.py --forever` continuously at lowest CPU and I/O priority, surviving reboots and unattended shutoffs, with no manual restart required.

## Architecture

A single systemd user service unit. No changes to `generate.py`.

## Components

### `~/.config/systemd/user/image-ocean2.service`

```ini
[Unit]
Description=image-ocean2 background image generator
After=network.target

[Service]
ExecStart=/home/sam/miniconda3/bin/python /home/sam/claude-workspace/image-ocean2/generate.py --forever
WorkingDirectory=/home/sam/claude-workspace/image-ocean2
Restart=always
RestartSec=10
Nice=19
IOSchedulingClass=idle
Environment=TOKENIZERS_PARALLELISM=false
Environment=TRANSFORMERS_VERBOSITY=error

[Install]
WantedBy=default.target
```

- `Nice=19` — lowest CPU scheduling priority on Linux
- `IOSchedulingClass=idle` — I/O only proceeds when no other process needs the disk
- `Restart=always` — auto-restart after crash or clean exit; `RestartSec=10` prevents tight restart loops
- Explicit Python path (`/home/sam/miniconda3/bin/python`) avoids PATH ambiguity in headless sessions
- `TOKENIZERS_PARALLELISM` and `TRANSFORMERS_VERBOSITY` carried over from `generate.py` defaults

### `loginctl enable-linger sam`

One-time command. Instructs systemd to start and maintain user services for `sam` at boot, without requiring an active login session. Persists across reboots.

## Management

```bash
systemctl --user start image-ocean2      # start now
systemctl --user stop image-ocean2       # pause
systemctl --user restart image-ocean2    # restart
systemctl --user status image-ocean2     # check state
journalctl --user -u image-ocean2 -f     # tail logs
```

## Error Handling

- Process crash: systemd restarts after 10 s
- PC shutdown: service stops cleanly; restarts at next boot via linger
- VRAM OOM: process exits, systemd restarts after 10 s (existing `--forever` behavior already catches most errors)

## Out of Scope

- GPU utilization detection / pause-when-busy (deferred; user confirmed lowest-priority CPU/IO is sufficient for now)
- Conda environment activation (base env is active by default; direct Python path is sufficient)
