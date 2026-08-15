"""
M0: Build the cross-domain benchmark manifest.

Outputs:
  benchmark/manifests/{domain}_manifest.json  — per-domain item list
  benchmark/manifests/full_manifest.json       — all domains combined
  benchmark/manifests/split_ids.json           — calibration / dev / test split

Each item:
{
  "item_id": "D1_0001",
  "domain": "industrial",
  "domain_code": "D1",
  "query_path": "/abs/path/to/image.png",
  "ref_paths": ["/abs/path/normal1.png", "/abs/path/normal2.png"],
  "label": 0 or 1,               # 0=normal, 1=anomalous
  "anomaly_type": "surface_defect" | "..." | null,
  "source_dataset": "MVTec-AD",
  "category": "bottle",
  "split": "calibration" | "dev" | "test"
}
"""

import json
import random
import os
from pathlib import Path

SEED = 42
random.seed(SEED)

_ROOT = os.environ.get("ANOMALYCLAW_ROOT", str(Path(__file__).resolve().parents[2]))

MVTEC_ROOT = Path(_ROOT + "/external_data/MMAD/MVTec-AD")
GOODSAD_ROOT = Path(_ROOT + "/external_data/MMAD/GoodsAD")
MANIFEST_DIR = Path(_ROOT + "/benchmark/manifests")
MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

# Taxonomy mapping
DEFECT_TO_TAXONOMY = {
    # MVTec
    "broken_large": "breakage_or_deformation",
    "broken_small": "breakage_or_deformation",
    "contamination": "contamination_or_artifact",
    "bent": "breakage_or_deformation",
    "bent_wire": "breakage_or_deformation",
    "cable_swap": "missing_or_extra_object",
    "combined": "breakage_or_deformation",
    "cut_inner_insulation": "damage_or_change",
    "cut_outer_insulation": "damage_or_change",
    "missing_cable": "missing_or_extra_object",
    "poke_insulation": "breakage_or_deformation",
    "crack": "breakage_or_deformation",
    "faulty_imprint": "surface_defect",
    "pill_type": "missing_or_extra_object",
    "scratch": "surface_defect",
    "squeeze": "breakage_or_deformation",
    "blowhole": "surface_defect",
    "break": "breakage_or_deformation",
    "burr": "surface_defect",
    "color": "surface_defect",
    "flip": "breakage_or_deformation",
    "rough": "surface_defect",
    "misprint": "surface_defect",
    "thread": "surface_defect",
    "glue": "contamination_or_artifact",
    "gray_stroke": "surface_defect",
    "oil": "contamination_or_artifact",
    "poke": "surface_defect",
    "fold": "breakage_or_deformation",
    "glue_strip": "contamination_or_artifact",
    "hole": "breakage_or_deformation",
    "metal_contamination": "contamination_or_artifact",
    "split": "breakage_or_deformation",
    # GoodsAD
    "cap_half_open": "breakage_or_deformation",
    "cap_open": "missing_or_extra_object",
    "surface_damage": "surface_defect",
    "dent": "surface_defect",
    "breakage": "breakage_or_deformation",
    "label_problem": "surface_defect",
    "dirty": "contamination_or_artifact",
    "opened": "breakage_or_deformation",
    "straw_missing": "missing_or_extra_object",
    "deformation": "breakage_or_deformation",
    "surface_anomaly": "surface_defect",
    "broken": "breakage_or_deformation",
}

SPLIT_SIZES = {"calibration": 20, "dev": 40, "test": 120}  # per domain (10/20/60 normal+anomaly each)


def assign_split(items):
    """Split items list into calibration/dev/test while preserving normal/anomaly balance."""
    normal = [x for x in items if x["label"] == 0]
    anomaly = [x for x in items if x["label"] == 1]
    random.shuffle(normal)
    random.shuffle(anomaly)

    result = []
    for split, total in SPLIT_SIZES.items():
        half = total // 2
        for item in normal[:half]:
            item = dict(item); item["split"] = split; result.append(item)
        for item in anomaly[:half]:
            item = dict(item); item["split"] = split; result.append(item)
        normal = normal[half:]
        anomaly = anomaly[half:]
    return result


def get_mvtec_refs(category_root: Path, n=10):
    """Get n normal reference images from train/good.  v0-v3 use first 2; v4+ use all."""
    train_good = category_root / "train" / "good"
    if not train_good.exists():
        return []
    imgs = sorted(train_good.glob("*.png")) + sorted(train_good.glob("*.jpg"))
    if not imgs:
        return []
    chosen = random.sample(imgs, min(n, len(imgs)))
    return [str(p) for p in chosen]


def build_d1_industrial(max_per_cat=20):
    """D1: MVTec-AD — industrial manufacturing."""
    categories = [d for d in MVTEC_ROOT.iterdir() if d.is_dir()]
    items = []
    item_idx = 0
    for cat in sorted(categories):
        test_root = cat / "test"
        if not test_root.exists():
            continue
        refs = get_mvtec_refs(cat)
        # Normal (good)
        good_dir = test_root / "good"
        normal_imgs = []
        if good_dir.exists():
            normal_imgs = sorted(good_dir.glob("*.png")) + sorted(good_dir.glob("*.jpg"))
        normal_imgs = list(normal_imgs)
        random.shuffle(normal_imgs)
        # Anomaly
        anomaly_imgs = []
        for defect_dir in sorted(test_root.iterdir()):
            if defect_dir.name == "good":
                continue
            imgs = sorted(defect_dir.glob("*.png")) + sorted(defect_dir.glob("*.jpg"))
            for img in imgs:
                taxonomy = DEFECT_TO_TAXONOMY.get(defect_dir.name, "other")
                anomaly_imgs.append((img, defect_dir.name, taxonomy))
        random.shuffle(anomaly_imgs)
        # Cap at max_per_cat each
        for img in normal_imgs[:max_per_cat]:
            items.append({
                "item_id": f"D1_{item_idx:04d}",
                "domain": "industrial",
                "domain_code": "D1",
                "query_path": str(img),
                "ref_paths": refs,
                "label": 0,
                "anomaly_type": None,
                "source_dataset": "MVTec-AD",
                "category": cat.name,
                "split": None,
            })
            item_idx += 1
        for img, defect, taxonomy in anomaly_imgs[:max_per_cat]:
            items.append({
                "item_id": f"D1_{item_idx:04d}",
                "domain": "industrial",
                "domain_code": "D1",
                "query_path": str(img),
                "ref_paths": refs,
                "label": 1,
                "anomaly_type": taxonomy,
                "source_dataset": "MVTec-AD",
                "category": cat.name,
                "split": None,
            })
            item_idx += 1

    # Balance: take 90 normal + 90 anomaly
    normal = [x for x in items if x["label"] == 0]
    anomaly = [x for x in items if x["label"] == 1]
    random.shuffle(normal); random.shuffle(anomaly)
    items = normal[:90] + anomaly[:90]
    # Re-assign IDs
    for i, item in enumerate(items):
        item["item_id"] = f"D1_{i:04d}"
    return assign_split(items)


