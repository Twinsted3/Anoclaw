"""
PatchCore-style few-shot anomaly detection expert using DINOv2 patch tokens.

For each query image:
1. Extract multi-scale patch tokens from DINOv2
2. For each patch token, find nearest neighbor in the reference memory bank
3. Anomaly score = aggregation of patch-level distances

This provides dense, localization-aware anomaly scoring that complements
the VLM's semantic reasoning.
"""

import os
import numpy as np
import torch
import torch.nn.functional as F
from pathlib import Path
from typing import Dict, List, Optional, Tuple


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ─── Model loading ─────────────────────────────────────────────────────────────

_model_cache = {}


def _load_model(device=DEVICE):
    if "model" in _model_cache:
        return _model_cache["model"], _model_cache["transform"]
    import timm
    model = timm.create_model("vit_small_patch14_dinov2.lvd142m", pretrained=True, num_classes=0)
    model = model.to(device).eval()
    data_cfg = timm.data.resolve_data_config(model.pretrained_cfg)
    transform = timm.data.create_transform(**data_cfg, is_training=False)
    _model_cache["model"] = model
    _model_cache["transform"] = transform
    return model, transform


# ─── Feature extraction ────────────────────────────────────────────────────────

def _extract_patch_features(model, transform, image_path: str,
                            device=DEVICE) -> np.ndarray:
    """Extract DINOv2 patch tokens from an image using the model's native transform.

    Returns: [N_patches, D] normalized feature array (37x37=1369 patches for 518px).
    """
    from PIL import Image
    img = Image.open(image_path).convert("RGB")
    tensor = transform(img).unsqueeze(0).to(device)

    with torch.no_grad():
        features = model.forward_features(tensor)
        # features: [1, 1+N_patches, D], first token is CLS
        patch_tokens = features[:, 1:, :]  # [1, N_patches, D]
        patch_tokens = F.normalize(patch_tokens, dim=-1)

    return patch_tokens.squeeze(0).cpu().numpy()  # [N_patches, D]


def _extract_global_feature(model, transform, image_path: str,
                            device=DEVICE) -> np.ndarray:
    """Extract CLS token (global feature) from DINOv2."""
    from PIL import Image
    img = Image.open(image_path).convert("RGB")
    tensor = transform(img).unsqueeze(0).to(device)
    with torch.no_grad():
        features = model.forward_features(tensor)
        cls_token = features[:, 0, :]  # [1, D]
        cls_token = F.normalize(cls_token, dim=-1)
    return cls_token.squeeze(0).cpu().numpy()


# ─── Patch memory bank ──────────────────────────────────────────────────────────

_patch_bank_cache = {}


def _build_patch_bank(model, transform, ref_paths: List[str],
                      max_refs: int = 8, device=DEVICE) -> np.ndarray:
    """Build a patch memory bank from reference images.

    Returns: [N_total_ref_patches, D] normalized feature array.
    """
    key = tuple(sorted(ref_paths[:max_refs]))
    if key in _patch_bank_cache:
        return _patch_bank_cache[key]

    all_patches = []
    for path in ref_paths[:max_refs]:
        if not os.path.exists(path):
            continue
        try:
            patches = _extract_patch_features(model, transform, path, device=device)
            all_patches.append(patches)
        except Exception:
            continue

    if not all_patches:
        return np.zeros((0, 384))

    bank = np.concatenate(all_patches, axis=0)

    # Subsample if bank is too large (>20k patches) for speed
    if bank.shape[0] > 20000:
        rng = np.random.default_rng(42)
        idx = rng.choice(bank.shape[0], 20000, replace=False)
        bank = bank[idx]

    _patch_bank_cache[key] = bank
    return bank


# ─── PatchCore-style scoring ────────────────────────────────────────────────────

