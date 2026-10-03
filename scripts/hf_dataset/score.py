"""Score every image with the LAION aesthetic predictor and an NSFW classifier.

usage: python scripts/hf_dataset/score.py --png-dir DIR --out scores.parquet [--limit N]

Columns written: id, laion_aesthetic (LAION improved aesthetic predictor v2,
sac+logos+ava1-l14-linearMSE on normalized CLIP ViT-L/14 image embeddings),
nsfw_prob (Falconsai/nsfw_image_detection probability of the "nsfw" label).
Resumable: ids already in --out are skipped.
"""
from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

import pandas as pd
import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset
from transformers import AutoImageProcessor, AutoModelForImageClassification, CLIPImageProcessor, CLIPModel

AESTHETIC_URL = (
    "https://github.com/christophschuhmann/improved-aesthetic-predictor/raw/main/"
    "sac+logos+ava1-l14-linearMSE.pth"
)
CLIP_ID = "openai/clip-vit-large-patch14"
NSFW_ID = "Falconsai/nsfw_image_detection"


class AestheticMLP(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(768, 1024), nn.Dropout(0.2), nn.Linear(1024, 128), nn.Dropout(0.2),
            nn.Linear(128, 64), nn.Dropout(0.1), nn.Linear(64, 16), nn.Linear(16, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.layers(x)


class Images(Dataset):
    def __init__(self, paths: list[Path], clip_proc, nsfw_proc) -> None:
        self.paths, self.clip_proc, self.nsfw_proc = paths, clip_proc, nsfw_proc

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, i: int):
        p = self.paths[i]
        try:
            im = Image.open(p).convert("RGB")
        except Exception:
            return p.stem, None, None
        a = self.clip_proc(images=im, return_tensors="pt")["pixel_values"][0]
        b = self.nsfw_proc(images=im, return_tensors="pt")["pixel_values"][0]
        return p.stem, a, b


def collate(batch):
    ok = [x for x in batch if x[1] is not None]
    bad = [x[0] for x in batch if x[1] is None]
    if not ok:
        return [], None, None, bad
    ids, a, b = zip(*ok)
    return list(ids), torch.stack(a), torch.stack(b), bad


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--png-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--weights-dir", type=Path, default=Path.home() / ".cache" / "image-ocean2")
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    done = set(pd.read_parquet(args.out)["id"]) if args.out.exists() else set()
    paths = sorted(p for p in args.png_dir.glob("*.png") if p.stem not in done)
    if args.limit:
        paths = paths[: args.limit]
    print(f"{len(done)} already scored, {len(paths)} to score", flush=True)
    if not paths:
        return

    args.weights_dir.mkdir(parents=True, exist_ok=True)
    wpath = args.weights_dir / "sac+logos+ava1-l14-linearMSE.pth"
    if not wpath.exists():
        urllib.request.urlretrieve(AESTHETIC_URL, wpath)

    dev = "cuda"
    clip = CLIPModel.from_pretrained(CLIP_ID, torch_dtype=torch.float16).to(dev).eval()
    mlp = AestheticMLP()
    mlp.load_state_dict(torch.load(wpath, map_location="cpu"))
    mlp = mlp.to(dev).eval()
    nsfw = AutoModelForImageClassification.from_pretrained(NSFW_ID, torch_dtype=torch.float16).to(dev).eval()
    nsfw_idx = {v: k for k, v in nsfw.config.id2label.items()}["nsfw"]

    ds = Images(paths, CLIPImageProcessor.from_pretrained(CLIP_ID), AutoImageProcessor.from_pretrained(NSFW_ID))
    dl = DataLoader(ds, batch_size=args.batch_size, num_workers=args.workers, collate_fn=collate)
    rows, unreadable = [], []
    with torch.inference_mode():
        for n, (ids, a, b, bad) in enumerate(dl, 1):
            unreadable += bad
            if not ids:
                continue
            emb = clip.get_image_features(pixel_values=a.to(dev, torch.float16))
            if not torch.is_tensor(emb):  # transformers 5 returns an output object; pooler_output = projected embeds
                emb = emb.pooler_output
            emb = emb.float()
            assert emb.shape[-1] == 768, emb.shape
            emb = emb / emb.norm(dim=-1, keepdim=True)
            aes = mlp(emb).squeeze(-1).cpu().tolist()
            prob = nsfw(pixel_values=b.to(dev, torch.float16)).logits.float().softmax(-1)[:, nsfw_idx].cpu().tolist()
            rows += [{"id": i, "laion_aesthetic": round(x, 4), "nsfw_prob": round(y, 5)} for i, x, y in zip(ids, aes, prob)]
            if n % 100 == 0:
                print(f"{len(rows)}/{len(paths)} scored", flush=True)
    out = pd.DataFrame(rows)
    if done:
        out = pd.concat([pd.read_parquet(args.out), out], ignore_index=True)
    out.to_parquet(args.out, index=False)
    print(f"wrote {len(out)} rows to {args.out}; unreadable: {unreadable}", flush=True)


if __name__ == "__main__":
    main()
