"""
SubspaceAD expert wrapper for the multi-tool agent.

Training-free few-shot anomaly detection via DINOv2 + PCA subspace modeling.
Wraps the SubspaceAD repo as a callable tool:
    (query_image_path, ref_image_paths[]) → (anomaly_score, top_patches[])

Usage:
    python3 benchmark/scripts/expert_subspacead.py \
        --manifest benchmark/manifests/full_manifest.json \
        --split calibration \
        --output benchmark/results/subspacead_calibration.json
"""
import argparse
import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from tqdm import tqdm

# Add SubspaceAD to path
SUBSPACEAD_ROOT = Path(__file__).resolve().parent.parent.parent / "experts" / "SubspaceAD"
sys.path.insert(0, str(SUBSPACEAD_ROOT / "src"))

DEVICE = "cuda:0"
MODEL_CKPT = "facebook/dinov2-with-registers-giant"
IMAGE_RES = 672
LAYERS = [-12, -13, -14, -15, -16, -17, -18]
AGG_METHOD = "mean"
PCA_EV = 0.99  # explained variance ratio for PCA
SCORING_METHOD = "reconstruction"
TOPK = 5


class SubspaceADTool:
    """Lazy-loaded SubspaceAD expert."""

    def __init__(self, device=DEVICE, model_ckpt=MODEL_CKPT):
        self.device = device
        self.model_ckpt = model_ckpt
        self._extractor = None

    def _load(self):
        if self._extractor is not None:
            return
        # SubspaceAD's FeatureExtractor uses a module-level DEVICE variable
        import subspacead.core.extractor as ext_mod
        ext_mod.DEVICE = torch.device(self.device)
        from subspacead.core.extractor import FeatureExtractor
        self._extractor = FeatureExtractor(model_ckpt=self.model_ckpt)
        print(f"[SubspaceAD] loaded {self.model_ckpt} on {self.device}")

    def _extract_tokens(self, pil_img):
        """Extract fused patch tokens for a single PIL image. Returns torch tensor."""
        fused, (hp, wp), sal = self._extractor.extract_tokens(
            [pil_img],
            res=IMAGE_RES,
            layers=LAYERS,
            agg_method=AGG_METHOD,
            docrop=False,
            use_clahe=False,
            dino_saliency_layer=0,
        )
        # fused can be numpy or torch; normalize to torch on self.device
        if isinstance(fused, np.ndarray):
            fused = torch.from_numpy(fused).to(self.device)
        tokens = fused.squeeze(0)  # remove batch dim
        if tokens.dim() == 3:  # (hp, wp, D) -> (hp*wp, D)
            tokens = tokens.reshape(-1, tokens.shape[-1])
        elif tokens.dim() == 1:  # edge case: single token
            tokens = tokens.unsqueeze(0)
        return tokens, (hp, wp)

    def predict(self, query_path: str, ref_paths: list, topk: int = TOPK) -> dict:
        """
        Run SubspaceAD on a single (query, refs) pair.
        Returns dict with anomaly_score, top_patches[], grid_size.
        """
        self._load()
        from subspacead.core.pca import PCAModel
        from subspacead.post_process.scoring import calculate_anomaly_scores

        # 1. Extract ref features
        ref_tokens_list = []
        for rp in ref_paths[:4]:  # limit to 4 refs for speed
            try:
                img = Image.open(rp).convert("RGB")
                tokens, _ = self._extract_tokens(img)
                ref_tokens_list.append(tokens)
            except Exception as e:
                print(f"[SubspaceAD] ref load error {rp}: {e}")
                continue

        if not ref_tokens_list:
            return {"anomaly_score": 0.5, "top_patches": [], "error": "no_refs"}

        all_ref = torch.cat(ref_tokens_list, dim=0)  # (N, D)

        # 2. Fit PCA — SubspaceAD PCA expects numpy from the generator, not torch
        pca_model = PCAModel(k=None, ev=PCA_EV)
        all_ref_np = all_ref.cpu().numpy() if isinstance(all_ref, torch.Tensor) else all_ref
        def feat_gen_factory():
            def gen():
                yield all_ref_np
            return gen()
        pca_params = pca_model.fit(
            feature_generator=feat_gen_factory,
            feature_dim=all_ref_np.shape[-1],
            total_tokens=all_ref_np.shape[0],
            num_batches=1,
        )

        # 3. Extract query features
        try:
            q_img = Image.open(query_path).convert("RGB")
            q_tokens, (hp, wp) = self._extract_tokens(q_img)
        except Exception as e:
            return {"anomaly_score": 0.5, "top_patches": [], "error": str(e)}

        # 4. Score — calculate_anomaly_scores expects numpy
        q_np = q_tokens.cpu().numpy() if isinstance(q_tokens, torch.Tensor) else q_tokens
        scores_np = calculate_anomaly_scores(
            q_np, pca_params,
            method=SCORING_METHOD,
            drop_k=0,
        )  # (hp*wp,) numpy
        scores_np = np.asarray(scores_np, dtype=np.float64)

        # 5. Image-level score (top-1% mean)
        k_top = max(1, int(len(scores_np) * 0.01))
        image_score = float(np.sort(scores_np)[-k_top:].mean())

        # Normalize to [0, 1] using sigmoid-like scaling
        # SubspaceAD raw scores can be very large; calibrate later
        # For now just report raw + a normalized version
        norm_score = float(1.0 / (1.0 + np.exp(-0.1 * (image_score - np.median(scores_np)))))

        # 6. Top-k patches
        top_idx = np.argsort(-scores_np)[:topk]
        top_patches = []
        for rank, idx in enumerate(top_idx, 1):
            row = int(idx // wp)
            col = int(idx % wp)
            top_patches.append({
                "rank": rank,
                "score": float(scores_np[idx]),
                "row": row, "col": col,
                "region": _region_label(row, col, max(hp, wp)),
            })

        return {
            "anomaly_score": image_score,
            "anomaly_score_norm": norm_score,
            "top_patches": top_patches,
            "grid_size": [int(hp), int(wp)],
            "error": None,
        }


def _region_label(row, col, grid):
    third = grid / 3.0
    vband = "upper" if row < third else ("lower" if row >= 2 * third else "middle")
    hband = "left" if col < third else ("right" if col >= 2 * third else "center")
    if vband == "middle" and hband == "center":
        return "center"
    return f"{vband}-{hband}" if hband != "center" else vband


def run_benchmark(manifest_path, split, output_path, domains=None, device=DEVICE):
    """Run SubspaceAD on a benchmark split."""
    with open(manifest_path) as f:
        items = json.load(f)
    items = [x for x in items
             if (split == "all" or x.get("split") == split)
             and (domains is None or x["domain_code"] in domains)]
    # v2: D8 is DermaMNIST (not Avenue surveillance), so no exclusion.

    tool = SubspaceADTool(device=device)
    results = []

    for item in tqdm(items, desc="SubspaceAD"):
        r = tool.predict(item["query_path"], item["ref_paths"])
        results.append({
            "item_id": item["item_id"],
            "domain": item.get("domain"),
            "domain_code": item["domain_code"],
            "label_gt": item["label"],
            "anomaly_score": r["anomaly_score"],
            "anomaly_score_norm": r.get("anomaly_score_norm", 0.5),
            "label_pred": 1 if r.get("anomaly_score_norm", 0.5) >= 0.5 else 0,
            "top_patches": r.get("top_patches", []),
            "error": r.get("error"),
            "split": item.get("split"),
        })

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    n_ok = sum(1 for x in results if not x.get("error"))
    print(f"Saved {output_path}: {n_ok}/{len(results)} ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", default="calibration")
    ap.add_argument("--output", required=True)
    ap.add_argument("--domains", nargs="*", default=None)
    ap.add_argument("--device", default=DEVICE)
    args = ap.parse_args()
    run_benchmark(args.manifest, args.split, args.output, args.domains, args.device)