def patch_expert_score(query_path: str, ref_paths: List[str],
                       max_refs: int = 8, top_fraction: float = 0.01,
                       device=DEVICE) -> Dict:
    """Compute PatchCore-style anomaly score.

    For each query patch, find its nearest neighbor in the reference bank.
    Anomaly score = mean of top-k% worst-matching patch distances.

    Returns:
        anomaly_score: float 0-1 (higher = more anomalous)
        patch_distances: sorted top distances for interpretability
        global_similarity: CLS-token similarity for calibration
        n_ref_patches: size of reference bank
        interpretation: text description
    """
    model, transform = _load_model(device)

    # Build reference patch bank
    bank = _build_patch_bank(model, transform, ref_paths, max_refs, device)
    if bank.shape[0] == 0:
        return {"anomaly_score": 0.5, "confidence": "low", "reason": "empty reference bank"}

    # Extract query patches
    query_patches = _extract_patch_features(model, transform, query_path, device=device)

    # Compute pairwise distances (cosine distance = 1 - cosine_similarity)
    # query_patches: [Nq, D], bank: [Nr, D]
    # Do in batches to avoid OOM
    batch_size = 512
    min_dists = []
    for i in range(0, query_patches.shape[0], batch_size):
        q_batch = query_patches[i:i+batch_size]
        sims = q_batch @ bank.T  # [batch, Nr]
        batch_min_dist = 1.0 - sims.max(axis=1)  # cosine distance to nearest ref patch
        min_dists.append(batch_min_dist)

    min_dists = np.concatenate(min_dists)

    # Anomaly score: mean of top-k% worst-matching patches
    n_top = max(1, int(len(min_dists) * top_fraction))
    top_dists = np.sort(min_dists)[::-1][:n_top]
    anomaly_score_raw = float(np.mean(top_dists))

    # Also compute global similarity
    global_feat = _extract_global_feature(model, transform, query_path, device)
    global_bank = []
    for path in ref_paths[:max_refs]:
        if os.path.exists(path):
            try:
                gf = _extract_global_feature(model, transform, path, device)
                global_bank.append(gf)
            except:
                pass
    if global_bank:
        global_bank = np.stack(global_bank)
        global_sim = float((global_feat @ global_bank.T).max())
    else:
        global_sim = 0.5

    # Calibrate: use sigmoid mapping for better score distribution
    # These thresholds are empirically tuned
    # Normal images typically have anomaly_score_raw < 0.15
    # Anomalous images typically have anomaly_score_raw > 0.20
    import math
    calibrated = 1.0 / (1.0 + math.exp(-20 * (anomaly_score_raw - 0.18)))

    # Interpretation
    if calibrated > 0.8:
        interpretation = "strong anomaly signal — multiple patches deviate significantly from normal"
        confidence = "high"
    elif calibrated > 0.6:
        interpretation = "moderate anomaly signal — some patches deviate from normal"
        confidence = "medium"
    elif calibrated > 0.4:
        interpretation = "ambiguous — borderline similarity to normal bank"
        confidence = "low"
    elif calibrated > 0.2:
        interpretation = "mostly normal — minor deviations within expected range"
        confidence = "medium"
    else:
        interpretation = "very similar to normal — no significant patch deviations"
        confidence = "high"

    return {
        "anomaly_score": round(float(calibrated), 4),
        "raw_patch_distance": round(float(anomaly_score_raw), 4),
        "global_similarity": round(float(global_sim), 4),
        "top_patch_distances": [round(float(d), 4) for d in top_dists[:5]],
        "n_query_patches": int(len(min_dists)),
        "n_ref_patches": int(bank.shape[0]),
        "interpretation": interpretation,
        "confidence": confidence,
    }


# ─── Batch evaluation ──────────────────────────────────────────────────────────

def evaluate_standalone(manifest_path: str, split: str = "test",
                        domains: Optional[List[str]] = None,
                        output_path: Optional[str] = None):
    """Run patch expert as standalone baseline on the benchmark."""
    import json
    from tqdm import tqdm

    with open(manifest_path) as f:
        items = json.load(f)

    items = [x for x in items
             if (split == "all" or x["split"] == split)
             and (domains is None or x["domain_code"] in domains)]

    print(f"PatchCore expert: {len(items)} items")

    # Pre-load model
    _load_model()

    results = []
    for item in tqdm(items, desc="PatchExpert"):
        try:
            result = patch_expert_score(
                item["query_path"],
                item["ref_paths"][:8],
            )
            pred = 1 if result["anomaly_score"] > 0.5 else 0
            results.append({
                "item_id": item["item_id"],
                "domain": item["domain"],
                "domain_code": item["domain_code"],
                "label_gt": item["label"],
                "split": item["split"],
                "label_pred": pred,
                "anomaly_score": result["anomaly_score"],
                "raw_output": result,
                "cost_tokens": {"input": 0, "output": 0},
                "latency_sec": 0.0,
                "error": None,
            })
        except Exception as e:
            results.append({
                "item_id": item["item_id"],
                "domain": item["domain"],
                "domain_code": item["domain_code"],
                "label_gt": item["label"],
                "split": item["split"],
                "label_pred": 0,
                "anomaly_score": 0.5,
                "raw_output": None,
                "cost_tokens": {"input": 0, "output": 0},
                "latency_sec": 0.0,
                "error": str(e),
            })

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Saved: {output_path}")

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="/hdd1/jiangxi/AD-Agent/benchmark/manifests/full_manifest.json")
    parser.add_argument("--split", default="test")
    parser.add_argument("--domains", nargs="*", default=None)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    evaluate_standalone(args.manifest, args.split, args.domains, args.output)
