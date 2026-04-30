"""
Build the v2 cross-domain benchmark manifest with 12 unified domains (D1-D12).

Remaps the original builder functions from build_manifest.py into a clean
D1-D12 numbering scheme. No builder logic is duplicated — all dataset-specific
code lives in build_manifest.py and is imported here.

Domain mapping (v2):
  D1  MVTec-AD          Industrial Manufacturing
  D5  GoodsAD           Retail / Product QC
  D2  VisA              Complex Industrial
  D6  SDNET2018         Infrastructure / Maintenance
  D3  MVTec-LOCO        Logical Anomaly
  D4  MVTec-3D          3D Industrial
  D7  LEVIR-CD+         Remote Sensing / Change Detection
  D8  DermaMNIST        Medical — Dermatology
  D9  BraTS2021         Medical — Brain MRI
  D10 BMAD-Liver        Medical — Liver CT
  D11 HyperKvasir       Medical — GI Endoscopy
  D12 BDD100K+RA21      Road Safety

Outputs:
  benchmark/manifests_v2/{domain}_manifest.json  — per-domain
  benchmark/manifests_v2/full_manifest.json      — combined
  benchmark/manifests_v2/split_ids.json          — calibration / dev / test
"""

import json
import copy
from pathlib import Path

import random
from build_manifest import (
    build_d1_industrial,
    build_d2_retail,
    build_d10_visa,
    build_d4_maintenance,
    build_d9_loco,
    build_d11_mvtec3d,
    build_d6_remote_sensing,
    build_d5_medical,
    build_d5b_brain,
    build_d5c_liver,
    build_d5d_colon,
    build_d7_road,
    SPLIT_SIZES,
    assign_split,
)

REAL3D_RGB_ROOT = Path("/hdd1/jiangxi/AD-Agent/benchmark/data/Real3D-AD-RGB")

