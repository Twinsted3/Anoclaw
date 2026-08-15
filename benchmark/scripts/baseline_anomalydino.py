"""
AnomalyDINO baseline runner over manifests_v2 test split.

Wraps the official AnomalyDINO (Damm et al., WACV 2025) DINOv2 + faiss
patch-NN pipeline so each manifest item builds its own few-shot memory
bank from `ref_paths` and scores `query_path` via mean(top-1%) of
patch-level 1-NN L2-normalized distances.

Defaults match the paper's "agnostic" preset: PCA foreground masking +
rotation augmentation on refs, DINOv2 ViT-B/14, 448px shorter edge.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import cv2
import faiss
import numpy as np
import torch
from tqdm import tqdm

ANOMDINO = Path(__file__).resolve().parent.parent.parent / "experts" / "AnomalyDINO"
sys.path.insert(0, str(ANOMDINO))
from src.backbones import get_model  # noqa: E402
from src.utils import augment_image  # noqa: E402
from src.post_eval import mean_top1p  # noqa: E402


def score_item(model, query_path, ref_paths, knn_neighbors, masking, rotation,
               max_refs, faiss_on_cpu):
    """Build a memory bank from refs and score the query (mean-top1% patch L2)."""
    features_ref = []
    refs = ref_paths[:max_refs] if max_refs > 0 else ref_paths
    with torch.inference_mode():
        for rp in refs:
            img_ref = cv2.cvtColor(cv2.imread(rp, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
            augs = augment_image(img_ref) if rotation else [img_ref]
            for aug in augs:
                tens, gs = model.prepare_image(aug)
                f = model.extract_features(tens)
                m = model.compute_background_mask(f, gs, threshold=10, masking_type=masking)
                features_ref.append(f[m])
        feats = np.concatenate(features_ref, axis=0).astype("float32")
        if faiss_on_cpu:
            knn = faiss.IndexFlatL2(feats.shape[1])
        else:
            res = faiss.StandardGpuResources()
            knn = faiss.GpuIndexFlatL2(res, feats.shape[1])
        faiss.normalize_L2(feats)
        knn.add(feats)

        img_q = cv2.cvtColor(cv2.imread(query_path, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        tq, gq = model.prepare_image(img_q)
        fq = model.extract_features(tq)
        mq = model.compute_background_mask(fq, gq, threshold=10, masking_type=masking) if masking else np.ones(fq.shape[0], dtype=bool)
        fq_keep = fq[mq].astype("float32")
        faiss.normalize_L2(fq_keep)
        d, _ = knn.search(fq_keep, k=knn_neighbors)
        if knn_neighbors > 1:
            d = d.mean(axis=1)
        d = (d / 2).squeeze()  # L2-normalized → cosine distance scale
        score = float(mean_top1p(d.flatten()))
    return score


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--output", required=True)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--model_name", default="dinov2_vitb14")
    ap.add_argument("--smaller_edge_size", type=int, default=448)
    ap.add_argument("--max_refs", type=int, default=4, help="few-shot k; 0=use all refs")
    ap.add_argument("--knn_neighbors", type=int, default=1)
    ap.add_argument("--masking", action="store_true", default=True)
    ap.add_argument("--no_masking", dest="masking", action="store_false")
    ap.add_argument("--rotation", action="store_true", default=True)
    ap.add_argument("--no_rotation", dest="rotation", action="store_false")
    ap.add_argument("--faiss_on_cpu", action="store_true")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    items = json.load(open(args.manifest))
    if args.split:
        items = [x for x in items if x.get("split") == args.split]

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = {}
    if args.resume and out_path.exists():
        try:
            done = {r["item_id"]: r for r in json.load(open(out_path))}
            print(f"[resume] {len(done)} already done")
        except Exception:
            done = {}

    print(f"Loading {args.model_name} on {args.device} (edge={args.smaller_edge_size}) ...")
    model = get_model(args.model_name, args.device, smaller_edge_size=args.smaller_edge_size)

    results = list(done.values())
    pending = [it for it in items if it["item_id"] not in done]
    print(f"Manifest items={len(items)}, pending={len(pending)}, mask={args.masking}, rot={args.rotation}, k={args.max_refs}")

    t0 = time.time()
    for it in tqdm(pending, desc="AnomalyDINO"):
        try:
            s = score_item(
                model, it["query_path"], it["ref_paths"],
                args.knn_neighbors, args.masking, args.rotation,
                args.max_refs, args.faiss_on_cpu,
            )
            results.append({
                "item_id": it["item_id"],
                "domain_code": it.get("domain_code"),
                "split": it.get("split"),
                "label": it.get("label"),
                "anomaly_score": s,
                "label_pred": int(s > 0.5),
                "error": None,
            })
        except Exception as e:
            results.append({
                "item_id": it["item_id"],
                "domain_code": it.get("domain_code"),
                "split": it.get("split"),
                "label": it.get("label"),
                "anomaly_score": None,
                "label_pred": None,
                "error": f"{type(e).__name__}: {e}",
            })

        if len(results) % 50 == 0:
            json.dump(results, open(out_path, "w"))

    json.dump(results, open(out_path, "w"))
    print(f"[done] wrote {len(results)} items in {time.time()-t0:.1f}s -> {out_path}")


if __name__ == "__main__":
    main()