def _get_goodsad_product_id(path):
    """Extract product ID from GoodsAD filename: {product_id}_{image_id}.jpg"""
    return Path(path).stem.split('_')[0]


def _get_product_refs(train_good_dir, product_id, n=10):
    """Get refs from same product in train/good."""
    all_imgs = sorted(train_good_dir.glob("*.jpg")) + sorted(train_good_dir.glob("*.png"))
    same_product = [p for p in all_imgs if p.stem.split('_')[0] == product_id]
    if len(same_product) >= 2:
        return [str(p) for p in random.sample(same_product, min(n, len(same_product)))]
    # Fallback: if same product has < 2 images, use all same-product + fill from others
    refs = [str(p) for p in same_product]
    others = [p for p in all_imgs if p.stem.split('_')[0] != product_id]
    if others:
        refs += [str(p) for p in random.sample(others, min(n - len(refs), len(others)))]
    return refs


def build_d2_retail(max_per_cat=15):
    """D5: GoodsAD — retail shelf/product anomaly. Refs matched by product ID."""
    categories = [d for d in GOODSAD_ROOT.iterdir() if d.is_dir()]
    items = []
    item_idx = 0
    for cat in sorted(categories):
        test_root = cat / "test"
        if not test_root.exists():
            continue
        train_good = cat / "train" / "good"

        good_dir = test_root / "good"
        normal_imgs = []
        if good_dir.exists():
            normal_imgs = sorted(good_dir.glob("*.png")) + sorted(good_dir.glob("*.jpg"))
        normal_imgs = list(normal_imgs); random.shuffle(normal_imgs)

        anomaly_imgs = []
        for defect_dir in sorted(test_root.iterdir()):
            if defect_dir.name == "good":
                continue
            imgs = sorted(defect_dir.glob("*.png")) + sorted(defect_dir.glob("*.jpg"))
            for img in imgs:
                taxonomy = DEFECT_TO_TAXONOMY.get(defect_dir.name, "other")
                anomaly_imgs.append((img, defect_dir.name, taxonomy))
        random.shuffle(anomaly_imgs)

        for img in normal_imgs[:max_per_cat]:
            pid = _get_goodsad_product_id(img)
            refs = _get_product_refs(train_good, pid) if train_good.exists() else []
            items.append({
                "item_id": f"D5_{item_idx:04d}",
                "domain": "retail",
                "domain_code": "D5",
                "query_path": str(img),
                "ref_paths": refs,
                "label": 0,
                "anomaly_type": None,
                "source_dataset": "GoodsAD",
                "category": cat.name,
                "split": None,
            })
            item_idx += 1
        for img, defect, taxonomy in anomaly_imgs[:max_per_cat]:
            pid = _get_goodsad_product_id(img)
            refs = _get_product_refs(train_good, pid) if train_good.exists() else []
            items.append({
                "item_id": f"D5_{item_idx:04d}",
                "domain": "retail",
                "domain_code": "D5",
                "query_path": str(img),
                "ref_paths": refs,
                "label": 1,
                "anomaly_type": taxonomy,
                "source_dataset": "GoodsAD",
                "category": cat.name,
                "split": None,
            })
            item_idx += 1

    normal = [x for x in items if x["label"] == 0]
    anomaly = [x for x in items if x["label"] == 1]
    random.shuffle(normal); random.shuffle(anomaly)
    items = normal[:90] + anomaly[:90]
    for i, item in enumerate(items):
        item["item_id"] = f"D5_{i:04d}"
    return assign_split(items)


SDNET_ROOT = Path(_ROOT + "/benchmark/data/SDNET2018/DATA_Maguire_20180517_ALL/SDNET2018")
PIDRAY_ROOT = Path(_ROOT + "/benchmark/data/PIDray/data")
ROAD_ROOT = Path(_ROOT + "/benchmark/data/RoadAnomaly21/RoadAnomaly21")
ROADOBS_ROOT = Path(_ROOT + "/benchmark/data/RoadAnomaly21/RoadObstacle21")
BDD_ROOT = Path(_ROOT + "/benchmark/data/BDD100K_normal")
AVENUE_ROOT = Path(_ROOT + "/benchmark/data/Avenue/Avenue Dataset")
CHEXPERT_ROOT = Path(_ROOT + "/benchmark/data/CheXpert")
LEVIR_ROOT = Path(_ROOT + "/benchmark/data/LEVIR-CD")


def build_d3_screening():
    """D2: PIDray — X-ray prohibited item detection (anomalous=contains weapon/prohibited item)."""
    if not PIDRAY_ROOT.exists():
        print("  [WARN] D2: PIDray not found. Run: bash benchmark/scripts/download_datasets.sh pidray")
        return []

    # PIDray: xray_easy*, xray_hard*, xray_hidden* are anomalous (with prohibited items)
    # We treat all PIDray images as anomalous since they contain prohibited items
    anomaly_imgs = []
    for subdir in sorted(PIDRAY_ROOT.iterdir()):
        if subdir.is_dir():
            imgs = sorted(subdir.glob("*.png")) + sorted(subdir.glob("*.jpg"))
            anomaly_imgs.extend(imgs)

    if not anomaly_imgs:
        print("  [WARN] D2: No PIDray images found")
        return []

    random.shuffle(anomaly_imgs)
    # Take up to 90 anomalous X-ray images
    anomaly_imgs = anomaly_imgs[:90]

    # For normal X-ray images: use images where background is clear
    # PIDray doesn't include negatives — use a simple strategy:
    # Label the "easy" ones as the clearer anomalies, treat first half as normal (no clear alternative)
    # Better approach: sample images without annotations. For now, duplicate with flipped label
    # and note this limitation. In paper: use PIDray-hard/hidden as anomalous, easy as borderline.
    # PRACTICAL FIX: Download SIXray-10 negatives or use ImageNet X-ray proxies.
    # For now: use 90 from PIDray as anomalous only. Skip normal (unbalanced but honest).
    # Flag: needs normal X-ray sourcing.
    print(f"  [NOTE] D2: Using {len(anomaly_imgs)} PIDray anomaly images (no normal X-ray available yet)")
    # Create balanced set by treating some as "less anomalous" if we have enough variety
    # For benchmark correctness, we only include items we can label correctly
    items = []
    for i, img in enumerate(anomaly_imgs):
        items.append({
            "item_id": f"D2_{i:04d}",
            "domain": "screening",
            "domain_code": "D2",
            "query_path": str(img),
            "ref_paths": [],  # No reference for X-ray (zero-shot domain)
            "label": 1,
            "anomaly_type": "prohibited_item",
            "source_dataset": "PIDray",
            "category": img.parent.name,
            "split": None,
        })

    # Since we only have anomalous, we need to skip D2 or accept imbalanced
    # Return empty to skip — will revisit when we have normal X-rays
    print("  [SKIP] D2: Cannot build balanced manifest without normal X-ray images. Skipping for now.")
    return []


