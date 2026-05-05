#!/usr/bin/env python3
"""image-ocean2 local gallery.

A tiny stdlib-only web server that renders ``output/`` as a responsive
thumbnail grid. Reads each PNG's JSON sidecar so cards show the category
and full prompt subject. The index is rebuilt from disk on every request,
so images created by an in-flight ``--forever`` run show up the moment
you reload — and the live feed prepends them without a reload.

Auto-scrolling features
-----------------------
* **Ambient page scroll** — header button (or spacebar) toggles a slow
  continuous downward scroll that wraps to the top at the bottom edge.
* **Live feed** — polls ``/api/list`` every 5 s and prepends new images
  with a brief highlight pulse. Shows a "+N new" pill when scrolled
  away from the top.
* **Lightbox slideshow** — play/pause button (or spacebar) inside the
  lightbox advances every 4 s through the currently visible cards;
  arrow keys for prev/next.

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
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"
INITIAL_PAGE_SIZE = 200  # how many cards the server renders into the initial HTML
PAGE_SIZE = 200  # /api/page batch size for infinite-scroll loads


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>image-ocean2 gallery — __TOTAL__ images</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #0d0d0f; color: #e6e6e6; margin: 0;
  }
  header {
    position: sticky; top: 0; z-index: 20;
    background: rgba(13,13,15,0.92); backdrop-filter: blur(8px);
    padding: 0.75rem 1.25rem; border-bottom: 1px solid #222;
    display: flex; align-items: baseline; gap: 1rem; flex-wrap: wrap;
  }
  h1 { font-size: 1.1rem; margin: 0; font-weight: 600; }
  .count { color: #888; font-size: 0.9rem; }
  .controls { margin-left: auto; display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
  select, button, input[type=search] {
    background: #1a1a1d; color: #eee; border: 1px solid #333;
    padding: 0.4rem 0.7rem; border-radius: 6px; font-size: 0.85rem;
    font-family: inherit;
  }
  button { cursor: pointer; }
  button:hover, select:hover, input:hover { border-color: #555; }
  button.active { background: #15323f; border-color: #6cf; color: #6cf; }
  input[type=search] { width: 200px; }
  .live-dot {
    display: inline-block; width: 8px; height: 8px; border-radius: 50%;
    background: #555; margin-right: 0.4rem; vertical-align: middle;
    transition: background 0.2s, box-shadow 0.2s;
  }
  .live-dot.on {
    background: #4cd964;
    box-shadow: 0 0 6px rgba(76, 217, 100, 0.7);
    animation: live-pulse 2s ease-in-out infinite;
  }
  @keyframes live-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.45; }
  }
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
    /* Browser-native virtualization: skip layout/paint for off-screen
       cards. contain-intrinsic-size reserves space so the scrollbar
       and scrollHeight stay stable while skipped content exists. */
    content-visibility: auto;
    contain-intrinsic-size: 320px 360px;
  }
  .card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.5);
  }
  /* Aspect-ratio fallback when an image lacks width/height attrs.
     Modern browsers derive aspect ratio from width/height attrs, so
     this only kicks in for sidecars missing dimensions. */
  .card img { width: 100%; height: auto; display: block; background: #222; aspect-ratio: 1 / 1; }
  .card.new { animation: pulse-new 1.6s ease-out; }
  @keyframes pulse-new {
    0%   { box-shadow: 0 0 0 0   rgba(108, 207, 255, 0.75); }
    100% { box-shadow: 0 0 0 14px rgba(108, 207, 255, 0);    }
  }
  .meta {
    padding: 0.6rem 0.75rem; font-size: 0.82rem; line-height: 1.4;
    border-top: 1px solid #222;
  }
  .cat {
    display: inline-block; font-size: 0.7rem; text-transform: uppercase;
    letter-spacing: 0.05em; color: #6cf; font-weight: 600;
  }
  .subj { color: #aaa; margin-top: 0.25rem; display: block; }
  .new-pill {
    position: fixed; top: 4.2rem; left: 50%; transform: translateX(-50%);
    background: #6cf; color: #0d0d0f; padding: 0.45rem 1rem;
    border-radius: 999px; font-size: 0.85rem; font-weight: 600;
    cursor: pointer; opacity: 0; pointer-events: none;
    transition: opacity 0.25s, transform 0.25s; z-index: 50;
    box-shadow: 0 4px 16px rgba(0,0,0,0.4);
  }
  .new-pill.show {
    opacity: 1; pointer-events: auto;
    transform: translateX(-50%) translateY(0);
  }
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
    font-size: 2rem; cursor: pointer; user-select: none; z-index: 110;
  }
  .lb-controls {
    position: fixed; bottom: 1rem; right: 1.25rem; z-index: 110;
    display: flex; gap: 0.5rem;
  }
  .lb-controls button {
    background: rgba(0,0,0,0.7); color: #eee; border: 1px solid #444;
    width: 42px; height: 42px; border-radius: 50%; font-size: 1rem;
    padding: 0; line-height: 1;
  }
  .lb-controls button:hover { border-color: #6cf; color: #6cf; }
  .lb-nav {
    position: fixed; top: 50%; transform: translateY(-50%);
    color: #ccc; font-size: 2.4rem; cursor: pointer;
    user-select: none; padding: 1rem 1.25rem; z-index: 110;
    opacity: 0.5; transition: opacity 0.15s;
  }
  .lb-nav:hover { opacity: 1; color: #6cf; }
  .lb-prev { left: 0.5rem; }
  .lb-next { right: 0.5rem; }
  .empty { color: #666; padding: 3rem; text-align: center; }
  .sentinel { color: #555; padding: 2rem 1rem 4rem; text-align: center; font-size: 0.85rem; }
  .sentinel.done { color: #444; }
</style>
</head>
<body>
<header>
  <h1>image-ocean2</h1>
  <span class="count" id="count" data-total="__TOTAL__">__N__ of __TOTAL__ images</span>
  <div class="controls">
    <input type="search" id="search" placeholder="filter by prompt…">
    <select id="filter">
      <option value="">all categories</option>
      __OPTIONS__
    </select>
    <button id="ambient-btn" title="Toggle ambient auto-scroll (space)">▶ scroll</button>
    <button id="live-btn" class="active" title="Toggle live feed polling"><span class="live-dot on" id="live-dot"></span>live</button>
    <button onclick="location.reload()" title="Reload from disk">refresh</button>
  </div>
</header>
<div class="new-pill" id="new-pill" title="Click to jump to top">+0 new</div>
<main>
  <div class="grid" id="grid">
    __CARDS__
  </div>
  <div class="sentinel" id="sentinel">Loading more…</div>
</main>
<div class="lightbox" id="lightbox">
  <span class="lb-close" onclick="closeLightbox()" title="Close (Esc)">×</span>
  <span class="lb-nav lb-prev" id="lb-prev" title="Previous (←)">‹</span>
  <span class="lb-nav lb-next" id="lb-next" title="Next (→)">›</span>
  <img id="lb-img" src="" alt="">
  <div class="lb-meta" id="lb-meta"></div>
  <div class="lb-controls">
    <button id="ss-btn" title="Toggle slideshow (space)">▶</button>
  </div>
</div>
<script>
"use strict";

const grid = document.getElementById('grid');
const lb = document.getElementById('lightbox');
const lbImg = document.getElementById('lb-img');
const lbMeta = document.getElementById('lb-meta');
const filter = document.getElementById('filter');
const search = document.getElementById('search');
const countEl = document.getElementById('count');
const sentinel = document.getElementById('sentinel');
const ambientBtn = document.getElementById('ambient-btn');
const liveBtn = document.getElementById('live-btn');
const liveDot = document.getElementById('live-dot');
const newPill = document.getElementById('new-pill');
const ssBtn = document.getElementById('ss-btn');
const lbPrev = document.getElementById('lb-prev');
const lbNext = document.getElementById('lb-next');

let totalOnDisk = parseInt(countEl.dataset.total || '0', 10) || 0;

function updateCount() {
  const all = document.querySelectorAll('.card');
  const n = all.length;
  const cat = filter.value;
  const q = search.value.trim().toLowerCase();
  if (cat || q) {
    let visible = 0;
    all.forEach(c => { if (c.style.display !== 'none') visible++; });
    countEl.textContent = visible + ' / ' + n + ' loaded' + (n < totalOnDisk ? ' (' + totalOnDisk + ' total)' : '');
  } else {
    countEl.textContent = n < totalOnDisk
      ? n + ' of ' + totalOnDisk + ' images'
      : n + ' images';
  }
}

// ---------- Filtering ----------
function applyFilters() {
  const cat = filter.value;
  const q = search.value.trim().toLowerCase();
  const all = document.querySelectorAll('.card');
  all.forEach(c => {
    const matchCat = !cat || c.dataset.cat === cat;
    const matchQ = !q || c.dataset.subj.toLowerCase().includes(q);
    c.style.display = (matchCat && matchQ) ? '' : 'none';
  });
  updateCount();
}
filter.addEventListener('change', applyFilters);
search.addEventListener('input', applyFilters);

// ---------- Lightbox ----------
let currentLbCard = null;

function visibleCards() {
  return Array.from(document.querySelectorAll('.card'))
    .filter(c => c.style.display !== 'none');
}

function openLightbox(card) {
  currentLbCard = card;
  lbImg.src = card.dataset.full;
  lbMeta.textContent = '[' + card.dataset.cat + '] ' + card.dataset.subj;
  lb.classList.add('open');
  if (slideshowOn) restartSlideshowTimer();
}

function closeLightbox() {
  lb.classList.remove('open');
  lbImg.src = '';
  currentLbCard = null;
  stopSlideshowTimer();
}

function stepLightbox(dir) {
  const cards = visibleCards();
  if (cards.length === 0) return;
  let idx = cards.indexOf(currentLbCard);
  if (idx < 0) idx = 0;
  const next = cards[(idx + dir + cards.length) % cards.length];
  openLightbox(next);
}

lb.addEventListener('click', e => {
  if (e.target === lb || e.target === lbImg) closeLightbox();
});
lbPrev.addEventListener('click', e => { e.stopPropagation(); stepLightbox(-1); if (slideshowOn) restartSlideshowTimer(); });
lbNext.addEventListener('click', e => { e.stopPropagation(); stepLightbox(1);  if (slideshowOn) restartSlideshowTimer(); });

function attachCardHandlers(card) {
  card.addEventListener('click', () => openLightbox(card));
}
document.querySelectorAll('.card').forEach(attachCardHandlers);

// ---------- Ambient auto-scroll ----------
const AMBIENT_PX_PER_SEC = 30;
let ambientOn = false;
let ambientLast = 0;

function ambientStep(ts) {
  if (!ambientOn) return;
  if (lb.classList.contains('open')) {
    ambientLast = ts;  // hold steady while paused
    requestAnimationFrame(ambientStep);
    return;
  }
  if (ambientLast) {
    const dt = (ts - ambientLast) / 1000;
    const dy = AMBIENT_PX_PER_SEC * dt;
    const max = document.documentElement.scrollHeight - window.innerHeight;
    if (max <= 0) {
      // nothing to scroll yet
    } else if (window.scrollY + dy >= max) {
      window.scrollTo(0, 0);
    } else {
      window.scrollBy(0, dy);
    }
  }
  ambientLast = ts;
  requestAnimationFrame(ambientStep);
}

function setAmbient(on) {
  ambientOn = on;
  ambientLast = 0;
  ambientBtn.classList.toggle('active', on);
  ambientBtn.textContent = on ? '⏸ scroll' : '▶ scroll';
  if (on) requestAnimationFrame(ambientStep);
}
ambientBtn.addEventListener('click', () => setAmbient(!ambientOn));

// ---------- Live feed ----------
const POLL_MS = 5000;
const NEAR_TOP_PX = 200;
let liveOn = true;
let latestMtime = 0;
let pendingNew = 0;

(function initLatest() {
  const first = document.querySelector('.card');
  if (!first) return;
  const m = parseFloat(first.dataset.mtime);
  if (!isNaN(m)) latestMtime = m;
})();

function makeCard(item) {
  const div = document.createElement('div');
  div.className = 'card new';
  div.dataset.cat = item.cat;
  div.dataset.subj = item.subj;
  div.dataset.mtime = String(item.mtime);
  div.dataset.full = item.url;

  const img = document.createElement('img');
  img.loading = 'lazy';
  img.decoding = 'async';
  // width/height attrs let the browser reserve aspect-ratio space,
  // preventing layout shift when the image decodes.
  if (item.w && item.h) { img.width = item.w; img.height = item.h; }
  img.src = item.url;
  img.alt = item.subj;

  const meta = document.createElement('div');
  meta.className = 'meta';
  const cat = document.createElement('span');
  cat.className = 'cat';
  cat.textContent = item.cat;
  const subj = document.createElement('span');
  subj.className = 'subj';
  subj.textContent = item.subj;
  meta.appendChild(cat);
  meta.appendChild(subj);

  div.appendChild(img);
  div.appendChild(meta);
  div.addEventListener('animationend', () => div.classList.remove('new'));
  attachCardHandlers(div);
  return div;
}

function showNewPill() {
  newPill.textContent = '+' + pendingNew + ' new ↑';
  newPill.classList.add('show');
}
function hideNewPill() {
  pendingNew = 0;
  newPill.classList.remove('show');
}
newPill.addEventListener('click', () => {
  window.scrollTo({ top: 0, behavior: 'smooth' });
  hideNewPill();
});
window.addEventListener('scroll', () => {
  if (window.scrollY <= NEAR_TOP_PX && pendingNew > 0) hideNewPill();
});

async function pollOnce() {
  try {
    const r = await fetch('/api/list?since=' + encodeURIComponent(latestMtime));
    if (!r.ok) return;
    const data = await r.json();
    const items = data.images || [];
    if (items.length === 0) return;

    const empty = grid.querySelector('.empty');
    if (empty) empty.remove();

    const prevScrollY = window.scrollY;
    const prevScrollHeight = document.documentElement.scrollHeight;

    const anchor = grid.querySelector('.card');
    for (const it of items) {
      const card = makeCard(it);
      if (anchor) grid.insertBefore(card, anchor);
      else grid.appendChild(card);
      if (it.mtime > latestMtime) latestMtime = it.mtime;
    }
    totalOnDisk = Math.max(totalOnDisk, data.total || 0);
    applyFilters();

    // Preserve visual position when content is prepended above the viewport.
    // Skip when at true top (scrollY === 0) so the user naturally sees new arrivals.
    if (prevScrollY > 0) {
      const heightAdded = document.documentElement.scrollHeight - prevScrollHeight;
      if (heightAdded > 0) window.scrollTo(0, prevScrollY + heightAdded);
      pendingNew += items.length;
      showNewPill();
    }
  } catch (e) {
    // network blip — try again next interval
  }
}

async function pollLoop() {
  if (liveOn) await pollOnce();
  setTimeout(pollLoop, POLL_MS);
}
pollLoop();

function setLive(on) {
  liveOn = on;
  liveDot.classList.toggle('on', on);
  liveBtn.classList.toggle('active', on);
}
liveBtn.addEventListener('click', () => setLive(!liveOn));

// ---------- Infinite scroll ----------
let pageLoading = false;
let pageDone = false;
let oldestMtime = 0;

(function initOldest() {
  const cards = document.querySelectorAll('.card');
  if (!cards.length) { pageDone = true; return; }
  let m = Infinity;
  cards.forEach(c => {
    const v = parseFloat(c.dataset.mtime);
    if (!isNaN(v) && v < m) m = v;
  });
  if (isFinite(m)) oldestMtime = m;
  if (cards.length >= totalOnDisk) pageDone = true;
})();

async function loadNextPage() {
  if (pageLoading || pageDone) return;
  pageLoading = true;
  try {
    const r = await fetch('/api/page?before=' + encodeURIComponent(oldestMtime) + '&limit=200');
    if (!r.ok) return;
    const data = await r.json();
    const items = data.images || [];
    totalOnDisk = Math.max(totalOnDisk, data.total || 0);
    if (items.length === 0) {
      pageDone = true;
      sentinel.classList.add('done');
      sentinel.textContent = 'End of gallery — ' + document.querySelectorAll('.card').length + ' loaded.';
      io.unobserve(sentinel);
      return;
    }
    // Bypass the "new" pulse animation on backfilled cards.
    const frag = document.createDocumentFragment();
    for (const it of items) {
      const card = makeCard(it);
      card.classList.remove('new');
      frag.appendChild(card);
      if (it.mtime < oldestMtime || oldestMtime === 0) oldestMtime = it.mtime;
    }
    grid.appendChild(frag);
    applyFilters();
    if (document.querySelectorAll('.card').length >= totalOnDisk) {
      pageDone = true;
      sentinel.classList.add('done');
      sentinel.textContent = 'End of gallery — ' + totalOnDisk + ' images.';
      io.unobserve(sentinel);
    }
  } catch (e) {
    // try again on next intersection
  } finally {
    pageLoading = false;
  }
}

const io = new IntersectionObserver(entries => {
  for (const e of entries) {
    if (e.isIntersecting) loadNextPage();
  }
}, { rootMargin: '1500px 0px' });

if (sentinel && !pageDone) io.observe(sentinel);
else if (sentinel) {
  sentinel.classList.add('done');
  sentinel.textContent = 'End of gallery.';
}

// ---------- Lightbox slideshow ----------
const SLIDESHOW_MS = 4000;
let slideshowOn = false;
let slideshowTimer = null;

function startSlideshow() {
  slideshowOn = true;
  ssBtn.textContent = '❚❚';
  ssBtn.classList.add('active');
  restartSlideshowTimer();
}
function stopSlideshow() {
  slideshowOn = false;
  ssBtn.textContent = '▶';
  ssBtn.classList.remove('active');
  stopSlideshowTimer();
}
function restartSlideshowTimer() {
  stopSlideshowTimer();
  slideshowTimer = setInterval(() => stepLightbox(1), SLIDESHOW_MS);
}
function stopSlideshowTimer() {
  if (slideshowTimer) {
    clearInterval(slideshowTimer);
    slideshowTimer = null;
  }
}
ssBtn.addEventListener('click', e => {
  e.stopPropagation();
  slideshowOn ? stopSlideshow() : startSlideshow();
});
lbImg.addEventListener('mouseenter', () => { if (slideshowOn) stopSlideshowTimer(); });
lbImg.addEventListener('mouseleave', () => { if (slideshowOn) restartSlideshowTimer(); });

// ---------- Keyboard ----------
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    if (lb.classList.contains('open')) closeLightbox();
    return;
  }
  const tag = (document.activeElement && document.activeElement.tagName) || '';
  if (tag === 'INPUT' || tag === 'TEXTAREA') return;

  if (lb.classList.contains('open')) {
    if (e.key === 'ArrowRight') {
      e.preventDefault();
      stepLightbox(1);
      if (slideshowOn) restartSlideshowTimer();
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      stepLightbox(-1);
      if (slideshowOn) restartSlideshowTimer();
    } else if (e.key === ' ') {
      e.preventDefault();
      slideshowOn ? stopSlideshow() : startSlideshow();
    }
  } else {
    if (e.key === ' ' && tag !== 'BUTTON' && tag !== 'SELECT') {
      e.preventDefault();
      setAmbient(!ambientOn);
    }
  }
});
</script>
</body>
</html>
"""


