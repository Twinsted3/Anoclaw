"""
Agent Tools for AnomaClaw V2.

Tools available to the main agent:
1. visual_retrieval - retrieve top-k similar normal refs from image bank
2. domain_knowledge - lookup domain-specific anomaly criteria
3. reference_comparison - detailed visual comparison with refs
"""

import json
import os
import numpy as np
from pathlib import Path


# ─── Tool 1: Visual Retrieval ────────────────────────────────────────────────

_retrieval_cache = {}  # {domain_code: (embeddings, paths, model, transform)}


def _load_retrieval_model(device="cuda"):
    import torch
    import timm
    model = timm.create_model("vit_small_patch14_dinov2.lvd142m", pretrained=True, num_classes=0)
    model = model.to(device).eval()
    data_cfg = timm.data.resolve_data_config(model.pretrained_cfg)
    transform = timm.data.create_transform(**data_cfg, is_training=False)
    return model, transform


def _get_query_embedding(image_path, model, transform, device="cuda"):
    import torch
    from PIL import Image
    img = Image.open(image_path).convert("RGB")
    tensor = transform(img).unsqueeze(0).to(device)
    with torch.no_grad():
        emb = model(tensor)
    emb = emb.cpu().numpy().flatten()
    return emb / (np.linalg.norm(emb) + 1e-8)


def tool_visual_retrieval(query_image_path, domain_code, k=4,
                          index_dir="/hdd1/jiangxi/AD-Agent/benchmark/retrieval_index",
                          device="cuda"):
    """Retrieve top-k most similar normal reference images."""
    global _retrieval_cache

    if "model" not in _retrieval_cache:
        model, transform = _load_retrieval_model(device)
        _retrieval_cache["model"] = model
        _retrieval_cache["transform"] = transform

    model = _retrieval_cache["model"]
    transform = _retrieval_cache["transform"]

    # Load index
    if domain_code not in _retrieval_cache:
        index_path = os.path.join(index_dir, f"{domain_code}_index.npz")
        if not os.path.exists(index_path):
            return []
        data = np.load(index_path, allow_pickle=True)
        _retrieval_cache[domain_code] = {
            "embeddings": data["embeddings"],
            "paths": data["paths"],
        }

    bank = _retrieval_cache[domain_code]
    query_emb = _get_query_embedding(query_image_path, model, transform, device)
    sims = bank["embeddings"] @ query_emb
    topk_idx = np.argsort(sims)[::-1][:k]

    results = [(str(bank["paths"][i]), float(sims[i])) for i in topk_idx]
    return results


# ─── Tool 2: Domain Knowledge ────────────────────────────────────────────────

