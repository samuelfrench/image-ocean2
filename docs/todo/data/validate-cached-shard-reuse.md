---
title: "Validate cached shard IDs before reusing a dataset rebuild"
status: next
area: data
due: null
updated: 2026-10-04
owner: agent
brief: "Reproducer: an existing one-row shard retains stale-id when the requested row is intended-new-id; verify IDs before reuse"
refs:
  - "scripts/hf_dataset/build_shards.py:134"
  - "docs/todo/done/data/verify-hf-copy-cleanup.md"
test: null
---

- **Measured defect (2026-10-04):** `scripts/hf_dataset/build_shards.py:134` returns an existing shard's row count without checking its IDs, recipe values or build inputs. A temporary 446-byte one-row shard with `id=stale-id` was accepted when `write_shard` requested `id=intended-new-id`; the stale ID remained. Reusing the same shard filenames after exclusions change can preserve old rows. This is a proven local reproducer; it does not establish a defect in the current Hub dataset, whose 165 immutable shards / 82,481 images all passed independent checksum, row, recipe and decode checks on 2026-10-04.
- **Reproduce:** from the repo root run the snippet below using the dataset build environment. It only creates and removes a temporary local fixture.

```python
import importlib.util, tempfile
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
spec = importlib.util.spec_from_file_location("builder", "scripts/hf_dataset/build_shards.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / "data").mkdir()
    path = root / "data/train-00000-of-00001.parquet"
    pq.write_table(pa.table({"id": ["stale-id"]}), path)
    builder.write_shard((0, 1, [{"id": "intended-new-id"}], str(root / "no-inputs"), str(root)))
    print(pq.read_table(path).column("id").to_pylist())  # observed: ['stale-id']
```

- **Next:** make cached reuse conditional on the intended ordered IDs and relevant build/recipe identity; rebuild stale shards. Preserve resumability for truly identical inputs. Check changing exclusions while the shard count remains constant.
- **Done when:** changed inputs cannot silently reuse stale rows, identical builds remain resumable, and focused verification demonstrates both outcomes. No Hub publication or source-copy cleanup belongs to this follow-up.