_INDEX_CACHE: dict = {"dir_mtime": -1.0, "items": []}


def list_images() -> list[dict]:
    """Walk OUTPUT_DIR and return image records sorted newest-first.

    Cached by directory mtime — adding/removing a file in OUTPUT_DIR
    bumps its mtime, so a fresh walk runs only when the contents have
    changed. With 20k+ files this avoids re-reading 20k JSON sidecars
    on every page hit and every 5 s live-feed poll.
    """
    if not OUTPUT_DIR.exists():
        return []
    dir_mtime = OUTPUT_DIR.stat().st_mtime
    if _INDEX_CACHE["dir_mtime"] == dir_mtime:
        return _INDEX_CACHE["items"]

    entries = []
    with os.scandir(OUTPUT_DIR) as it:
        for e in it:
            if e.is_file() and e.name.endswith(".png"):
                try:
                    entries.append((e.path, e.name, e.stat().st_mtime))
                except OSError:
                    pass
    entries.sort(key=lambda t: t[2], reverse=True)

    items: list[dict] = []
    for path, name, mtime in entries:
        json_p = Path(path).with_suffix(".json")
        cat, subj, w, h = "?", name.rsplit(".", 1)[0], 0, 0
        try:
            meta = json.loads(json_p.read_text())
            cat = meta.get("category") or "?"
            subj = meta.get("prompt_subject") or subj
            w = int(meta.get("width") or 0)
            h = int(meta.get("height") or 0)
        except Exception:
            pass
        items.append({
            "name": name,
            "url": f"/output/{name}",
            "cat": cat,
            "subj": subj,
            "w": w,
            "h": h,
            "mtime": mtime,
        })

    _INDEX_CACHE["dir_mtime"] = dir_mtime
    _INDEX_CACHE["items"] = items
    return items