def build_d4_maintenance():
    """D6: SDNET2018 — concrete crack detection (anomalous=cracked)."""
    if not SDNET_ROOT.exists():
        print("  [WARN] D6: SDNET2018 not found. Run: bash benchmark/scripts/download_datasets.sh sdnet")
        return []

    # Structure: D/CD (deck cracked), D/UD (deck uncracked), W/CW, W/UW, P/CP, P/UP
    items = []
    item_idx = 0
    surface_map = {"D": "deck", "W": "wall", "P": "pavement"}

    for surface_code, surface_name in surface_map.items():
        surface_dir = SDNET_ROOT / surface_code
        if not surface_dir.exists():
            continue
        for subdir in sorted(surface_dir.iterdir()):
            if not subdir.is_dir():
                continue
            name = subdir.name  # e.g. "CD", "UD", "CW", "UW"
            is_cracked = name.startswith("C")
            label = 1 if is_cracked else 0
            anomaly_type = "crack" if is_cracked else None

            imgs = sorted(subdir.glob("*.jpg")) + sorted(subdir.glob("*.png"))
            if not imgs:
                continue
            # Collect reference images from uncracked surface of same type
            ref_dir = surface_dir / f"U{surface_code}"
            refs = []
            if ref_dir.exists():
                ref_imgs = sorted(ref_dir.glob("*.jpg")) + sorted(ref_dir.glob("*.png"))
                refs = [str(p) for p in random.sample(ref_imgs, min(10, len(ref_imgs)))]

            random.shuffle(imgs)
            for img in imgs[:60]:  # cap per subdir
                items.append({
                    "item_id": f"D6_{item_idx:04d}",
                    "domain": "maintenance",
                    "domain_code": "D6",
                    "query_path": str(img),
                    "ref_paths": refs,
                    "label": label,
                    "anomaly_type": anomaly_type,
                    "source_dataset": "SDNET2018",
                    "category": surface_name,
                    "split": None,
                })
                item_idx += 1

    # Balance: 90 normal + 90 anomaly
    normal = [x for x in items if x["label"] == 0]
    anomaly = [x for x in items if x["label"] == 1]
    random.shuffle(normal); random.shuffle(anomaly)
    items = normal[:90] + anomaly[:90]
    for i, item in enumerate(items):
        item["item_id"] = f"D6_{i:04d}"
    print(f"  D6: {len(normal)} normal, {len(anomaly)} anomaly images available")
    return assign_split(items)


def build_d5_medical():
    """D3: DermaMNIST — skin lesion anomaly detection (normal=melanocytic nevi, anomaly=melanoma).

    Uses MedMNIST DermaMNIST 224x224 dataset (ISIC skin dermoscopy images).
    Compatible with BMAD/UniMMAD medical AD evaluation protocol.
    Normal = class 5 (melanocytic_nevi, most common benign lesion).
    Anomaly = class 4 (melanoma, malignant).
    """
    import numpy as np
    from PIL import Image

    DERMAMNIST_ROOT = Path(_ROOT + "/benchmark/data/MedMNIST")
    npz_path = DERMAMNIST_ROOT / "dermamnist_224.npz"
    if not npz_path.exists():
        print("  [WARN] D3: DermaMNIST not found. Run: pip install medmnist && download.")
        return []

    data = np.load(str(npz_path))
    img_dir = DERMAMNIST_ROOT / "dermamnist_images"
    img_dir.mkdir(exist_ok=True)

    # Class 5 = melanocytic_nevi (normal/benign), Class 4 = melanoma (anomaly/malignant)
    NORMAL_CLASS = 5
    ANOMALY_CLASS = 4

    normal_imgs = []
    anomaly_imgs = []

    # Use train + test splits for maximum coverage
    for split_name in ["train", "test", "val"]:
        images = data[f"{split_name}_images"]
        labels = data[f"{split_name}_labels"].flatten()
        for i in range(len(images)):
            cls = int(labels[i])
            if cls not in (NORMAL_CLASS, ANOMALY_CLASS):
                continue
            img_path = img_dir / f"derm_{split_name}_{i:05d}.jpg"
            if not img_path.exists():
                Image.fromarray(images[i]).save(str(img_path))
            if cls == NORMAL_CLASS:
                normal_imgs.append(str(img_path))
            else:
                anomaly_imgs.append(str(img_path))

    if not normal_imgs or not anomaly_imgs:
        print(f"  [WARN] D3: Insufficient DermaMNIST images (normal={len(normal_imgs)}, anomaly={len(anomaly_imgs)})")
        return []

    random.shuffle(normal_imgs)
    random.shuffle(anomaly_imgs)

    # Use up to 10 normal images as reference pool
    refs_pool = normal_imgs[:20]
    normal_imgs = normal_imgs[:90]
    anomaly_imgs = anomaly_imgs[:90]

    print(f"  D3: {len(normal_imgs)} normal (nevi), {len(anomaly_imgs)} anomaly (melanoma) — DermaMNIST")

    items = []
    for i, img in enumerate(normal_imgs):
        refs = random.sample(refs_pool, min(10, len(refs_pool)))
        items.append({
            "item_id": f"D3_{i:04d}",
            "domain": "medical",
            "domain_code": "D3",
            "query_path": img,
            "ref_paths": refs,
            "label": 0,
            "anomaly_type": None,
            "source_dataset": "DermaMNIST",
            "category": "skin_lesion",
            "split": None,
        })
    for j, img in enumerate(anomaly_imgs):
        refs = random.sample(refs_pool, min(10, len(refs_pool)))
        items.append({
            "item_id": f"D3_{90+j:04d}",
            "domain": "medical",
            "domain_code": "D3",
            "query_path": img,
            "ref_paths": refs,
            "label": 1,
            "anomaly_type": "melanoma",
            "source_dataset": "DermaMNIST",
            "category": "skin_lesion",
            "split": None,
        })

    for i, item in enumerate(items):
        item["item_id"] = f"D3_{i:04d}"
    return assign_split(items)