def build_d6_real3d():
    """D4: Real3D-AD — 3D product anomaly detection from rendered point cloud RGB views."""
    if not REAL3D_RGB_ROOT.exists():
        print("  [WARN] D4: Real3D-AD rendered images not found. Run: python benchmark/scripts/render_real3d.py")
        return []

    random.seed(42)
    items = []
    item_idx = 0
    skip = {"test_render", "gemstone_registration", "gyro"}

    for cat_dir in sorted(REAL3D_RGB_ROOT.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name in skip:
            continue
        cat_name = cat_dir.name

        # Collect template images as references
        template_imgs = sorted(str(p) for p in cat_dir.rglob("train/template/*.png"))
        refs = template_imgs[:10] if template_imgs else []

        # Normal test images
        normal_imgs = sorted(str(p) for p in cat_dir.rglob("test/normal/*.png"))
        random.shuffle(normal_imgs)
        for img in normal_imgs[:12]:
            items.append({
                "item_id": f"D4_{item_idx:04d}",
                "domain": "industrial_3d",
                "domain_code": "D4",
                "query_path": img,
                "ref_paths": refs,
                "label": 0,
                "anomaly_type": None,
                "source_dataset": "Real3D-AD",
                "category": cat_name,
                "split": None,
            })
            item_idx += 1

        # Anomaly test images
        anomaly_imgs = sorted(str(p) for p in cat_dir.rglob("test/anomaly/*.png"))
        random.shuffle(anomaly_imgs)
        for img in anomaly_imgs[:12]:
            items.append({
                "item_id": f"D4_{item_idx:04d}",
                "domain": "industrial_3d",
                "domain_code": "D4",
                "query_path": img,
                "ref_paths": refs,
                "label": 1,
                "anomaly_type": "geometric_defect",
                "source_dataset": "Real3D-AD",
                "category": cat_name,
                "split": None,
            })
            item_idx += 1

    if not items:
        return []

    normal = [x for x in items if x["label"] == 0]
    anomaly = [x for x in items if x["label"] == 1]
    random.shuffle(normal); random.shuffle(anomaly)
    items = normal[:90] + anomaly[:90]
    for i, item in enumerate(items):
        item["item_id"] = f"D4_{i:04d}"
    print(f"  D4: {min(len(normal),90)} normal, {min(len(anomaly),90)} anomaly (Real3D-AD RGB)")
    return assign_split(items)

# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------
MANIFEST_V2_DIR = Path("/hdd1/jiangxi/AD-Agent/benchmark/manifests_v2")
MANIFEST_V2_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Domain configuration — single source of truth for the 12-domain benchmark
# ---------------------------------------------------------------------------
DOMAIN_CONFIG = {
    "D1": {
        "name": "Industrial Manufacturing",
        "source_dataset": "MVTec-AD",
        "anomaly_type": "surface_defect / structural",
        "modality": "RGB",
        "reference_type": "few-shot (train/good)",
        "description": "Classic industrial surface inspection across 15 object/texture categories.",
    },
    "D5": {
        "name": "Retail / Product QC",
        "source_dataset": "GoodsAD",
        "anomaly_type": "packaging_defect / contamination",
        "modality": "RGB",
        "reference_type": "few-shot (same product)",
        "description": "Retail shelf product anomaly detection with product-matched references.",
    },
    "D2": {
        "name": "Complex Industrial",
        "source_dataset": "VisA",
        "anomaly_type": "defect",
        "modality": "RGB",
        "reference_type": "few-shot (train/good)",
        "description": "12-category industrial AD with complex textures and fine-grained defects.",
    },
    "D6": {
        "name": "Infrastructure / Maintenance",
        "source_dataset": "SDNET2018",
        "anomaly_type": "crack",
        "modality": "RGB",
        "reference_type": "few-shot (uncracked surface)",
        "description": "Concrete crack detection on decks, walls, and pavement.",
    },
    "D3": {
        "name": "Logical Anomaly",
        "source_dataset": "MVTec-LOCO",
        "anomaly_type": "logical / structural",
        "modality": "RGB",
        "reference_type": "few-shot (train/good)",
        "description": "Logical and structural constraint violations beyond surface defects.",
    },
    "D4": {
        "name": "3D Product (RGB)",
        "source_dataset": "Real3D-AD",
        "anomaly_type": "geometric_defect",
        "modality": "rendered point cloud",
        "reference_type": "few-shot (template renders)",
        "description": "3D product anomaly detection from rendered point cloud views (bulge, sink, contamination).",
    },
    "D7": {
        "name": "Remote Sensing / Change Detection",
        "source_dataset": "LEVIR-CD+",
        "anomaly_type": "building_change",
        "modality": "satellite RGB",
        "reference_type": "temporal pair (before image)",
        "description": "Satellite building change detection between temporal image pairs.",
    },
    "D8": {
        "name": "Medical — Dermatology",
        "source_dataset": "DermaMNIST",
        "anomaly_type": "melanoma",
        "modality": "dermoscopy RGB",
        "reference_type": "few-shot (benign nevi)",
        "description": "Skin lesion anomaly detection: melanocytic nevi (normal) vs melanoma.",
    },
    "D9": {
        "name": "Medical — Brain MRI",
        "source_dataset": "BraTS2021",
        "anomaly_type": "pathology (tumor)",
        "modality": "MRI slice",
        "reference_type": "few-shot (healthy slices)",
        "description": "Brain MRI anomaly detection from BMAD benchmark (BraTS2021 slices).",
    },
    "D10": {
        "name": "Medical — Liver CT",
        "source_dataset": "BMAD-Liver",
        "anomaly_type": "pathology",
        "modality": "CT slice",
        "reference_type": "few-shot (healthy slices)",
        "description": "Liver CT anomaly detection from BMAD benchmark.",
    },
    "D11": {
        "name": "Medical — GI Endoscopy",
        "source_dataset": "HyperKvasir",
        "anomaly_type": "pathology (polyp/ulcer)",
        "modality": "endoscopy RGB",
        "reference_type": "few-shot (normal mucosa)",
        "description": "GI tract endoscopy anomaly detection: normal mucosa vs polyps/ulcers.",
    },
    "D12": {
        "name": "Road Safety",
        "source_dataset": "BDD100K + RoadAnomaly21",
        "anomaly_type": "road_obstacle",
        "modality": "dashcam RGB",
        "reference_type": "few-shot (normal road scenes)",
        "description": "Road scene anomaly detection: normal driving vs unexpected obstacles.",
    },
}

# ---------------------------------------------------------------------------
# Mapping: new v2 code -> (builder_func, old_code, new_domain_name, v2_file_label)
# ---------------------------------------------------------------------------
_DOMAIN_MAP = {
    "D1":  (build_d1_industrial,    "D1",  "industrial",        "D1_industrial"),
    "D5":  (build_d2_retail,        "D5",  "retail",            "D5_retail"),
    "D2":  (build_d10_visa,         "D10", "complex_industrial","D2_complex_industrial"),
    "D6":  (build_d4_maintenance,   "D6",  "infrastructure",    "D6_infrastructure"),
    "D3":  (build_d9_loco,          "D9",  "logical",           "D3_logical"),
    "D4":  (build_d6_real3d,         "D4",  "industrial_3d",     "D4_industrial_3d"),
    "D7":  (build_d6_remote_sensing,"D4",  "remote_sensing",    "D7_remote_sensing"),
    "D8":  (build_d5_medical,       "D3",  "dermatology",       "D8_dermatology"),
    "D9":  (build_d5b_brain,        "D3b", "brain_mri",         "D9_brain_mri"),
    "D10": (build_d5c_liver,        "D3c", "liver_ct",          "D10_liver_ct"),
    "D11": (build_d5d_colon,        "D3d", "gi_endoscopy",      "D11_gi_endoscopy"),
    "D12": (build_d7_road,          "D7",  "road_safety",       "D12_road_safety"),
}


# ---------------------------------------------------------------------------
# Remapping utility
# ---------------------------------------------------------------------------

def remap_items(items, old_code, new_code, new_domain_name):
    """Remap a list of manifest items from one domain code to another.

    Updates:
      - domain_code:  old_code -> new_code
      - domain:       -> new_domain_name
      - item_id:      replaces the old_code prefix with new_code
                       e.g. "D10_0042" -> "D2_0042"

    Returns a new list (originals are not mutated).
    """
    remapped = []
    for item in items:
        new_item = copy.deepcopy(item)
        new_item["domain_code"] = new_code
        new_item["domain"] = new_domain_name

        old_id = new_item["item_id"]
        # Handle codes like "D3b", "D3c", "D3d" as well as "D10", "D11"
        if old_id.startswith(old_code + "_"):
            suffix = old_id[len(old_code) + 1:]  # everything after "Dxx_"
            new_item["item_id"] = f"{new_code}_{suffix}"

        remapped.append(new_item)
    return remapped


# ---------------------------------------------------------------------------
# Per-domain save helper
# ---------------------------------------------------------------------------

def _save_domain(items, file_label):
    """Save a per-domain manifest JSON."""
    path = MANIFEST_V2_DIR / f"{file_label}_manifest.json"
    with open(path, "w") as f:
        json.dump(items, f, indent=2)
    print(f"  Saved {len(items)} items -> {path}")


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_all_v2():
    """Build the full 12-domain v2 benchmark manifest."""
    all_items = []
    domain_stats = {}

    for new_code in sorted(_DOMAIN_MAP.keys(), key=lambda c: int(c[1:])):
        builder, old_code, domain_name, file_label = _DOMAIN_MAP[new_code]
        cfg = DOMAIN_CONFIG[new_code]

        print(f"Building {new_code}: {cfg['name']} ({cfg['source_dataset']})...")
        raw_items = builder()

        if raw_items:
            items = remap_items(raw_items, old_code, new_code, domain_name)
            _save_domain(items, file_label)
        else:
            items = []

        all_items.extend(items)
        domain_stats[new_code] = len(items)

    # ---- Save combined manifest ----
    with open(MANIFEST_V2_DIR / "full_manifest.json", "w") as f:
        json.dump(all_items, f, indent=2)

    # ---- Save split index ----
    split_ids = {"calibration": [], "dev": [], "test": []}
    for item in all_items:
        if item.get("split") in split_ids:
            split_ids[item["split"]].append(item["item_id"])
    with open(MANIFEST_V2_DIR / "split_ids.json", "w") as f:
        json.dump(split_ids, f, indent=2)

    # ---- Save domain config for downstream consumers ----
    with open(MANIFEST_V2_DIR / "domain_config.json", "w") as f:
        json.dump(DOMAIN_CONFIG, f, indent=2)

    # ---- Summary ----
    print("\n=== V2 Manifest Build Summary (12 Domains) ===")
    for code in sorted(domain_stats.keys(), key=lambda c: int(c[1:])):
        count = domain_stats[code]
        cfg = DOMAIN_CONFIG[code]
        status = "OK" if count > 0 else "MISSING - needs download"
        print(f"  {code:>3s}  {cfg['name']:<35s}  {count:>4d} items  [{status}]")

    total = sum(domain_stats.values())
    expected = 12 * 180
    print(f"\n  Total: {total}/{expected} items built")
    print(f"  Manifests saved to: {MANIFEST_V2_DIR}/")
    return all_items


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    build_all_v2()