def render_card_html(it: dict) -> str:
    """One card's HTML — shared by initial render and any future SSR path."""
    dim_attrs = (
        f' width="{it["w"]}" height="{it["h"]}"'
        if it.get("w") and it.get("h")
        else ""
    )
    return (
        f'<div class="card" '
        f'data-cat="{html.escape(it["cat"], quote=True)}" '
        f'data-subj="{html.escape(it["subj"], quote=True)}" '
        f'data-mtime="{it["mtime"]:.6f}" '
        f'data-full="{it["url"]}">'
        f'<img loading="lazy" decoding="async"{dim_attrs} '
        f'src="{it["url"]}" alt="{html.escape(it["subj"], quote=True)}">'
        f'<div class="meta"><span class="cat">{html.escape(it["cat"])}</span>'
        f'<span class="subj">{html.escape(it["subj"])}</span></div>'
        f"</div>"
    )


def render_index() -> str:
    items = list_images()
    total = len(items)
    if not items and not OUTPUT_DIR.exists():
        return (
            PAGE.replace("__N__", "0")
            .replace("__TOTAL__", "0")
            .replace("__OPTIONS__", "")
            .replace("__CARDS__", '<div class="empty">No output/ directory yet.</div>')
        )

    # Categories are derived from the full set so the dropdown stays accurate
    # even though only the first INITIAL_PAGE_SIZE cards ship in the HTML.
    cats: set[str] = {it["cat"] for it in items}
    initial = items[:INITIAL_PAGE_SIZE]
    cards = [render_card_html(it) for it in initial]

    options = "\n".join(
        f'<option value="{html.escape(c, quote=True)}">{html.escape(c)}</option>'
        for c in sorted(cats)
    )
    return (
        PAGE.replace("__N__", str(len(initial)))
        .replace("__TOTAL__", str(total))
        .replace("__OPTIONS__", options)
        .replace("__CARDS__", "\n".join(cards) or '<div class="empty">No images yet.</div>')
    )


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 (stdlib name)
        if self.path in ("/", "/index.html"):
            body = render_index().encode("utf-8")
            self._send_bytes(body, "text/html; charset=utf-8")
            return
        if self.path.startswith("/api/list"):
            self._serve_list_json()
            return
        if self.path.startswith("/api/page"):
            self._serve_page_json()
            return
        super().do_GET()

    def end_headers(self) -> None:  # noqa: N802 (stdlib name)
        # Long-lived public cache for static image bytes — file paths embed
        # a timestamp+seed so they're effectively immutable.
        if self.path.startswith("/output/"):
            self.send_header("Cache-Control", "public, max-age=86400, immutable")
        super().end_headers()

    def _send_bytes(self, body: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_list_json(self) -> None:
        qs = parse_qs(urlsplit(self.path).query)
        try:
            since = float(qs.get("since", ["0"])[0])
        except (TypeError, ValueError):
            since = 0.0
        all_items = list_images()
        new_items = [it for it in all_items if it["mtime"] > since]
        body = json.dumps({"images": new_items, "total": len(all_items)}).encode("utf-8")
        self._send_bytes(body, "application/json; charset=utf-8")

    def _serve_page_json(self) -> None:
        """Older-than cursor pagination for infinite scroll.

        ``before`` is the mtime of the oldest currently-loaded card; the
        server returns up to ``limit`` items strictly older than that.
        ``before=0`` (or omitted) means start from the newest.
        """
        qs = parse_qs(urlsplit(self.path).query)
        try:
            before = float(qs.get("before", ["0"])[0])
        except (TypeError, ValueError):
            before = 0.0
        try:
            limit = int(qs.get("limit", [str(PAGE_SIZE)])[0])
        except (TypeError, ValueError):
            limit = PAGE_SIZE
        limit = max(1, min(limit, 1000))
        all_items = list_images()
        if before <= 0:
            page = all_items[:limit]
        else:
            page = [it for it in all_items if it["mtime"] < before][:limit]
        body = json.dumps({"images": page, "total": len(all_items)}).encode("utf-8")
        self._send_bytes(body, "application/json; charset=utf-8")

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