def build_d6_remote_sensing():
    """D4: LEVIR-CD+ — satellite building change detection (anomalous=changed/damaged buildings).

    Uses pyarrow to directly read parquet files — avoids datasets library compatibility issues.
    Note: LEVIR-CD+ has ~79 no-change and ~906 changed samples total; uses all 79 normal + 79 anomaly.
    """
    if not LEVIR_ROOT.exists():
        print("  [WARN] D4: LEVIR-CD not found. Run: bash benchmark/scripts/download_datasets.sh xbd")
        return []

    try:
        import pyarrow.parquet as pq
        import numpy as np
        from PIL import Image
        import io
    except ImportError:
        print("  [WARN] D4: pyarrow or PIL not available")
        return []

    parquet_files = sorted(LEVIR_ROOT.rglob("*.parquet"))
    if not parquet_files:
        print("  [WARN] D4: LEVIR-CD parquet files not found (still downloading?)")
        return []

    img_dir = LEVIR_ROOT / "extracted_images"
    img_dir.mkdir(exist_ok=True)

    normal_samples = []
    anomaly_samples = []
    global_idx = 0

    for pf in parquet_files:
        try:
            table = pq.read_table(str(pf))
        except Exception:
            continue
        for i in range(len(table)):
            row = table.slice(i, 1).to_pydict()
            try:
                mask_bytes = row["mask"][0]["bytes"]
                img2_bytes = row["image2"][0]["bytes"]
                img1_bytes = row["image1"][0]["bytes"]
            except (KeyError, IndexError, TypeError):
                continue

            mask_arr = np.array(Image.open(io.BytesIO(mask_bytes)))
            has_change = bool(mask_arr.max() > 0)

            img2_path = img_dir / f"img2_{global_idx:04d}.png"
            img1_path = img_dir / f"img1_{global_idx:04d}.png"
            if not img2_path.exists():
                try:
                    Image.open(io.BytesIO(img2_bytes)).save(str(img2_path))
                except Exception:
                    global_idx += 1
                    continue
            if not img1_path.exists():
                try:
                    Image.open(io.BytesIO(img1_bytes)).save(str(img1_path))
                except Exception:
                    pass

            entry = {"img1": str(img1_path), "img2": str(img2_path), "has_change": has_change}
            if has_change:
                anomaly_samples.append(entry)
            else:
                normal_samples.append(entry)
            global_idx += 1

        # Stop early if we have enough of both classes
        if len(normal_samples) >= 90 and len(anomaly_samples) >= 90:
            break

    if not normal_samples:
        print(f"  [WARN] D4: No no-change LEVIR-CD samples found")
        return []

    random.shuffle(normal_samples); random.shuffle(anomaly_samples)
    # Balance using however many normal we have (may be <90)
    n_balanced = min(len(normal_samples), len(anomaly_samples), 90)
    normal_samples = normal_samples[:n_balanced]
    anomaly_samples = anomaly_samples[:n_balanced]

    print(f"  D4: {len(normal_samples)} no-change, {len(anomaly_samples)} changed images (LEVIR-CD+)")

    items = []
    for i, s in enumerate(normal_samples):
        items.append({
            "item_id": f"D4_{i:04d}",
            "domain": "remote_sensing",
            "domain_code": "D4",
            "query_path": s["img2"],
            "ref_paths": [s["img1"]],
            "label": 0,
            "anomaly_type": None,
            "source_dataset": "LEVIR-CD+",
            "category": "building",
            "split": None,
        })
    for j, s in enumerate(anomaly_samples):
        items.append({
            "item_id": f"D4_{n_balanced+j:04d}",
            "domain": "remote_sensing",
            "domain_code": "D4",
            "query_path": s["img2"],
            "ref_paths": [s["img1"]],
            "label": 1,
            "anomaly_type": "building_change",
            "source_dataset": "LEVIR-CD+",
            "category": "building",
            "split": None,
        })

    for i, item in enumerate(items):
        item["item_id"] = f"D4_{i:04d}"
    return assign_split(items)


def build_d7_road():
    """D7: RoadAnomaly21 — road scene anomaly detection (anomalous=unexpected object on road)."""
    if not ROAD_ROOT.exists():
        print("  [WARN] D7: RoadAnomaly21 not found. Run: bash benchmark/scripts/download_datasets.sh road")
        return []

    import numpy as np

    # Collect anomalous images (all RoadAnomaly21 images have road anomalies)
    img_dir = ROAD_ROOT / "images"
    anomaly_imgs = sorted(img_dir.glob("*.jpg")) + sorted(img_dir.glob("*.png")) + sorted(img_dir.glob("*.webp"))
    random.shuffle(anomaly_imgs)
    anomaly_imgs = anomaly_imgs[:90]

    # Collect normal road images from BDD100K or RoadObstacle21
    normal_imgs = []
    bdd_img_dirs = [BDD_ROOT / "val" / "images", BDD_ROOT / "validation" / "images",
                    BDD_ROOT]
    for bdd_dir in bdd_img_dirs:
        if bdd_dir.exists():
            imgs = sorted(bdd_dir.rglob("*.jpg")) + sorted(bdd_dir.rglob("*.png"))
            normal_imgs.extend(imgs)
    random.shuffle(normal_imgs)
    normal_imgs = normal_imgs[:90]

    if not normal_imgs:
        print("  [WARN] D7: No normal road images found (BDD100K not downloaded). Using RoadObstacle21 as anomaly-only.")
        # Can't build balanced manifest without normal images
        return []

    items = []
    item_idx = 0
    # Reference pool: all normal images (each query gets a DIFFERENT random sample)
    ref_pool = [str(p) for p in normal_imgs]

    for img in normal_imgs:
        # Sample refs excluding self
        candidates = [r for r in ref_pool if r != str(img)]
        refs = random.sample(candidates, min(10, len(candidates)))
        items.append({
            "item_id": f"D7_{item_idx:04d}",
            "domain": "road",
            "domain_code": "D7",
            "query_path": str(img),
            "ref_paths": refs,
            "label": 0,
            "anomaly_type": None,
            "source_dataset": "BDD100K",
            "category": "road_scene",
            "split": None,
        })
        item_idx += 1

    for img in anomaly_imgs:
        # Determine anomaly type from filename (e.g. cow0000.jpg → animal)
        stem = img.stem
        anomaly_class = "road_obstacle"
        for keyword, atype in [("cow", "animal"), ("zebra", "animal"), ("leopard", "animal"),
                                 ("boat", "vehicle_on_road"), ("carton", "debris"),
                                 ("validation", "road_obstacle")]:
            if keyword in stem.lower():
                anomaly_class = atype
                break
        refs = random.sample(ref_pool, min(10, len(ref_pool)))
        items.append({
            "item_id": f"D7_{item_idx:04d}",
            "domain": "road",
            "domain_code": "D7",
            "query_path": str(img),
            "ref_paths": refs,
            "label": 1,
            "anomaly_type": anomaly_class,
            "source_dataset": "RoadAnomaly21",
            "category": "road_scene",
            "split": None,
        })
        item_idx += 1

    # Balance
    normal_items = [x for x in items if x["label"] == 0][:90]
    anomaly_items = [x for x in items if x["label"] == 1][:90]
    items = normal_items + anomaly_items
    for i, item in enumerate(items):
        item["item_id"] = f"D7_{i:04d}"
    print(f"  D7: {len(normal_items)} normal road, {len(anomaly_items)} anomaly road images")
    return assign_split(items)


