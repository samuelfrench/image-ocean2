# Hugging Face dataset build

Turns `output/` (PNG + JSON sidecar per image) into the Parquet dataset published at
[samfrench9/image-ocean2-sdxl-82k](https://huggingface.co/datasets/samfrench9/image-ocean2-sdxl-82k).

Run in order (base conda env: torch, transformers, pandas, pyarrow, pillow, matplotlib):

```bash
python scripts/hf_dataset/score.py --png-dir output --out scores.parquet
python scripts/hf_dataset/build_shards.py --png-dir output --meta-dir output --scores scores.parquet --out dist
python scripts/hf_dataset/make_card.py --out dist --png-dir output --repo-id samfrench9/image-ocean2-sdxl-82k
```

- `score.py` — LAION improved aesthetic predictor v2 (CLIP ViT-L/14) and `Falconsai/nsfw_image_detection`; resumable.
- `build_shards.py` — lossless WebP (pixel-identical to the PNG) + full recipe columns, ~500-row Parquet shards with Hugging Face `Image` feature metadata, plus `metadata/metadata.parquet` without image bytes. Drops images with `nsfw_prob >= 0.5`, ids in `--exclude`, and PNGs without a sidecar; lists them in `build-report.json`.
- `make_card.py` — dataset card `README.md` with stats, sample grid, seed-sweep grid and charts in `dist/assets/`.

Upload with `huggingface_hub.HfApi().upload_large_folder(repo_id, repo_type="dataset", folder_path="dist", allow_patterns=["data/*.parquet", "metadata/*.parquet", "assets/*", "README.md"])`.
