---
title: "Publish the 82k-image archive as a Hugging Face dataset"
status: now
area: data
due: null
updated: 2026-10-03
owner: agent
brief: "Restore the S3 Glacier archive, score, shard to Parquet and publish samfrench9/image-ocean2-sdxl-82k (CC0)"
refs:
  - "scripts/hf_dataset/"
test: null
---

- **What:** publish every image this repo generated (82,492 PNG + JSON sidecars, 2026-04-20 → 2026-05-13, all `sdxl-refined`) as a public CC0 dataset `samfrench9/image-ocean2-sdxl-82k` on Hugging Face. Sam asked for the upload on 2026-10-03.
- **Why this framing:** only ~225 distinct prompt subjects, ~367 seeds each, every image with its full generation recipe. Lead the card with the seed-variance angle, not "high quality stock". A free-stock SEO site was evaluated and rejected the same day (StockCake already serves 25M+ public-domain AI images; 82k pages from 225 prompts would be near-duplicates).
- **State (2026-10-03):** the archive lives in Sam's S3 overflow bucket (bucket + prefix in `~/hf-staging/image-ocean2/ops/env`, deliberately not committed — this repo is public). PNGs are storage class GLACIER (lifecycle moves objects >128 KB); JSON sidecars are STANDARD. Bulk restore of all 82,492 PNGs submitted 2026-10-03 ~16:10 UTC with `Days=14` (log `~/hf-staging/image-ocean2/logs/restore.log`: 82,480 requested, 11 already in progress, 1 `InvalidObjectState` = not archived). Bulk restores complete in 5–12 h. Staging dir: `~/hf-staging/image-ocean2/` (`png/`, `meta/`, `ops/`, `logs/`).
- **Plan:** (1) download restored PNGs (`aws s3 sync … --force-glacier-transfer`); (2) score every image with the LAION improved aesthetic predictor (CLIP ViT-L/14) and an NSFW classifier, drop flagged images after visual spot-check; (3) re-encode PNG → lossless WebP (pixel-identical, smaller) and write ~500 MB Parquet shards with the full recipe columns; (4) build card assets (sample grid, seed-sweep grid, category chart); (5) upload private with `upload_large_folder`, verify loading, then flip public. Free HF accounts get 100 GB private storage, so the private staging copy must stay under that.
- **Cost:** AWS restore + egress for ~105 GB ≤ ~$15 one-off; restored copies bill at S3 Standard for 14 days (~$1). Hugging Face public storage is free (best-effort).
- **Done when:** the dataset is public, `datasets.load_dataset(..., streaming=True)` returns rows with images, the Dataset Viewer renders, the card has stats + sample grids, and the repo README links to it.
