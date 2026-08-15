"""
VisualAD baseline runner over manifests_v2 test split.

Wraps the official VisualAD (Hou et al., arXiv 2603.07952) inference
pipeline. VisualAD is *zero-shot*: it uses two learned tokens
(anomaly_token, normal_token) on top of a frozen CLIP ViT-L/14@336px,
plus per-layer feature MLPs and a spatial cross-attention block. It
does not consume the few-shot reference images; it scores a single
query image and reduces a pixel-level anomaly map to an image-level
score via top-k pooling (default top-1%, paper setting).

Default checkpoint: weight/train_on_mvtec/CLIP.pth (industrial-trained,
the cleanest published one). The visa-trained checkpoint is used in the
ablation.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from scipy.ndimage import gaussian_filter
from tqdm import tqdm

VAD_ROOT = Path(__file__).resolve().parent.parent.parent / "experts" / "VisualAD"
sys.path.insert(0, str(VAD_ROOT))

import VisualAD_lib  # noqa: E402
from utils.transforms import get_transform  # noqa: E402
from utils.feature_transform import create_feature_transform  # noqa: E402
from utils.spatial_cross_attention import build_layer_adaptive_cross_attention  # noqa: E402
from utils.anomaly_detection import generate_anomaly_map_from_tokens  # noqa: E402
from utils.scoring import reduce_anomaly_map  # noqa: E402


class _Args:
    pass


def load_visualad(checkpoint_path, device):
    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
    args = _Args()
    args.backbone = ckpt.get("backbone", "ViT-L/14@336px")
    args.image_size = ckpt.get("image_size", 518)
    args.features_list = ckpt.get("features_list", [6, 12, 18, 24])

    preprocess, _ = get_transform(args)

    model, _ = VisualAD_lib.load(args.backbone, device=device)
    model.eval().to(device)
    feature_dim = model.visual.embed_dim

    model.visual.anomaly_token.data = ckpt["anomaly_token"].to(device)
    model.visual.normal_token.data = ckpt["normal_token"].to(device)

    layer_transforms = nn.ModuleDict()
    if "layer_transforms" in ckpt:
        for layer_name, sd in ckpt["layer_transforms"].items():
            hidden = sd["mlp.0.weight"].shape[0]
            layer_transforms[layer_name] = create_feature_transform(
                transform_type="mlp",
                input_dim=feature_dim,
                hidden_dim=hidden,
                output_dim=feature_dim,
                dropout=0.0,
            ).to(device)
            layer_transforms[layer_name].load_state_dict(sd)
            layer_transforms[layer_name].eval()

    cross_attn = None
    if "cross_attn" in ckpt:
        cfg = ckpt.get("cross_attn_config", {})
        cross_attn = build_layer_adaptive_cross_attention(
            layers=args.features_list,
            embed_dim=feature_dim,
            num_anchors=cfg.get("num_anchors", 4),
            dropout=cfg.get("dropout", 0.1),
            res_scale_init=cfg.get("res_scale_init", 0.01),
        ).to(device)
        cross_attn.load_state_dict(ckpt["cross_attn"])
        cross_attn.eval()

    return model, preprocess, args.features_list, args.image_size, layer_transforms, cross_attn


def score_item(model, preprocess, features_list, image_size, layer_transforms,
               cross_attn, query_path, device, sigma=4):
    img = Image.open(query_path).convert("RGB")
    x = preprocess(img).unsqueeze(0).to(device)

    with torch.no_grad():
        out = model.encode_image(x, features_list)
        anomaly_features = out["anomaly_features"]
        normal_features = out["normal_features"]
        patch_tokens = out["patch_tokens"]
        patch_start_idx = out["patch_start_idx"]

        patch_features_list = [pt[:, patch_start_idx:, :] for pt in patch_tokens]
        if cross_attn is not None:
            adapted = cross_attn(anomaly_features, normal_features, patch_features_list, features_list)
            anomaly_features_list = [a["anomaly"] for a in adapted]
            normal_features_list = [a["normal"] for a in adapted]
        else:
            anomaly_features_list = [anomaly_features] * len(patch_tokens)
            normal_features_list = [normal_features] * len(patch_tokens)

        maps = []
        for i, pt in enumerate(patch_tokens):
            af = F.normalize(anomaly_features_list[i], dim=1, eps=1e-8)
            nf = F.normalize(normal_features_list[i], dim=1, eps=1e-8)
            key = f"layer_{features_list[i]}"
            patch_feat = pt[:, patch_start_idx:, :]
            if key in layer_transforms:
                B, N, D = patch_feat.shape
                patch_feat = layer_transforms[key](patch_feat.reshape(-1, D)).view(B, N, D)
            am = generate_anomaly_map_from_tokens(af, nf, patch_feat, image_size)
            maps.append(am)

        fused = torch.stack(maps).sum(dim=0).cpu()
        smoothed = gaussian_filter(fused[0].numpy(), sigma=sigma)
        smoothed_t = torch.from_numpy(smoothed)

        score = reduce_anomaly_map(smoothed_t, mode="topk_mean", topk_ratio=0.01)
        return float(score.item())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--output", required=True)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--checkpoint",
                    default=str(VAD_ROOT / "weight" / "train_on_mvtec" / "CLIP.pth"))
    ap.add_argument("--sigma", type=int, default=4)
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

    print(f"Loading VisualAD from {args.checkpoint}")
    model, preprocess, features_list, image_size, layer_transforms, cross_attn = \
        load_visualad(args.checkpoint, args.device)
    print(f"Image size={image_size}, features_list={features_list}")

    results = list(done.values())
    pending = [it for it in items if it["item_id"] not in done]
    print(f"Manifest items={len(items)}, pending={len(pending)}")

    t0 = time.time()
    for it in tqdm(pending, desc="VisualAD"):
        try:
            s = score_item(
                model, preprocess, features_list, image_size,
                layer_transforms, cross_attn, it["query_path"],
                args.device, sigma=args.sigma,
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
