---
title: "Verify the Hugging Face transfer before cleaning up the archive copy"
status: now
area: data
due: null
updated: 2026-10-04
owner: agent
brief: "Source mappings and 82,481 metadata rows verified; full image-shard download/checksum/decode running, no archive deletion"
refs:
  - "docs/todo/done/data/hf-dataset-upload.md"
  - "scripts/hf_dataset/build_shards.py"
  - "https://huggingface.co/datasets/samfrench9/image-ocean2-sdxl-82k"
test: null
---

- **What:** Sam requested cleanup of the original archive copy after independently verifying the Hugging Face dataset. Exact infrastructure scope, evidence paths and private inventories live in the image-ocean2 section of `~/TODO.md`; they must not be committed to this public repo.
- **State (2026-10-04):** verification started; no archive object deleted. Current Hub revision `c2897656e413ca1dc6590dc434ba69bb870b73f5` is public, has 172 files / 81,327,331,245 bytes and 165 image shards. The earlier private upload log reports 43 more bytes before subsequent card edits. Expected final row count from the pipeline is 82,481; independently reading all shards remains pending.
- **Source checkpoint:** 82,481 unique metadata rows exactly match the expected included IDs and all 30 normalized recipe columns; all five logged failed downloads appear in final metadata. Every local source sidecar matches its source inventory checksum. Eleven omitted images account for 20 source objects; retain another 115 original sidecars to preserve renderer details omitted from the normalized schema. The last image shard has 481 correct rows. No source object deleted.
- **Verification approach:** sparse HTTP reads of all recipe columns triggered Hub rate limiting after 20 shards in about 120 seconds. Use bounded full-shard reads with declared-size/checksum checks, row comparisons and image decoding instead; retain private resumable evidence.
- **Next:** verify every shard is present and readable; compare its rows with final metadata and the source inventory; reconcile all early failed downloads. Stop before deletion on any real transfer gap. Delete only source objects represented on the Hub, preserving deliberate exclusions and anything unmatched; handle versions and delete markers if present. Record measured retained/deleted counts and sizes and archive minimum-duration billing effects in the private operational record.
- **Done when:** verification passes, scoped deletion is confirmed by a fresh inventory, retained exclusions/unmatched objects are counted with reasons, and the global TODO/shared memory agree with current evidence.

- **Payload gate launched (2026-10-04):** bounded four-worker verification downloads each immutable shard, compares its full bytes with the Hub LFS checksum, compares every ordered row and all recipe fields with final metadata, and decodes every image. It saves resumable private per-shard evidence and fails closed; no source deletion before all 165 shards / 82,481 images and all five recovery IDs pass. The local verifier passed seven meaningful synthetic checks before launch.
