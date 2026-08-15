"""
Classical (training-free) baselines for benchmark.

Methods:
  - DINOv2-GlobalNN: global embedding cosine similarity to reference pool
  - DINOv2-PatchNN:  patch-level nearest-neighbor distance
  - CLIP-ZeroShot:   text-image similarity for "normal" vs "anomalous"

Usage:
  python benchmark/scripts/classical_baselines.py \
      --manifest benchmark/manifests/full_manifest.json \
      --split calibration \
      --method dinov2_global \
      --output benchmark/results/dinov2_global_calibration.json
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


# ─── DINOv2 ───────────────────────────────────────────────────────────────────

def load_dinov2():
    import torchvision.transforms as T
    model = torch.hub.load("facebookresearch/dinov2", "dinov2_vitb14",
                           source="github", force_reload=False)
    model.eval().to(DEVICE)
    transform = T.Compose([
        T.ToPILImage(),
        T.Resize(224),
        T.CenterCrop(224),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    return model, transform


def embed_image_dino(model, transform, path: str) -> torch.Tensor:
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    x = transform(img).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        feat = model(x)
    return F.normalize(feat, dim=-1).squeeze(0)


def embed_patches_dino(model, transform, path: str, patch_size: int = 224) -> torch.Tensor:
    """Return CLS token of each patch tile (no overlap for simplicity)."""
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w = img.shape[:2]
    # Take 2x2 = 4 patches
    patches = []
    for r in [0, h//2]:
        for c in [0, w//2]:
            p = img[r:r+h//2, c:c+w//2]
            patches.append(transform(p).unsqueeze(0).to(DEVICE))
    batch = torch.cat(patches, dim=0)
    with torch.no_grad():
        feats = model(batch)
    return F.normalize(feats, dim=-1)


def run_dinov2_global(items):
    model, transform = load_dinov2()
    results = []
    for item in tqdm(items, desc="DINOv2-Global"):
        try:
            query_feat = embed_image_dino(model, transform, item["query_path"])
            if item["ref_paths"]:
                ref_feats = torch.stack([
                    embed_image_dino(model, transform, p)
                    for p in item["ref_paths"][:2]
                ])
                sim = (query_feat @ ref_feats.T).max().item()
                score = float(1.0 - sim)  # high distance = anomalous
            else:
                score = 0.5
            results.append({**base_result(item), "anomaly_score": score,
                             "label_pred": int(score > 0.5), "error": None})
        except Exception as e:
            results.append({**base_result(item), "anomaly_score": 0.5,
                             "label_pred": 0, "error": str(e)})
    return results


def run_dinov2_patch(items):
    model, transform = load_dinov2()
    results = []
    for item in tqdm(items, desc="DINOv2-PatchNN"):
        try:
            q_patches = embed_patches_dino(model, transform, item["query_path"])
            if item["ref_paths"]:
                ref_patches = torch.cat([
                    embed_patches_dino(model, transform, p)
                    for p in item["ref_paths"][:2]
                ], dim=0)
                sim = (q_patches @ ref_patches.T)  # [Nq, Nr]
                max_sim_per_patch = sim.max(dim=1).values
                score = float(1.0 - max_sim_per_patch.mean().item())
            else:
                score = 0.5
            results.append({**base_result(item), "anomaly_score": score,
                             "label_pred": int(score > 0.5), "error": None})
        except Exception as e:
            results.append({**base_result(item), "anomaly_score": 0.5,
                             "label_pred": 0, "error": str(e)})
    return results


# ─── CLIP ─────────────────────────────────────────────────────────────────────

CLIP_TEMPLATES = {
    "D1": ["a photo of a defective product", "a photo of a normal product"],
    "D5": ["a photo of a damaged or missing retail item",
           "a photo of a normal retail shelf item"],
    "D2": ["an X-ray scan containing prohibited or dangerous items",
           "a normal clear X-ray baggage scan"],
    "D6": ["a photo of cracked or damaged concrete",
           "a photo of normal concrete surface"],
    "D3": ["a chest X-ray showing pathology or disease",
           "a normal chest X-ray with no findings"],
    "D4": ["a satellite image showing damage or destruction",
           "a normal satellite image with no damage"],
    "D7": ["a road scene with unusual or dangerous objects",
           "a normal clear road scene"],
    "D8": ["a surveillance frame showing abnormal activity or objects",
           "a normal surveillance scene"],
}
DEFAULT_TEMPLATES = ["a photo showing an anomaly or defect",
                     "a photo of a normal scene without defects"]


def load_clip():
    import open_clip
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k"
    )
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    model.eval().to(DEVICE)
    return model, preprocess, tokenizer


def run_clip_zeroshot(items):
    try:
        model, preprocess, tokenizer = load_clip()
    except ImportError:
        print("[WARN] open_clip not installed. Install: pip install open-clip-torch")
        return []
    import torchvision.transforms.functional as TF
    from PIL import Image

    results = []
    for item in tqdm(items, desc="CLIP-ZeroShot"):
        try:
            templates = CLIP_TEMPLATES.get(item["domain_code"], DEFAULT_TEMPLATES)
            texts = tokenizer(templates).to(DEVICE)
            with torch.no_grad():
                text_feats = F.normalize(model.encode_text(texts), dim=-1)

            img = Image.open(item["query_path"]).convert("RGB")
            x = preprocess(img).unsqueeze(0).to(DEVICE)
            with torch.no_grad():
                img_feat = F.normalize(model.encode_image(x), dim=-1)

            sims = (img_feat @ text_feats.T).squeeze(0)
            # sims[0] = anomaly template, sims[1] = normal template
            score = float(torch.softmax(sims * 100, dim=0)[0].item())

            results.append({**base_result(item), "anomaly_score": score,
                             "label_pred": int(score > 0.5), "error": None})
        except Exception as e:
            results.append({**base_result(item), "anomaly_score": 0.5,
                             "label_pred": 0, "error": str(e)})
    return results


# ─── Helpers ──────────────────────────────────────────────────────────────────

def base_result(item):
    return {
        "item_id": item["item_id"],
        "domain": item["domain"],
        "domain_code": item["domain_code"],
        "label_gt": item["label"],
        "split": item.get("split"),
        "source_dataset": item.get("source_dataset"),
        "category": item.get("category"),
        "anomaly_type_pred": None,
        "raw_output": None,
        "cost_tokens": {"input": 0, "output": 0},
        "latency_sec": 0.0,
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--split", default="calibration",
                        choices=["calibration", "dev", "test", "all"])
    parser.add_argument("--method", required=True,
                        choices=["dinov2_global", "dinov2_patch", "clip_zeroshot"])
    parser.add_argument("--output", required=True)
    parser.add_argument("--domains", nargs="*", default=None)
    args = parser.parse_args()

    with open(args.manifest) as f:
        all_items = json.load(f)

    items = [x for x in all_items
             if (args.split == "all" or x.get("split") == args.split)
             and (args.domains is None or x["domain_code"] in args.domains)]

    print(f"{args.method}: {len(items)} items")

    if args.method == "dinov2_global":
        results = run_dinov2_global(items)
    elif args.method == "dinov2_patch":
        results = run_dinov2_patch(items)
    elif args.method == "clip_zeroshot":
        results = run_clip_zeroshot(items)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
