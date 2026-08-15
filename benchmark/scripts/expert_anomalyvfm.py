"""
AnomalyVFM expert wrapper for the multi-tool agent.

Zero-shot anomaly detection using pre-trained VFM + LoRA adapters.
No reference images needed — works on single query image.
    (query_image_path) → (anomaly_score, anomaly_map)

Usage:
    python3 benchmark/scripts/expert_anomalyvfm.py \
        --manifest benchmark/manifests/full_manifest.json \
        --split calibration \
        --output benchmark/results/anomalyvfm_calibration.json \
        --checkpoint experts/AnomalyVFM/checkpoints/dinov2_model.pkl
"""
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from tqdm import tqdm

# Add AnomalyVFM to path — must be first in sys.path so 'models' resolves to AnomalyVFM's
AVFM_ROOT = Path(__file__).resolve().parent.parent.parent / "experts" / "AnomalyVFM"
if str(AVFM_ROOT) not in sys.path:
    sys.path.insert(0, str(AVFM_ROOT))
# Also need peft_local from the repo
PEFT_LOCAL = AVFM_ROOT / "peft_local"
if str(PEFT_LOCAL.parent) not in sys.path:
    sys.path.insert(0, str(PEFT_LOCAL.parent))

DEVICE = "cuda:2"  # use a different GPU than SubspaceAD
TOPK = 5


class AnomalyVFMTool:
    """Lazy-loaded AnomalyVFM zero-shot expert."""

    def __init__(self, checkpoint_path=None, device=DEVICE):
        self.checkpoint_path = checkpoint_path or str(AVFM_ROOT / "checkpoints" / "dinov2_model.pkl")
        self.device = device
        self._model = None
        self._decoder = None
        self._predictor = None
        self._transform = None
        self._feat_size = None
        self._smoother = None

    def _load(self):
        if self._model is not None:
            return
        try:
            from models.model import FeatureExtractor, BACKBONES
            from decoder import SimpleDecoder, SimplePredictor
            from peft_local.peft_wrapper import PeftType
        except ImportError as e:
            print(f"[AnomalyVFM] import error: {e}")
            print(f"[AnomalyVFM] sys.path[0:3] = {sys.path[:3]}")
            raise

        # DINOv2 backbone: feat_dim=1024, patch_size=14
        feat_dim = 1024
        image_size = 672
        patch_size = 14
        self._feat_size = image_size // patch_size  # 48

        fe = FeatureExtractor(BACKBONES.DINOV2, height=image_size)
        self._model = fe.model
        self._model.add_peft(r=64, peft_type="dora")
        # Match predict_single_image.py: num_up_layers=1, not upsample_blocks=2
        self._decoder = SimpleDecoder(feat_dim, 1, 1)
        self._predictor = SimplePredictor(feat_dim)

        state = torch.load(self.checkpoint_path, map_location="cpu")
        self._model.load_state_dict(state["model_state_dict"])
        self._decoder.load_state_dict(state["decoder_state_dict"])
        self._predictor.load_state_dict(state["predictor_state_dict"])

        self._model.eval().to(self.device)
        self._decoder.eval().to(self.device)
        self._predictor.eval().to(self.device)
        self._transform = self._model.get_img_transform()
        self._smoother = torch.nn.AvgPool2d(kernel_size=21, stride=1, padding=10)

        print(f"[AnomalyVFM] loaded DINOv2 checkpoint on {self.device}")

    def predict(self, query_path: str, topk: int = TOPK) -> dict:
        """Run zero-shot inference on a single image."""
        self._load()
        try:
            img = Image.open(query_path).convert("RGB")
            x = self._transform(img).unsqueeze(0).to(self.device)
        except Exception as e:
            return {"anomaly_score": 0.5, "top_patches": [], "error": str(e)}

        with torch.amp.autocast("cuda", dtype=torch.bfloat16):
            with torch.no_grad():
                summary, ftrs = self._model(x)
                ftrs = ftrs.permute(0, 2, 1).reshape(1, -1, self._feat_size, self._feat_size)
                mask, _ = self._decoder(ftrs)
                score = self._predictor(summary).squeeze().sigmoid()

        mask = self._smoother(mask)
        mask_np = mask.squeeze().cpu().float().numpy()
        score_val = float(score.cpu().float())

        # Top-k from the anomaly map
        flat = mask_np.flatten()
        top_idx = np.argsort(-flat)[:topk]
        h, w = mask_np.shape
        top_patches = []
        for rank, idx in enumerate(top_idx, 1):
            row = int(idx // w)
            col = int(idx % w)
            top_patches.append({
                "rank": rank,
                "score": float(flat[idx]),
                "row": row, "col": col,
                "region": _region_label(row, col, max(h, w)),
            })

        return {
            "anomaly_score": score_val,
            "top_patches": top_patches,
            "map_shape": [h, w],
            "error": None,
        }


def _region_label(row, col, grid):
    third = grid / 3.0
    vband = "upper" if row < third else ("lower" if row >= 2 * third else "middle")
    hband = "left" if col < third else ("right" if col >= 2 * third else "center")
    if vband == "middle" and hband == "center":
        return "center"
    return f"{vband}-{hband}" if hband != "center" else vband


def run_benchmark(manifest_path, split, output_path, checkpoint_path=None,
                  domains=None, device=DEVICE):
    with open(manifest_path) as f:
        items = json.load(f)
    items = [x for x in items
             if (split == "all" or x.get("split") == split)
             and (domains is None or x["domain_code"] in domains)]
    # v2: D8 is DermaMNIST (not Avenue surveillance), so no exclusion.

    tool = AnomalyVFMTool(checkpoint_path=checkpoint_path, device=device)
    results = []

    for item in tqdm(items, desc="AnomalyVFM"):
        r = tool.predict(item["query_path"])
        results.append({
            "item_id": item["item_id"],
            "domain": item.get("domain"),
            "domain_code": item["domain_code"],
            "label_gt": item["label"],
            "anomaly_score": r["anomaly_score"],
            "label_pred": 1 if r["anomaly_score"] >= 0.5 else 0,
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
    ap.add_argument("--checkpoint", default=None)
    ap.add_argument("--domains", nargs="*", default=None)
    ap.add_argument("--device", default=DEVICE)
    args = ap.parse_args()
    run_benchmark(args.manifest, args.split, args.output, args.checkpoint,
                  args.domains, args.device)
