---
title: "Verify the Hugging Face transfer before cleaning up the archive copy"
status: now
area: data
due: null
updated: 2026-10-04
owner: agent
brief: "Source mappings and 82,481 metadata rows verified; Full transfer verified; corrected cleanup has confirmed 100,000 / 164,847 object deletions, final retained verification pending"
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

- **Mid-run checkpoint (2026-10-04T15:22:47.049863+00:00):** 88 shards / 44,000 decoded images / 44,713,344,546 bytes passed; all five previously failed source images were independently downloaded and decoded from the Hub. Zero errors; no source deletion.

- **Payload gate PASSED (2026-10-04):** all 165 shards / 81,323,516,544 bytes downloaded at the immutable Hub revision and matched declared size/LFS SHA256; all 82,481 unique images decoded with matching dimensions/path and every ordered recipe row matched all 30 metadata fields. All five logged failed downloads independently decoded on the Hub. No missing/unexpected/duplicate image IDs and no excluded image IDs present. The local cleanup plan maps every source object, retains 135 objects / 13,408,223 bytes, and permits deletion of 164,847 verified represented objects / 105,042,349,293 bytes only after a fresh live source/Hub comparison. Cleanup verifier passed 13 offline guard/response/journal checks and root review; no deletion at this checkpoint.

- **Provider gate failure (2026-10-04):** fresh whole-prefix current/version snapshots and unchanged Hub identity passed. The first 1,000-object conditional delete request combined an explicit null version ID with an ETag and returned `NotImplemented` for every entry, with zero deleted entries. Dedicated stopped inventories match every original object identity, count and byte total; no source mutation occurred. Preserve the failed request/response evidence. Adjust the request format for the strictly unversioned source bucket, retaining conditional content checks, and rerun all live preflight/final-retained gates. This is an API-format rejection, not a transfer gap.

- **Request correction reviewed (2026-10-04):** the strictly unversioned source uses current-object Key+ETag conditional requests without a version-ID field, matching the AWS documented request format. Original null-version rejection and unchanged inventories remain preserved; a separate compatibility gate requires all 1,000 errors/zero deletions and exact unchanged stopped inventories. Compile, 20 offline mock guard checks and root review passed. Full source/Hub/payload/versioning/retained gates remain required before/after cleanup; no unconditional deletion fallback or provider settings change.

- **Deletion checkpoint (2026-10-04):** corrected current-object ETag requests accepted after fresh full source/version/Hub preflight; 100,000 objects / 65,495,082,760 bytes durably confirmed deleted at this checkpoint. The retained manifest is excluded from all batches. Final exact retained identities/count/size and absence of eligible versions/delete markers remain pending.
