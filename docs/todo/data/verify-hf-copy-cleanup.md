---
title: "Verify the Hugging Face transfer before cleaning up the archive copy"
status: now
area: data
due: null
updated: 2026-10-04
owner: agent
brief: "Verify all 165 image shards and source mappings; delete only confirmed copies and retain every excluded or unmatched object"
refs:
  - "docs/todo/done/data/hf-dataset-upload.md"
  - "scripts/hf_dataset/build_shards.py"
  - "https://huggingface.co/datasets/samfrench9/image-ocean2-sdxl-82k"
test: null
---

- **What:** Sam requested cleanup of the original archive copy after independently verifying the Hugging Face dataset. Exact infrastructure scope, evidence paths and private inventories live in the image-ocean2 section of `~/TODO.md`; they must not be committed to this public repo.
- **State (2026-10-04):** verification started; no archive object deleted. Current Hub revision `c2897656e413ca1dc6590dc434ba69bb870b73f5` is public, has 172 files / 81,327,331,245 bytes and 165 image shards. The earlier private upload log reports 43 more bytes before subsequent card edits. Expected final row count from the pipeline is 82,481; independently reading all shards remains pending.
- **Next:** verify every shard is present and readable; compare its rows with final metadata and the source inventory; reconcile all early failed downloads. Stop before deletion on any real transfer gap. Delete only source objects represented on the Hub, preserving deliberate exclusions and anything unmatched; handle versions and delete markers if present. Record measured retained/deleted counts and sizes and archive minimum-duration billing effects in the private operational record.
- **Done when:** verification passes, scoped deletion is confirmed by a fresh inventory, retained exclusions/unmatched objects are counted with reasons, and the global TODO/shared memory agree with current evidence.