def extract_avenue_frames(output_dir: Path, fps=1, max_frames_per_video=30):
    """Extract frames from Avenue Dataset AVI videos using OpenCV."""
    import cv2

    output_dir.mkdir(parents=True, exist_ok=True)
    video_dir = AVENUE_ROOT / "testing_videos"
    normal_dir = AVENUE_ROOT / "training_videos"

    extracted = {"normal": [], "anomaly": []}

    # Training videos = normal activity (no anomalies annotated)
    if normal_dir.exists():
        for vid in sorted(normal_dir.glob("*.avi")):
            cap = cv2.VideoCapture(str(vid))
            frame_count = 0
            saved = 0
            while saved < max_frames_per_video:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_count % int(cap.get(cv2.CAP_PROP_FPS) or 25) == 0:
                    fname = output_dir / f"normal_{vid.stem}_{frame_count:05d}.jpg"
                    if not fname.exists():
                        cv2.imwrite(str(fname), frame)
                    extracted["normal"].append(fname)
                    saved += 1
                frame_count += 1
            cap.release()

    # Testing videos = anomalous periods
    if video_dir.exists():
        for vid in sorted(video_dir.glob("*.avi")):
            cap = cv2.VideoCapture(str(vid))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_count = 0
            saved = 0
            while saved < max_frames_per_video:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_count % int(cap.get(cv2.CAP_PROP_FPS) or 25) == 0:
                    fname = output_dir / f"anomaly_{vid.stem}_{frame_count:05d}.jpg"
                    if not fname.exists():
                        cv2.imwrite(str(fname), frame)
                    extracted["anomaly"].append(fname)
                    saved += 1
                frame_count += 1
            cap.release()

    return extracted


def build_d8_surveillance():
    """D8: Avenue — surveillance video anomaly detection (anomalous=abnormal pedestrian behavior)."""
    if not AVENUE_ROOT.exists():
        print("  [WARN] D8: Avenue dataset not found. Run: bash benchmark/scripts/download_datasets.sh avenue")
        return []

    frames_dir = Path(_ROOT + "/benchmark/data/Avenue/frames")

    # Check if frames already extracted
    existing_normal = sorted(frames_dir.glob("normal_*.jpg")) if frames_dir.exists() else []
    existing_anomaly = sorted(frames_dir.glob("anomaly_*.jpg")) if frames_dir.exists() else []

    if len(existing_normal) < 10 or len(existing_anomaly) < 10:
        print("  Extracting Avenue video frames (this may take a moment)...")
        extracted = extract_avenue_frames(frames_dir, max_frames_per_video=20)
        existing_normal = extracted["normal"]
        existing_anomaly = extracted["anomaly"]

    if not existing_normal or not existing_anomaly:
        print("  [WARN] D8: Could not extract Avenue frames")
        return []

    random.shuffle(existing_normal); random.shuffle(existing_anomaly)
    normal_imgs = existing_normal[:90]
    anomaly_imgs = existing_anomaly[:90]

    items = []
    item_idx = 0
    refs = [str(p) for p in normal_imgs[:10]]

    for img in normal_imgs:
        items.append({
            "item_id": f"D8_{item_idx:04d}",
            "domain": "surveillance",
            "domain_code": "D8",
            "query_path": str(img),
            "ref_paths": refs,
            "label": 0,
            "anomaly_type": None,
            "source_dataset": "Avenue",
            "category": "pedestrian_scene",
            "split": None,
        })
        item_idx += 1

    for img in anomaly_imgs:
        items.append({
            "item_id": f"D8_{item_idx:04d}",
            "domain": "surveillance",
            "domain_code": "D8",
            "query_path": str(img),
            "ref_paths": refs,
            "label": 1,
            "anomaly_type": "abnormal_behavior",
            "source_dataset": "Avenue",
            "category": "pedestrian_scene",
            "split": None,
        })
        item_idx += 1

    normal_items = [x for x in items if x["label"] == 0][:90]
    anomaly_items = [x for x in items if x["label"] == 1][:90]
    items = normal_items + anomaly_items
    for i, item in enumerate(items):
        item["item_id"] = f"D8_{i:04d}"
    print(f"  D8: {len(normal_items)} normal frames, {len(anomaly_items)} anomaly frames")
    return assign_split(items)


def build_placeholder_domain(code, name, source, n=180):
    """Placeholder for domains not yet downloaded — returns empty list with a warning."""
    print(f"  [WARN] {code} ({name}) — dataset '{source}' not found. Run download script first.")
    return []


VISA_ROOT = Path(_ROOT + "/external_data/MMAD/VisA")
LOCO_ROOT = Path(_ROOT + "/external_data/MMAD/MVTec-LOCO")
MVTEC3D_ROOT = Path(_ROOT + "/benchmark/data/MVTec3D")
BRAIN_ROOT = Path(_ROOT + "/benchmark/data/BMAD/Brain_AD/BraTS2021_slice")
LIVER_ROOT = Path(_ROOT + "/benchmark/data/BMAD/Liver_AD/hist_DIY")
HYPER_ROOT = Path(_ROOT + "/benchmark/data/HyperKvasir")


