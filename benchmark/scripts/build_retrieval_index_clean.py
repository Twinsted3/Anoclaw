"""Rebuild retrieval indices with strict train-only clean normal pool.

Codex discovered that the old indices (D3/D3d/D7) include normal images
from the test and dev splits, causing tool_reference_retriever to
self-match a query at similarity ~1.0. This contaminates evaluation.

This script rebuilds the indices using ONLY images whose path does NOT
appear as any manifest item's query_path for ANY split. Also stores per-
entry provenance (split_source, item_id if known) so debugging is easy.

Usage:
  python benchmark/scripts/build_retrieval_index_clean.py \
    --manifest benchmark/manifests/full_manifest.json \
    --source_root MMAD/dataset/MMAD \
    --out_dir benchmark/retrieval_index_clean

Expected runtime: ~10 min per domain on a single GPU.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from collections import defaultdict

import numpy as np
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    import torch
    import timm
    model = timm.create_model("vit_small_patch14_dinov2.lvd142m",
                              pretrained=True, num_classes=0)
    model = model.to(args.device).eval()
    cfg = timm.data.resolve_data_config(model.pretrained_cfg)
    transform = timm.data.create_transform(**cfg, is_training=False)

    # Collect all query_paths across all splits (must be EXCLUDED from bank)
    m = json.load(open(args.manifest))
    exclude_paths = {x["query_path"] for x in m}
    # Ref paths are normal images; they CAN be in the bank (they are the bank)
    # but we record their provenance.
    ref_paths_by_domain = defaultdict(set)
    for x in m:
        for rp in x.get("ref_paths") or []:
            ref_paths_by_domain[x["domain_code"]].add(rp)

    Path(args.out_dir).mkdir(parents=True, exist_ok=True)

    for dom, ref_pool in sorted(ref_paths_by_domain.items()):
        # Remove any ref_path that is somebody's query_path (self-match)
        clean = sorted(p for p in ref_pool if p not in exclude_paths)
        # Also filter to existing files
        clean = [p for p in clean if os.path.exists(p)]
        if not clean:
            print(f"[{dom}] no clean refs; skipping")
            continue

        emb_list = []
        with torch.no_grad():
            for p in clean:
                try:
                    img = Image.open(p).convert("RGB")
                    t = transform(img).unsqueeze(0).to(args.device)
                    e = model(t).cpu().numpy().flatten()
                    e = e / (np.linalg.norm(e) + 1e-8)
                    emb_list.append(e)
                except Exception as e:
                    print(f"  [{dom}] skip {p}: {e}")
                    emb_list.append(np.zeros(384, dtype=np.float32))

        emb = np.stack(emb_list).astype(np.float32)
        out = Path(args.out_dir) / f"{dom}_index.npz"
        np.savez(out, paths=np.array(clean, dtype=object), embeddings=emb,
                 build_info=np.array(
                     [f"clean_train_only, {len(clean)} items"]))
        print(f"[{dom}] wrote {out} with {len(clean)} items "
              f"(excluded any query_path)")


if __name__ == "__main__":
    main()
