"""
Build visual retrieval index for each domain using DINOv2 embeddings.

For each domain, extracts embeddings from all train/good (normal) images,
saves as a .npz file for fast retrieval at inference time.

Usage:
  python benchmark/scripts/build_retrieval_index.py
"""

import json
import os
import numpy as np
import torch
from pathlib import Path
from tqdm import tqdm

# Use DINOv2-small via timm (fast, good features)
MODEL_NAME = "vit_small_patch14_dinov2.lvd142m"


def load_model(device="cuda"):
    import timm
    model = timm.create_model(MODEL_NAME, pretrained=True, num_classes=0)
    model = model.to(device).eval()

    data_cfg = timm.data.resolve_data_config(model.pretrained_cfg)
    transform = timm.data.create_transform(**data_cfg, is_training=False)
    return model, transform


def extract_embedding(model, transform, image_path, device="cuda"):
    from PIL import Image
    img = Image.open(image_path).convert("RGB")
    tensor = transform(img).unsqueeze(0).to(device)
    with torch.no_grad():
        emb = model(tensor)
    return emb.cpu().numpy().flatten()


def build_index_for_domain(manifest_path, domain_code, output_dir, model, transform, device="cuda"):
    """Build retrieval index from train/good images for a domain."""
    with open(manifest_path) as f:
        manifest = json.load(f)

    # Collect all unique ref paths for this domain (these are the normal bank)
    ref_paths = set()
    for item in manifest:
        if item["domain_code"] == domain_code:
            for rp in item.get("ref_paths", []):
                ref_paths.add(rp)

    ref_paths = sorted(ref_paths)
    if not ref_paths:
        print(f"  {domain_code}: no ref paths found, skipping")
        return

    print(f"  {domain_code}: extracting embeddings for {len(ref_paths)} normal images...")

    embeddings = []
    valid_paths = []
    for rp in tqdm(ref_paths, desc=f"  {domain_code}"):
        if not os.path.exists(rp):
            continue
        try:
            emb = extract_embedding(model, transform, rp, device)
            embeddings.append(emb)
            valid_paths.append(rp)
        except Exception as e:
            print(f"  Warning: failed to process {rp}: {e}")

    if not embeddings:
        print(f"  {domain_code}: no valid embeddings")
        return

    embeddings = np.array(embeddings)
    # Normalize for cosine similarity
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / (norms + 1e-8)

    output_path = Path(output_dir) / f"{domain_code}_index.npz"
    np.savez(str(output_path), embeddings=embeddings, paths=np.array(valid_paths))
    print(f"  {domain_code}: saved {len(valid_paths)} embeddings → {output_path}")


def retrieve_topk(query_path, index_path, model, transform, k=4, device="cuda"):
    """Retrieve top-k most similar normal images for a query."""
    data = np.load(index_path, allow_pickle=True)
    bank_embs = data["embeddings"]
    bank_paths = data["paths"]

    query_emb = extract_embedding(model, transform, query_path, device)
    query_emb = query_emb / (np.linalg.norm(query_emb) + 1e-8)

    # Cosine similarity
    sims = bank_embs @ query_emb
    topk_idx = np.argsort(sims)[::-1][:k]

    results = [(str(bank_paths[i]), float(sims[i])) for i in topk_idx]
    return results


if __name__ == "__main__":
    manifest_path = "/hdd1/jiangxi/AD-Agent/benchmark/manifests/full_manifest.json"
    output_dir = "/hdd1/jiangxi/AD-Agent/benchmark/retrieval_index"
    os.makedirs(output_dir, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading {MODEL_NAME} on {device}...")
    model, transform = load_model(device)

    domains = ["D1", "D2", "D4", "D5", "D5b", "D5c", "D5d", "D7", "D9", "D10"]
    for dc in domains:
        build_index_for_domain(manifest_path, dc, output_dir, model, transform, device)

    print("\nDone! Retrieval indices saved to:", output_dir)