def build_d10_visa():
    """D10: VisA — 12-category industrial anomaly detection."""
    if not VISA_ROOT.exists():
        print("  [WARN] D10: VisA not found")
        return []

    items = []
    item_idx = 0
    for cat in sorted(VISA_ROOT.iterdir()):
        if not cat.is_dir():
            continue
        train_good = cat / "train" / "good"
        refs = []
        if train_good.exists():
            ref_imgs = sorted(train_good.glob("*.png")) + sorted(train_good.glob("*.JPG"))
            refs = [str(p) for p in random.sample(ref_imgs, min(10, len(ref_imgs)))]

        test_root = cat / "test"
        if not test_root.exists():
            continue

        good_dir = test_root / "good"
        if good_dir.exists():
            normal_imgs = sorted(good_dir.glob("*.png")) + sorted(good_dir.glob("*.JPG"))
            random.shuffle(normal_imgs)
            for img in normal_imgs[:12]:
                items.append({
                    "item_id": f"D10_{item_idx:04d}",
                    "domain": "industrial_visa",
                    "domain_code": "D10",
                    "query_path": str(img),
                    "ref_paths": refs,
                    "label": 0,
                    "anomaly_type": None,
                    "source_dataset": "VisA",
                    "category": cat.name,
                    "split": None,
                })
                item_idx += 1

        for defect_dir in sorted(test_root.iterdir()):
            if defect_dir.name == "good" or not defect_dir.is_dir():
                continue
            imgs = sorted(defect_dir.glob("*.png")) + sorted(defect_dir.glob("*.JPG"))
            random.shuffle(imgs)
            for img in imgs[:12]:
                items.append({
                    "item_id": f"D10_{item_idx:04d}",
                    "domain": "industrial_visa",
                    "domain_code": "D10",
                    "query_path": str(img),
                    "ref_paths": refs,
                    "label": 1,
                    "anomaly_type": "defect",
                    "source_dataset": "VisA",
                    "category": cat.name,
                    "split": None,
                })
                item_idx += 1

    normal = [x for x in items if x["label"] == 0]
    anomaly = [x for x in items if x["label"] == 1]
    random.shuffle(normal); random.shuffle(anomaly)
    items = normal[:90] + anomaly[:90]
    for i, item in enumerate(items):
        item["item_id"] = f"D10_{i:04d}"
    print(f"  D10: {min(len(normal),90)} normal, {min(len(anomaly),90)} anomaly (VisA, {len(set(x['category'] for x in items))} categories)")
    return assign_split(items)