# manifests_v2 taxonomy (2026-04-21). Keys correspond to benchmark/manifests_v2/domain_config.json:
# D1=MVTec-AD, D2=GoodsAD, D3=VisA, D4=SDNET, D5=MVTec-LOCO, D6=Real3D-AD, D7=LEVIR-CD+,
# D8=DermaMNIST, D9=BraTS, D10=BMAD-Liver, D11=HyperKvasir, D12=BDD100K+RoadAnomaly21.
DOMAIN_KNOWLEDGE = {
    "D1": {
        "domain": "Industrial Manufacturing (MVTec-AD)",
        "normal": "Defect-free manufactured products (bottles, cables, pills, screws, etc.)",
        "anomaly_criteria": [
            "Surface defects: scratches, stains, discoloration, rough patches",
            "Structural defects: cracks, breaks, bends, missing parts",
            "Contamination: foreign objects, glue residue, oil marks",
            "Missing/extra components: wrong count, misplaced parts",
        ],
        "common_false_positives": [
            "Lighting variation or shadow differences",
            "Slight rotation or positioning differences",
            "Normal manufacturing tolerance in dimensions",
        ],
    },
    "D2": {
        "domain": "Retail Products (GoodsAD)",
        "normal": "Intact consumer products (bottles, cans, boxes, packages)",
        "anomaly_criteria": [
            "Physical damage: dents, tears, crushed packaging",
            "Opening defects: caps open/half-open, seals broken",
            "Surface damage: scratches, stains, label problems",
            "Missing parts: straw missing, cap missing",
        ],
        "common_false_positives": [
            "Different viewing angle of the same product",
            "Normal label variation (different batch/print run)",
            "Slight color differences due to lighting",
        ],
    },
    "D3": {
        "domain": "Industrial Inspection (VisA)",
        "normal": "Defect-free manufactured items (PCBs, capsules, candles, etc.)",
        "anomaly_criteria": [
            "Surface defects: scratches, cracks, discoloration",
            "Structural anomalies: bent pins, missing solder, misalignment",
            "Contamination: foreign particles, excess adhesive",
        ],
        "common_false_positives": [
            "Normal manufacturing variation in appearance",
            "Slight positional differences",
            "Lighting artifacts or reflections",
        ],
    },
    "D4": {
        "domain": "Infrastructure Maintenance (SDNET2018)",
        "normal": "Intact concrete surfaces (deck, pavement, wall)",
        "anomaly_criteria": [
            "Cracks: linear dark lines crossing the surface, may be very thin",
            "Types: transverse, longitudinal, map/alligator cracking",
            "Look for: continuous dark lines that cross aggregate boundaries",
        ],
        "common_false_positives": [
            "Surface texture variation and aggregate patterns",
            "Stains, discoloration, or weathering marks",
            "Construction joints or control joints (intentional)",
            "Shadows from nearby objects",
        ],
    },
    "D5": {
        "domain": "Logical Anomaly (MVTec-LOCO)",
        "normal": "Correctly assembled products with right parts in right positions",
        "anomaly_criteria": [
            "LOGICAL: wrong count (extra/missing items)",
            "LOGICAL: wrong arrangement or position of parts",
            "LOGICAL: wrong type of component in a slot",
            "STRUCTURAL: physical damage to any component",
        ],
        "common_false_positives": [
            "Slight position variation within tolerance",
            "Different viewing angle showing same correct assembly",
            "Color variation in same-type components",
        ],
    },
    "D6": {
        "domain": "3D Product — rendered point cloud (Real3D-AD)",
        "normal": "Geometrically intact product matching reference shape (no bulge, sink, hole, or added material)",
        "anomaly_criteria": [
            "Bulge: outward protrusion on the 3D surface vs reference shape",
            "Sink: inward depression or dent",
            "Hole: missing material / perforation through the surface",
            "Contamination: foreign bumps or added material on the surface",
            "Asymmetry / deformation relative to reference renders",
        ],
        "common_false_positives": [
            "Low surface detail inherent to point-cloud rendering",
            "Viewpoint rotation vs reference (same shape, different angle)",
            "Dotted / sparse texture from point-cloud density variation",
        ],
    },
    "D7": {
        "domain": "Remote Sensing / Building Change (LEVIR-CD+)",
        "normal": "No building change between reference (earlier) and query (later) aerial tiles of the same location",
        "anomaly_criteria": [
            "New construction: buildings present in query that are absent in reference",
            "Building demolition: buildings in reference removed in query",
            "Roof replacement or expansion of an existing building footprint",
            "Road or warehouse extension into previously open ground",
        ],
        "common_false_positives": [
            "Seasonal / radiometric differences (lighting, vegetation colour)",
            "Shadow direction differences between captures",
            "Minor parked-vehicle or surface-stain changes (not buildings)",
            "Cloud or atmospheric artifacts",
        ],
    },
    "D8": {
        "domain": "Dermatology (DermaMNIST/ISIC)",
        "normal": "Melanocytic nevi (benign moles)",
        "anomaly_criteria": [
            "ABCDE criteria for melanoma:",
            "A - Asymmetry: one half unlike the other",
            "B - Border: irregular, ragged, or blurred edges",
            "C - Color: varied shades (tan, brown, black, red, white, blue)",
            "D - Diameter: larger than 6mm (pencil eraser)",
            "E - Evolving: changing in size, shape, or color",
        ],
        "common_false_positives": [
            "Hair artifacts overlaying the lesion",
            "Dermoscopic artifacts (bubbles, ink marks)",
            "Normal benign nevi can have slight asymmetry",
            "Dark but uniformly colored moles are typically benign",
        ],
    },
    "D9": {
        "domain": "Brain MRI (BraTS2021)",
        "normal": "Normal brain MRI slices",
        "anomaly_criteria": [
            "Focal hyperintense or hypointense lesions",
            "Mass effect: midline shift, ventricular compression",
            "Abnormal enhancement patterns",
            "Irregular tissue boundaries suggesting tumor infiltration",
        ],
        "common_false_positives": [
            "Normal anatomical asymmetry between hemispheres",
            "Slice position differences (different axial level)",
            "Partial volume effects at tissue boundaries",
            "Normal choroid plexus or ventricular variation",
        ],
    },
    "D10": {
        "domain": "Liver CT (BMAD-Liver)",
        "normal": "Normal liver CT slices",
        "anomaly_criteria": [
            "Focal hypodense or hyperdense lesions within liver parenchyma",
            "Irregular margins suggesting malignancy",
            "Portal vein invasion or biliary dilation",
        ],
        "common_false_positives": [
            "Different slice levels showing different liver segments",
            "Normal hepatic vessels appearing as hypodense spots",
            "Partial volume artifacts at liver edges",
            "Normal gallbladder or ligamentum teres",
        ],
    },
    "D11": {
        "domain": "Gastrointestinal Endoscopy (HyperKvasir)",
        "normal": "Normal colon/GI mucosa",
        "anomaly_criteria": [
            "Polyps: raised mucosal lesions protruding into lumen",
            "Ulceration: mucosal breaks with crater-like appearance",
            "Tumor: irregular mass with abnormal vasculature",
            "Inflammation: erythema, edema, loss of vascular pattern",
        ],
        "common_false_positives": [
            "Normal mucosal folds and haustral markings",
            "Specular reflections from endoscope light",
            "Bubbles or debris in the lumen",
            "Normal vascular pattern variation",
        ],
    },
    "D12": {
        "domain": "Road Safety (BDD100K + RoadAnomaly21)",
        "normal": "Normal road driving scenes",
        "anomaly_criteria": [
            "Unexpected objects on road: animals, debris, fallen cargo",
            "Unusual vehicles: tractors, construction equipment on highway",
            "Road hazards: large potholes, collapsed barriers",
        ],
        "common_false_positives": [
            "Normal parked cars or vehicles in adjacent lanes",
            "Traffic signs, road markings, construction zones",
            "Pedestrians on sidewalks (expected)",
            "Weather conditions (rain, snow on road surface)",
        ],
    },
}


