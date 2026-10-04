---
title: "Verify the Hugging Face transfer before cleaning up the archive copy"
status: done
area: data
due: null
updated: 2026-10-04
owner: agent
brief: "Verified 165 shards / 82,481 images; deleted 164,847 represented source objects, retained 135 excluded/unmatched/detail sidecars"
refs:
  - "docs/todo/done/data/hf-dataset-upload.md"
  - "scripts/hf_dataset/build_shards.py"
  - "https://huggingface.co/datasets/samfrench9/image-ocean2-sdxl-82k"
test: null
---

- **What:** Sam requested cleanup of the original archive copy after independent Hugging Face completeness/source mapping checks. Exact infrastructure scope and private inventories/journals are in the image-ocean2 section of `~/TODO.md`; do not publish those details in this public repo.
- **Verified dataset (2026-10-04):** public Hub revision `c2897656e413ca1dc6590dc434ba69bb870b73f5`, 172 files / 81,327,331,245 bytes. All 165 image shards / 81,323,516,544 bytes were downloaded anonymously at that immutable revision and matched declared size/LFS SHA256. All 82,481 unique images decoded with matching paths/dimensions; every ordered row and all 30 normalized recipe fields matched final metadata and original source metadata/scores. No missing, unexpected, duplicate or excluded IDs. Every source JSON matched its source inventory MD5/size. All five logged early `InvalidObjectState` downloads were later scored, included and independently downloaded/decoded from the Hub.
- **Cleanup result (2026-10-04 16:00:29 UTC):** deleted 164,847 represented source objects / 105,042,349,293 bytes. Fresh current-object and full-version listings show exactly 135 retained objects / 13,408,223 bytes, unchanged source identities, zero eligible versions and zero delete markers. Bucket versioning was absent throughout; no noncurrent versions existed. A separate live read at 16:01:48 UTC confirmed the same retained state and unchanged public Hub revision. Every deletion request was bounded to the authorized source scope and acknowledged in a durable journal.

| Retention reason | Objects | Bytes |
| --- | ---: | ---: |
| Deliberate NSFW exclusions | 14 | 8,995,102 |
| Deliberate manual exclusions | 4 | 3,160,102 |
| Unreadable/no-sidecar PNGs without a Hub row | 2 | 1,048,797 |
| Raw JSON preserving caption-renderer detail omitted from normalized metadata | 115 | 204,222 |
| Total | 135 | 13,408,223 |

- **Provider compatibility correction:** the first 1,000-target request combined an explicit null version ID and per-object ETag, and every entry returned `NotImplemented` with zero deletions. Dedicated stopped inventories exactly matched baseline; all error evidence was preserved. The corrected strictly unversioned request used current-object Key+ETag conditional deletes, matching AWS's documented format, after repeating complete live source/version/Hub checks. Conditional delete evaluations apply to current objects. No unconditional fallback or provider configuration change was used. Source versioning was checked before every batch; final retained identities/versions/markers were independently re-read. Request-combination incompatibility is inferred from the rejection and successful format correction; AWS did not identify the exact unsupported field.
- **Validation:** 165 full shard checks / 82,481 image decodes and source/metadata comparisons passed. Payload verifier passed seven offline synthetic checks; corrected cleanup verifier passed 20 offline guard/journal/compatibility checks and root review. Required TODO build/check and 30 tooling tests passed; docs commits were pushed, with CI checked at closeout. This operational data task has no application build/deploy lane. Concurrent unrelated generator/gallery/README/spec edits were preserved using an isolated docs worktree.
- **Billing:** possible Glacier minimum-duration early-deletion charge approximately US$0.08–0.09, an estimate rather than an invoice amount; the 90-day minimum had not fully elapsed. Zero Deep Archive objects, so no Deep Archive early-deletion charge. Audit API reads were under US$0.01 at published rates; delete requests are free. No new billable service and no Anthropic API.
- **Rebuild correction:** the included original source objects are removed. Use the verified Hub lossless WebP images plus recipes/retained local metadata for future rebuild work; the old full-archive restore/sync instructions cannot recover deleted included originals. Keep excluded/unmatched sources in place unless Sam gives new instructions. The known cached-shard reuse defect remains a separate follow-up in `docs/todo/data/validate-cached-shard-reuse.md`; every current Hub shard passed the dedicated content check.
- **Done when:** complete Hub verification, scoped confirmed deletion, exact retained count/size/reasons and absence of eligible versions/markers, and consistent global TODO/shared memory. All operational conditions passed; private evidence paths and the final record checks are in `~/TODO.md`.
