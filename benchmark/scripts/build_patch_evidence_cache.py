"""
Build a DINOv2 patch-evidence cache used by EGRA components C1 and C3.

For each benchmark item we run a dense patch-level DINOv2 comparison of the
query image against its normal reference images and save the top-k most
anomalous patches together with coarse region labels (upper-left, center, ...)
into a JSON file keyed by item_id. infer.py's v3_grounded / v3_egra variants
then read this cache and inject the evidence as a short textual block into
the VLM prompt --- no numerical fusion, no training.

Unlike the coarse 2x2 DINOv2-PatchNN baseline in classical_baselines.py, this
script uses DINOv2's native 16x16 patch tokens (ViT-B/14 at 224x224) to get
256 patches per image and a proper top-k localisation.

Usage:
  python3 benchmark/scripts/build_patch_evidence_cache.py \
      --manifest benchmark/manifests/full_manifest.json \
      --split test \
      --output benchmark/results/patch_evidence_test.json \
      --topk 5

The output JSON is a dict keyed by item_id, each value containing:
  {
    "item_id": ...,
    "domain_code": ...,
    "patch_grid": [14, 14],
    "top_patches": [{"rank":1, "distance":0.42, "baseline":0.08,
                     "row":2, "col":3, "region":"upper-left"}, ...],
    "global_score": 0.38,       # mean top-10 patch distance
    "error": null
  }
"""

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from tqdm import tqdm

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# DINOv2 ViT-B/14: image 224x224 → 16x16 = 256 patch tokens
PATCH_IMG_SIZE = 224
PATCH_GRID = 16


def _region_label(row: int, col: int, grid: int = PATCH_GRID) -> str:
    """Map (row, col) in a [grid x grid] patch grid to a coarse 3x3 region label."""
    third = grid / 3.0
    vband = "upper" if row < third else ("lower" if row >= 2 * third else "middle")
    hband = "left" if col < third else ("right" if col >= 2 * third else "center")
    if vband == "middle" and hband == "center":
        return "center"
    return f"{vband}-{hband}" if hband != "center" else f"{vband}"


def load_dinov2():
    import torchvision.transforms as T
    model = torch.hub.load("facebookresearch/dinov2", "dinov2_vitb14",
                           source="github", force_reload=False)
    model.eval().to(DEVICE)
    transform = T.Compose([
        T.ToPILImage(),
        T.Resize(PATCH_IMG_SIZE),
        T.CenterCrop(PATCH_IMG_SIZE),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    return model, transform


def embed_patches(model, transform, path: str) -> torch.Tensor:
    """Return L2-normalised patch tokens: shape [256, 768]."""
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    x = transform(img).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        out = model.forward_features(x)
    # DINOv2 forward_features returns dict with 'x_norm_patchtokens' in new API
    if isinstance(out, dict) and "x_norm_patchtokens" in out:
        tokens = out["x_norm_patchtokens"].squeeze(0)  # [256, 768]
    elif isinstance(out, dict) and "x_prenorm" in out:
        tokens = out["x_prenorm"].squeeze(0)[1:]  # drop CLS
    else:
        # Fall back to generic hook
        tokens = out.squeeze(0) if out.dim() == 2 else out.squeeze(0)[1:]
    return F.normalize(tokens, dim=-1)


def patch_distance_map(q_tokens: torch.Tensor, ref_tokens_list) -> torch.Tensor:
    """
    For each query patch, compute the min cosine distance to ANY reference patch
    across all reference images. Returns a [256] distance tensor in [0, 2].
    """
    if not ref_tokens_list:
        return torch.zeros(q_tokens.shape[0], device=q_tokens.device)
    ref_cat = torch.cat(ref_tokens_list, dim=0)  # [n_ref * 256, 768]
    sim = q_tokens @ ref_cat.T                   # [256, n_ref*256]
    max_sim = sim.max(dim=1).values              # best match per query patch
    return 1.0 - max_sim                         # higher = more anomalous


def build_evidence_for_item(model, transform, item, topk: int = 5) -> dict:
    try:
        q = embed_patches(model, transform, item["query_path"])
        refs = [embed_patches(model, transform, p) for p in item["ref_paths"][:2]]
        if not refs:
            return {"item_id": item["item_id"], "error": "no_references"}
        dist = patch_distance_map(q, refs)  # [256]
        flat = dist.cpu().numpy()
        baseline = float(np.percentile(flat, 50))  # median as "normal" reference point
        top_idx = np.argsort(-flat)[:topk]
        top_patches = []
        for rank, idx in enumerate(top_idx, start=1):
            row = int(idx // PATCH_GRID)
            col = int(idx % PATCH_GRID)
            top_patches.append({
                "rank": rank,
                "distance": round(float(flat[idx]), 4),
                "baseline": round(baseline, 4),
                "row": row,
                "col": col,
                "region": _region_label(row, col),
            })
        global_score = float(np.sort(flat)[-10:].mean())
        return {
            "item_id": item["item_id"],
            "domain_code": item["domain_code"],
            "patch_grid": [PATCH_GRID, PATCH_GRID],
            "top_patches": top_patches,
            "global_score": round(global_score, 4),
            "baseline": round(baseline, 4),
            "error": None,
        }
    except Exception as e:
        return {"item_id": item["item_id"], "error": f"{type(e).__name__}: {e}"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--split", default="test",
                        choices=["calibration", "dev", "test", "all"])
    parser.add_argument("--output", required=True)
    parser.add_argument("--topk", type=int, default=5)
    parser.add_argument("--domains", nargs="*", default=None)
    args = parser.parse_args()

    with open(args.manifest) as f:
        all_items = json.load(f)
    items = [x for x in all_items
             if (args.split == "all" or x.get("split") == args.split)
             and (args.domains is None or x["domain_code"] in args.domains)]
    print(f"build_patch_evidence_cache: {len(items)} items, topk={args.topk}")

    model, transform = load_dinov2()

    # Cache already present → resume (skip existing item_ids)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cache: dict = {}
    if out_path.exists():
        try:
            cache = json.load(open(out_path))
            print(f"Resuming with {len(cache)} existing entries")
        except Exception:
            cache = {}

    for item in tqdm(items, desc="patch-evidence"):
        if item["item_id"] in cache and cache[item["item_id"]].get("error") is None:
            continue
        cache[item["item_id"]] = build_evidence_for_item(
            model, transform, item, topk=args.topk,
        )
        # periodic flush every 100 items
        if len(cache) % 100 == 0:
            json.dump(cache, open(out_path, "w"))

    json.dump(cache, open(out_path, "w"))
    n_ok = sum(1 for v in cache.values() if v.get("error") is None)
    n_err = len(cache) - n_ok
    print(f"Saved: {out_path}")
    print(f"OK: {n_ok}   errors: {n_err}")


if __name__ == "__main__":
    main()