def tool_domain_knowledge(domain_code):
    """Return domain-specific anomaly detection knowledge."""
    return DOMAIN_KNOWLEDGE.get(domain_code, {})


# ─── Tool 3: Expert AD Model (DINOv2 few-shot) ──────────────────────────────

def tool_expert_ad_score(query_image_path, domain_code, k=8,
                         index_dir="/hdd1/jiangxi/AD-Agent/benchmark/retrieval_index",
                         device="cuda"):
    """Few-shot AD using DINOv2 embedding distance.
    Returns anomaly_score (0-1) and interpretation.
    High score = query is far from all normal images = likely anomalous.
    """
    retrieved = tool_visual_retrieval(query_image_path, domain_code, k=k,
                                       index_dir=index_dir, device=device)
    if not retrieved:
        return {"anomaly_score": 0.5, "confidence": "low", "reason": "no retrieval index"}

    sims = [s for _, s in retrieved]
    top1_sim = sims[0]
    avg_sim = np.mean(sims)

    # Anomaly score = 1 - top1_similarity
    anomaly_score = 1.0 - top1_sim

    # Interpretation
    if top1_sim > 0.95:
        interpretation = "very similar to normal bank — likely normal"
        confidence = "high"
    elif top1_sim > 0.85:
        interpretation = "moderately similar to normal bank — possibly normal"
        confidence = "medium"
    elif top1_sim > 0.70:
        interpretation = "somewhat different from normal bank — inspect carefully"
        confidence = "medium"
    else:
        interpretation = "very different from normal bank — likely anomalous"
        confidence = "high"

    return {
        "anomaly_score": round(anomaly_score, 3),
        "top1_similarity": round(top1_sim, 3),
        "avg_similarity": round(avg_sim, 3),
        "interpretation": interpretation,
        "confidence": confidence,
    }
