#!/usr/bin/env python3
"""image-ocean2 local gallery.

A tiny stdlib-only web server that renders ``output/`` as a responsive
thumbnail grid. Reads each PNG's JSON sidecar so cards show the category
and full prompt subject. The index is rebuilt from disk on every request,
so images created by an in-flight ``--forever`` run show up the moment
you reload.

Usage:
  python gallery.py                     # http://127.0.0.1:8765
  python gallery.py --port 9000
  python gallery.py --host 0.0.0.0      # expose to LAN (careful)
"""

from __future__ import annotations

import argparse
import html
import http.server
import json
import os
import socketserver
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>image-ocean2 gallery — __N__ images</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #0d0d0f; color: #e6e6e6; margin: 0;
  }
  header {
    position: sticky; top: 0; z-index: 10;
    background: rgba(13,13,15,0.92); backdrop-filter: blur(8px);
    padding: 0.75rem 1.25rem; border-bottom: 1px solid #222;
    display: flex; align-items: baseline; gap: 1rem; flex-wrap: wrap;
  }
  h1 { font-size: 1.1rem; margin: 0; font-weight: 600; }
  .count { color: #888; font-size: 0.9rem; }
  .controls { margin-left: auto; display: flex; gap: 0.5rem; align-items: center; }
  select, button, input[type=search] {
    background: #1a1a1d; color: #eee; border: 1px solid #333;
    padding: 0.4rem 0.7rem; border-radius: 6px; font-size: 0.85rem;
    font-family: inherit;
  }
  button { cursor: pointer; }
  button:hover, select:hover, input:hover { border-color: #555; }
  input[type=search] { width: 200px; }
  main { padding: 1.25rem; }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 1rem;
  }
  .card {
    background: #18181b; border-radius: 8px; overflow: hidden;
    cursor: zoom-in; transition: transform 0.1s, box-shadow 0.1s;
    display: flex; flex-direction: column;
  }
  .card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.5);
  }
  .card img { width: 100%; height: auto; display: block; background: #222; }
  .meta {
    padding: 0.6rem 0.75rem; font-size: 0.82rem; line-height: 1.4;
    border-top: 1px solid #222;
  }
  .cat {
    display: inline-block; font-size: 0.7rem; text-transform: uppercase;
    letter-spacing: 0.05em; color: #6cf; font-weight: 600;
  }
  .subj { color: #aaa; margin-top: 0.25rem; display: block; }
  .lightbox {
    position: fixed; inset: 0; background: rgba(0,0,0,0.96);
    display: none; align-items: center; justify-content: center;
    z-index: 100; cursor: zoom-out;
  }
  .lightbox.open { display: flex; }
  .lightbox img {
    max-width: 96vw; max-height: 92vh;
    box-shadow: 0 8px 32px rgba(0,0,0,0.6);
  }
  .lb-meta {
    position: fixed; bottom: 1rem; left: 50%; transform: translateX(-50%);
    background: rgba(0,0,0,0.75); padding: 0.5rem 1rem; border-radius: 6px;
    font-size: 0.85rem; max-width: 90vw;
  }
  .lb-close {
    position: fixed; top: 0.75rem; right: 1.25rem; color: #ccc;
    font-size: 2rem; cursor: pointer; user-select: none;
  }
  .empty { color: #666; padding: 3rem; text-align: center; }
</style>
</head>
<body>
<header>
  <h1>image-ocean2</h1>
  <span class="count" id="count">__N__ images</span>
  <div class="controls">
    <input type="search" id="search" placeholder="filter by prompt…">
    <select id="filter">
      <option value="">all categories</option>
      __OPTIONS__
    </select>
    <button onclick="location.reload()">refresh</button>
  </div>
</header>
<main>
  <div class="grid" id="grid">
    __CARDS__
  </div>
</main>
<div class="lightbox" id="lightbox">
  <span class="lb-close" onclick="closeLightbox()">×</span>
  <img id="lb-img" src="" alt="">
  <div class="lb-meta" id="lb-meta"></div>
</div>
<script>
const lb = document.getElementById('lightbox');
const lbImg = document.getElementById('lb-img');
const lbMeta = document.getElementById('lb-meta');

function openLightbox(card) {
  lbImg.src = card.dataset.full;
  lbMeta.textContent = '[' + card.dataset.cat + '] ' + card.dataset.subj;
  lb.classList.add('open');
}
function closeLightbox() {
  lb.classList.remove('open');
  lbImg.src = '';
}
lb.addEventListener('click', e => {
  if (e.target === lb || e.target === lbImg) closeLightbox();
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeLightbox();
});

const cards = Array.from(document.querySelectorAll('.card'));
cards.forEach(c => c.addEventListener('click', () => openLightbox(c)));

const filter = document.getElementById('filter');
const search = document.getElementById('search');
const countEl = document.getElementById('count');
const TOTAL = __N__;

function applyFilters() {
  const cat = filter.value;
  const q = search.value.trim().toLowerCase();
  let visible = 0;
  cards.forEach(c => {
    const matchCat = !cat || c.dataset.cat === cat;
    const matchQ = !q || c.dataset.subj.toLowerCase().includes(q);
    const show = matchCat && matchQ;
    c.style.display = show ? '' : 'none';
    if (show) visible++;
  });
  countEl.textContent = (cat || q)
    ? visible + ' / ' + TOTAL + ' images'
    : TOTAL + ' images';
}
filter.addEventListener('change', applyFilters);
search.addEventListener('input', applyFilters);
</script>
</body>
</html>
"""


def render_index() -> str:
    if not OUTPUT_DIR.exists():
        return (
            PAGE.replace("__N__", "0")
            .replace("__OPTIONS__", "")
            .replace("__CARDS__", '<div class="empty">No output/ directory yet.</div>')
        )

    pngs = sorted(OUTPUT_DIR.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)

    cards: list[str] = []
    cats: set[str] = set()
    for p in pngs:
        json_p = p.with_suffix(".json")
        try:
            meta = json.loads(json_p.read_text())
            cat = meta.get("category") or "?"
            subj = meta.get("prompt_subject") or p.stem
        except Exception:
            cat, subj = "?", p.stem
        cats.add(cat)
        url = f"/output/{p.name}"
        cards.append(
            f'<div class="card" '
            f'data-cat="{html.escape(cat, quote=True)}" '
            f'data-subj="{html.escape(subj, quote=True)}" '
            f'data-full="{url}">'
            f'<img loading="lazy" src="{url}" alt="{html.escape(subj, quote=True)}">'
            f'<div class="meta"><span class="cat">{html.escape(cat)}</span>'
            f'<span class="subj">{html.escape(subj)}</span></div>'
            f"</div>"
        )

    options = "\n".join(
        f'<option value="{html.escape(c, quote=True)}">{html.escape(c)}</option>'
        for c in sorted(cats)
    )

    body = (
        PAGE.replace("__N__", str(len(pngs)))
        .replace("__OPTIONS__", options)
        .replace("__CARDS__", "\n".join(cards) or '<div class="empty">No images yet.</div>')
    )
    return body


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 (stdlib name)
        if self.path in ("/", "/index.html"):
            body = render_index().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        # Static fallthrough: serves /output/*.png and /output/*.json relative to ROOT.
        super().do_GET()

    def log_message(self, fmt: str, *args) -> None:  # noqa: N802
        # Skip 200s on /output/* — they're noisy when scrolling. Keep everything else.
        if len(args) >= 2 and str(args[1]) == "200" and self.path.startswith("/output/"):
            return
        super().log_message(fmt, *args)


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Local gallery for image-ocean2 outputs.")
    p.add_argument("--host", default="127.0.0.1", help="Bind host. Default: localhost only.")
    p.add_argument("--port", type=int, default=8765, help="Bind port.")
    args = p.parse_args(argv)

    os.chdir(ROOT)  # /output/foo.png → ./output/foo.png

    try:
        srv = ThreadedHTTPServer((args.host, args.port), Handler)
    except OSError as e:
        print(f"ERROR: could not bind {args.host}:{args.port} — {e}", file=sys.stderr)
        return 1

    url = f"http://{args.host}:{args.port}/"
    print(f"image-ocean2 gallery: {url}", flush=True)
    print("Ctrl-C to stop.", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