def build_d11_mvtec3d():
    """D11: MVTec-3D — 3D product anomaly detection (RGB views only)."""
    if not MVTEC3D_ROOT.exists():
        print("  [WARN] D11: MVTec-3D not found. Need to download RGB images.")
        return []

    items = []
    item_idx = 0
    for cat in sorted(MVTEC3D_ROOT.iterdir()):
        if not cat.is_dir():
            continue
        train_good = cat / "train" / "good" / "rgb"
        if not train_good.exists():
            train_good = cat / "train" / "good"
        refs = []
        if train_good.exists():
            ref_imgs = sorted(train_good.glob("*.png")) + sorted(train_good.glob("*.tiff"))
            refs = [str(p) for p in random.sample(ref_imgs, min(10, len(ref_imgs)))]

        test_root = cat / "test"
        if not test_root.exists():
            continue

        good_rgb = test_root / "good" / "rgb"
        if not good_rgb.exists():
            good_rgb = test_root / "good"
        if good_rgb.exists():
            normal_imgs = sorted(good_rgb.glob("*.png")) + sorted(good_rgb.glob("*.tiff"))
            random.shuffle(normal_imgs)
            for img in normal_imgs[:15]:
                items.append({
                    "item_id": f"D11_{item_idx:04d}",
                    "domain": "industrial_3d",
                    "domain_code": "D11",
                    "query_path": str(img),
                    "ref_paths": refs,
                    "label": 0,
                    "anomaly_type": None,
                    "source_dataset": "MVTec-3D",
                    "category": cat.name,
                    "split": None,
                })
                item_idx += 1

        for defect_dir in sorted(test_root.iterdir()):
            if defect_dir.name == "good" or not defect_dir.is_dir():
                continue
            rgb_dir = defect_dir / "rgb"
            if not rgb_dir.exists():
                rgb_dir = defect_dir
            imgs = sorted(rgb_dir.glob("*.png")) + sorted(rgb_dir.glob("*.tiff"))
            random.shuffle(imgs)
            for img in imgs[:15]:
                items.append({
                    "item_id": f"D11_{item_idx:04d}",
                    "domain": "industrial_3d",
                    "domain_code": "D11",
                    "query_path": str(img),
                    "ref_paths": refs,
                    "label": 1,
                    "anomaly_type": "defect",
                    "source_dataset": "MVTec-3D",
                    "category": cat.name,
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
        item["item_id"] = f"D11_{i:04d}"
    print(f"  D11: {min(len(normal),90)} normal, {min(len(anomaly),90)} anomaly (MVTec-3D RGB)")
    return assign_split(items)


def build_d9_loco():
    """D9: MVTec-LOCO — logical + structural anomaly detection."""
    if not LOCO_ROOT.exists():
        print("  [WARN] D9: MVTec-LOCO not found")
        return []

    items = []
    item_idx = 0
    for cat in sorted(LOCO_ROOT.iterdir()):
        if not cat.is_dir():
            continue
        # Refs from train/good (same category)
        train_good = cat / "train" / "good"
        refs = []
        if train_good.exists():
            ref_imgs = sorted(train_good.glob("*.png")) + sorted(train_good.glob("*.jpg"))
            refs = [str(p) for p in random.sample(ref_imgs, min(10, len(ref_imgs)))]

        test_root = cat / "test"
        if not test_root.exists():
            continue

        # Normal images
        good_dir = test_root / "good"
        if good_dir.exists():
            normal_imgs = sorted(good_dir.glob("*.png"))
            random.shuffle(normal_imgs)
            for img in normal_imgs[:20]:
                items.append({
                    "item_id": f"D9_{item_idx:04d}",
                    "domain": "logical",
                    "domain_code": "D9",
                    "query_path": str(img),
                    "ref_paths": refs,
                    "label": 0,
                    "anomaly_type": None,
                    "source_dataset": "MVTec-LOCO",
                    "category": cat.name,
                    "split": None,
                })
                item_idx += 1

        # Anomaly images (both structural and logical)
        for defect_dir in sorted(test_root.iterdir()):
            if defect_dir.name == "good" or not defect_dir.is_dir():
                continue
            anom_type = defect_dir.name  # "structural_anomalies" or "logical_anomalies"
            imgs = sorted(defect_dir.glob("*.png"))
            random.shuffle(imgs)
            for img in imgs[:20]:
                items.append({
                    "item_id": f"D9_{item_idx:04d}",
                    "domain": "logical",
                    "domain_code": "D9",
                    "query_path": str(img),
                    "ref_paths": refs,
                    "label": 1,
                    "anomaly_type": anom_type,
                    "source_dataset": "MVTec-LOCO",
                    "category": cat.name,
                    "split": None,
                })
                item_idx += 1

    normal = [x for x in items if x["label"] == 0]
    anomaly = [x for x in items if x["label"] == 1]
    random.shuffle(normal); random.shuffle(anomaly)
    items = normal[:90] + anomaly[:90]
    for i, item in enumerate(items):
        item["item_id"] = f"D9_{i:04d}"
    print(f"  D9: {min(len(normal),90)} normal, {min(len(anomaly),90)} anomaly (MVTec-LOCO)")
    return assign_split(items)


def _build_bmad_domain(domain_code, domain_name, source_dataset, category, root, max_per_class=90):
    """Generic builder for BMAD-style datasets (good/Ungood folder structure)."""
    if not root.exists():
        print(f"  [WARN] {domain_code}: {source_dataset} not found at {root}")
        return []

    train_good = root / "train" / "good"
    if not train_good.exists():
        # Try img subfolder
        train_good = root / "train" / "good" / "img" if (root / "train" / "good" / "img").exists() else root / "train" / "good"

    # Collect refs from training set
    ref_pool = []
    if train_good.exists():
        ref_pool = sorted(str(p) for p in train_good.glob("*.png"))
        random.shuffle(ref_pool)

    # Test set
    test_good_dir = root / "test" / "good" / "img" if (root / "test" / "good" / "img").exists() else root / "test" / "good"
    test_bad_dir = root / "test" / "Ungood" / "img" if (root / "test" / "Ungood" / "img").exists() else root / "test" / "ungood" / "img" if (root / "test" / "ungood" / "img").exists() else root / "test" / "Ungood"

    normal_imgs = sorted(str(p) for p in test_good_dir.glob("*.png")) if test_good_dir.exists() else []
    anomaly_imgs = sorted(str(p) for p in test_bad_dir.glob("*.png")) if test_bad_dir.exists() else []
    random.shuffle(normal_imgs); random.shuffle(anomaly_imgs)
    normal_imgs = normal_imgs[:max_per_class]
    anomaly_imgs = anomaly_imgs[:max_per_class]

    if not normal_imgs or not anomaly_imgs:
        print(f"  [WARN] {domain_code}: insufficient images (normal={len(normal_imgs)}, anomaly={len(anomaly_imgs)})")
        return []

    items = []
    for i, img in enumerate(normal_imgs):
        refs = random.sample(ref_pool, min(10, len(ref_pool))) if ref_pool else []
        items.append({
            "item_id": f"{domain_code}_{i:04d}",
            "domain": domain_name,
            "domain_code": domain_code,
            "query_path": img,
            "ref_paths": refs,
            "label": 0,
            "anomaly_type": None,
            "source_dataset": source_dataset,
            "category": category,
            "split": None,
        })
    for j, img in enumerate(anomaly_imgs):
        refs = random.sample(ref_pool, min(10, len(ref_pool))) if ref_pool else []
        items.append({
            "item_id": f"{domain_code}_{len(normal_imgs)+j:04d}",
            "domain": domain_name,
            "domain_code": domain_code,
            "query_path": img,
            "ref_paths": refs,
            "label": 1,
            "anomaly_type": "pathology",
            "source_dataset": source_dataset,
            "category": category,
            "split": None,
        })

    for i, item in enumerate(items):
        item["item_id"] = f"{domain_code}_{i:04d}"
    print(f"  {domain_code}: {len(normal_imgs)} normal, {len(anomaly_imgs)} anomaly — {source_dataset}")
    return assign_split(items)


def build_d5b_brain():
    return _build_bmad_domain("D3b", "medical_brain", "BraTS2021", "brain_mri", BRAIN_ROOT)

def build_d5c_liver():
    return _build_bmad_domain("D3c", "medical_liver", "BMAD-Liver", "liver_ct", LIVER_ROOT)

def build_d5d_colon():
    """D3d: Hyper-Kvasir — colon endoscopy anomaly detection."""
    labeled_dir = HYPER_ROOT / "labeled-images"
    if not labeled_dir.exists():
        # Try to extract
        zip_path = HYPER_ROOT / "hyper-kvasir-labeled-images.zip"
        if zip_path.exists() and zip_path.stat().st_size > 100_000_000:
            import zipfile
            print("  Extracting Hyper-Kvasir...")
            try:
                with zipfile.ZipFile(str(zip_path), 'r') as zf:
                    zf.extractall(str(HYPER_ROOT))
            except Exception as e:
                print(f"  [WARN] D3d: Failed to extract Hyper-Kvasir: {e}")
                return []
            labeled_dir = HYPER_ROOT / "labeled-images"
        if not labeled_dir.exists():
            # Try alternative paths
            for candidate in HYPER_ROOT.iterdir():
                if candidate.is_dir() and 'label' in candidate.name.lower():
                    labeled_dir = candidate
                    break
    if not labeled_dir.exists():
        print(f"  [WARN] D3d: Hyper-Kvasir labeled-images not found")
        return []

    # Hyper-Kvasir structure: labeled-images/lower-gi-tract/pathological-findings/... and .../normal/...
    # Normal: "normal-cecum", "normal-z-line", "normal-pylorus" etc.
    # Anomaly for AD: polyps, ulcerative-colitis, etc.
    normal_imgs = []
    anomaly_imgs = []

    for root_dir, dirs, files in os.walk(str(labeled_dir)):
        for f in files:
            if not f.lower().endswith(('.jpg', '.png', '.jpeg')):
                continue
            path = os.path.join(root_dir, f)
            # Classify based on folder name
            folder = os.path.basename(root_dir).lower()
            if 'normal' in folder or 'z-line' in folder or 'cecum' in folder or 'pylorus' in folder or 'retroflex' in folder:
                normal_imgs.append(path)
            elif 'polyp' in folder or 'cancer' in folder or 'ulcer' in folder or 'tumor' in folder or 'esophagitis' in folder:
                anomaly_imgs.append(path)

    random.shuffle(normal_imgs); random.shuffle(anomaly_imgs)
    if not normal_imgs or not anomaly_imgs:
        print(f"  [WARN] D3d: Insufficient Hyper-Kvasir images (normal={len(normal_imgs)}, anomaly={len(anomaly_imgs)})")
        return []

    ref_pool = normal_imgs[:20]
    normal_imgs = normal_imgs[:90]
    anomaly_imgs = anomaly_imgs[:90]

    items = []
    for i, img in enumerate(normal_imgs):
        refs = random.sample(ref_pool, min(10, len(ref_pool)))
        items.append({
            "item_id": f"D3d_{i:04d}", "domain": "medical_colon", "domain_code": "D3d",
            "query_path": img, "ref_paths": refs, "label": 0, "anomaly_type": None,
            "source_dataset": "HyperKvasir", "category": "endoscopy", "split": None,
        })
    for j, img in enumerate(anomaly_imgs):
        refs = random.sample(ref_pool, min(10, len(ref_pool)))
        items.append({
            "item_id": f"D3d_{90+j:04d}", "domain": "medical_colon", "domain_code": "D3d",
            "query_path": img, "ref_paths": refs, "label": 1, "anomaly_type": "pathology",
            "source_dataset": "HyperKvasir", "category": "endoscopy", "split": None,
        })
    for i, item in enumerate(items):
        item["item_id"] = f"D3d_{i:04d}"
    print(f"  D3d: {len(normal_imgs)} normal, {len(anomaly_imgs)} anomaly — HyperKvasir")
    return assign_split(items)


def build_all():
    all_items = []
    domain_stats = {}

    print("Building D1: Industrial (MVTec-AD)...")
    d1 = build_d1_industrial()
    all_items.extend(d1)
    domain_stats["D1"] = len(d1)
    save_domain(d1, "D1_industrial")

    print("Building D5: Retail (GoodsAD)...")
    d2 = build_d2_retail()
    all_items.extend(d2)
    domain_stats["D5"] = len(d2)
    save_domain(d2, "D5_retail")

    print("Building D2: Screening (PIDray)...")
    d3 = build_d3_screening()
    all_items.extend(d3)
    domain_stats["D2"] = len(d3)
    if d3:
        save_domain(d3, "D2_screening")

    print("Building D6: Maintenance (SDNET2018)...")
    d4 = build_d4_maintenance()
    all_items.extend(d4)
    domain_stats["D6"] = len(d4)
    if d4:
        save_domain(d4, "D6_maintenance")

    print("Building D3: Medical (CheXpert)...")
    d5 = build_d5_medical()
    all_items.extend(d5)
    domain_stats["D3"] = len(d5)
    if d5:
        save_domain(d5, "D3_medical")

    print("Building D4: Remote Sensing (LEVIR-CD+)...")
    d6 = build_d6_remote_sensing()
    all_items.extend(d6)
    domain_stats["D4"] = len(d6)
    if d6:
        save_domain(d6, "D4_remote_sensing")

    print("Building D7: Road (RoadAnomaly21 + BDD100K)...")
    d7 = build_d7_road()
    all_items.extend(d7)
    domain_stats["D7"] = len(d7)
    if d7:
        save_domain(d7, "D7_road")

    print("Building D8: Surveillance (Avenue)...")
    d8 = build_d8_surveillance()
    all_items.extend(d8)
    domain_stats["D8"] = len(d8)
    if d8:
        save_domain(d8, "D8_surveillance")

    print("Building D9: Logical Anomaly (MVTec-LOCO)...")
    d9 = build_d9_loco()
    all_items.extend(d9)
    domain_stats["D9"] = len(d9)
    if d9:
        save_domain(d9, "D9_logical")

    print("Building D10: Industrial/VisA...")
    d10 = build_d10_visa()
    all_items.extend(d10)
    domain_stats["D10"] = len(d10)
    if d10:
        save_domain(d10, "D10_visa")

    print("Building D11: Industrial/MVTec-3D...")
    d11 = build_d11_mvtec3d()
    all_items.extend(d11)
    domain_stats["D11"] = len(d11)
    if d11:
        save_domain(d11, "D11_mvtec3d")

    print("Building D3b: Medical/Brain (BraTS2021)...")
    d5b = build_d5b_brain()
    all_items.extend(d5b)
    domain_stats["D3b"] = len(d5b)
    if d5b:
        save_domain(d5b, "D3b_brain")

    print("Building D3c: Medical/Liver (BMAD-Liver)...")
    d5c = build_d5c_liver()
    all_items.extend(d5c)
    domain_stats["D3c"] = len(d5c)
    if d5c:
        save_domain(d5c, "D3c_liver")

    print("Building D3d: Medical/Colon (HyperKvasir)...")
    d5d = build_d5d_colon()
    all_items.extend(d5d)
    domain_stats["D3d"] = len(d5d)
    if d5d:
        save_domain(d5d, "D3d_colon")

    # Save combined manifest
    with open(MANIFEST_DIR / "full_manifest.json", "w") as f:
        json.dump(all_items, f, indent=2)

    # Save split index
    split_ids = {"calibration": [], "dev": [], "test": []}
    for item in all_items:
        split_ids[item["split"]].append(item["item_id"])
    with open(MANIFEST_DIR / "split_ids.json", "w") as f:
        json.dump(split_ids, f, indent=2)

    print("\n=== Manifest Build Summary ===")
    for code, count in domain_stats.items():
        status = "OK" if count > 0 else "MISSING — needs download"
        print(f"  {code}: {count} items  [{status}]")
    total = sum(v for v in domain_stats.values())
    print(f"\n  Total: {total}/1440 items built")
    print(f"  Manifests saved to: {MANIFEST_DIR}/")
    return all_items


def save_domain(items, name):
    path = MANIFEST_DIR / f"{name}_manifest.json"
    with open(path, "w") as f:
        json.dump(items, f, indent=2)
    print(f"  Saved {len(items)} items → {path}")


if __name__ == "__main__":
    build_all()
