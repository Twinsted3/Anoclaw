# AnomaClaw Dataset Survey

**Date**: 2026-04-02 (updated)
**Total surveyed**: 24 datasets
**Downloaded**: 18 datasets
**Currently in benchmark**: 5 domains (D1/D2/D4/D5a/D7)
**Target benchmark**: Align with UniMMAD (9 datasets, 3 fields, 12 modalities, 66 classes)

---

## Currently Used (5 Domains)

| Domain | Dataset | Source | Categories | Test Items | Anomaly Definition | Refs |
|--------|---------|--------|------------|------------|-------------------|------|
| D1 Industrial | MVTec-AD | MMAD bundle | 15 (bottle, cable, ...) | 120 (60N+60A) | Surface defect, breakage, contamination | Same-category, k=4 from 10 |
| D2 Retail | GoodsAD | MMAD bundle | 6 (drink_can, food_box, ...) | 120 (60N+60A) | opened, surface_damage, deformation, cap_open | Same-category, k=4 from 10 |
| D4 Maintenance | SDNET2018 | Downloaded | 3 (deck, pavement, wall) | 120 (60N+60A) | Concrete crack | Same-surface, k=4 from 10 |
| D5 Medical | DermaMNIST (ISIC) | MedMNIST pip | 1 (skin_lesion) | 120 (60N+60A) | Melanoma (vs benign nevi) | Random normal, k=4 from 10 |
| D7 Road | BDD100K + RoadAnomaly21 | Downloaded | 1 (road_scene) | 120 (60N+60A) | Road obstacle (animal, vehicle, debris) | Normal road images, k=4 from 10 |

## Downloaded but Excluded

| Dataset | Why Excluded | Size | Path |
|---------|-------------|------|------|
| CheXpert | Label leakage: "normal" images had visible pathology (uncertain labels treated as normal) | 9714 imgs | benchmark/data/CheXpert/ |
| LEVIR-CD+ | Change detection, not anomaly detection (paired img1→img2 temporal comparison) | 158 pairs | benchmark/data/LEVIR-CD/ |
| Avenue | Behavioral anomaly, single-frame insufficient for action recognition | video frames | benchmark/data/Avenue/ |
| PIDray | Only anomalous X-rays, no normal images available for balanced set | ~70 imgs | benchmark/data/PIDray/ |
| UniADRS (visible_light) | All 100 images are anomalous (pixel-level AD dataset, no normal class) | 1.8GB rar | benchmark/data/UniADRS/ |

## Downloaded, Candidate for Future Use

| Dataset | Potential Role | Size | Status | Path |
|---------|---------------|------|--------|------|
| **BMAD-Brain (BraTS2021)** | D5b Medical (brain MRI), compatible with UniMMAD | 383MB zip, extracted | test: 640 good + 3075 ungood, 240x240 RGB | benchmark/data/BMAD/Brain_AD/ |
| BMAD-Chest (RSNA) | Alternative D5 (chest X-ray with clean labels) | 9GB zip | Not extracted | benchmark/data/BMAD/bmad_updated/ |
| BMAD-Histopath (Camelyon16) | New medical domain (histopathology) | 850MB zip | Not extracted | benchmark/data/BMAD/bmad_updated/ |
| BMAD-Liver (BTCV+LiTS) | New medical domain (liver CT) | 38MB zip | Not extracted | benchmark/data/BMAD/bmad_updated/ |
| MVTec-LOCO | Future paper: logical/structural anomaly detection | Available | Not used | MMAD/dataset/MMAD/MVTec-LOCO/ |
| VisA | Additional industrial domain (12 categories) | Available | Not used | MMAD/dataset/MMAD/VisA/ |
| DS-MVTec | MVTec variant | Available | Not used | MMAD/dataset/MMAD/DS-MVTec/ |

## Available on /hdd6 (Not Downloaded to Project)

| Dataset | Notes |
|---------|-------|
| BTAD | Industrial AD |
| Real-IAD | Large-scale real industrial AD |
| MINT-AD | Multi-instance AD |
| MC3D-AD | 3D point cloud AD |
| Dinomaly | DINOv2-based AD framework |
| RAS | Remote sensing |

## Key Lessons Learned

1. **CheXpert**: Binary AD labels ≠ "looks normal to VLM." Uncertain pathology labels (code=2) were treated as normal, but VLMs correctly detected visible abnormalities → systematic false positives
2. **LEVIR-CD+**: Change detection (A→B) is fundamentally different from anomaly detection (normal vs abnormal). Not suitable for AD benchmark
3. **Avenue**: Single-frame behavioral anomaly detection is out of scope for appearance-based VLM methods
4. **UniADRS**: Designed for pixel-level anomaly localization (all images contain anomalies), not binary classification
5. **GoodsAD**: Has rich defect annotations (opened, surface_damage, cap_open, deformation) but manifest mapped them to coarse "other" label — should be preserved

---

## Target Benchmark: UniMMAD Alignment

### UniMMAD Medical Subset (UniMed) — 需要对齐

| Dataset | UniMMAD Key | Train Normal | Test Anomaly | Normal定义 | Anomaly定义 | 我们的状态 |
|---------|-------------|-------------|-------------|-----------|-----------|----------|
| BraTS2021 | BratsAD1K | 1183 | 167 | 正常脑MRI | 脑肿瘤 | ✅ BMAD Brain_AD 已解压 (7500 train, 640+3075 test) |
| Liver CT | LiverAD | 404 | 158 | 正常肝脏CT | 肝肿瘤 | ✅ BMAD Liver_AD 已解压 (1542 train, 833+660 test) |
| Retinal OCT | RetinaAD | 1009 | 270 | 正常视网膜OCT | 视网膜水肿 | ❌ BMAD下载失败(0字节), 需替代源 |
| Hyper-Kvasir | HyperAD | 2020 | 184 | 正常结肠镜 | 结肠肿瘤 | 🔄 下载中 (~1.1GB) |

### 工业+其他域

| Dataset | Categories | 状态 | 备注 |
|---------|-----------|------|------|
| MVTec-AD | 15 | ✅ D1 已用 | 纹理+结构异常 |
| GoodsAD | 6 | ✅ D2 已用 | 商品缺陷(opened/surface_damage等) |
| SDNET2018 | 3 | ✅ D4 已用 | 混凝土裂纹 |
| DermaMNIST | 1 | ✅ D5a 已用 | 皮肤病变(nevi vs melanoma) |
| BDD100K+RA21 | 1 | ✅ D7 已用 | 道路障碍 |
| **MVTec-LOCO** | 5 | ✅ 待构建 | **逻辑异常**(缺件/多件/组装错误), 1000×1700 PNG |
| MVTec-3D | 10 | ❌ 需下载RGB | 3D产品(VLM只用RGB视图) |
| VisA | 12 | ✅ 可用但未用 | 更多工业类别 |
| Eyecandies | 10 | — | UniMMAD用,我们暂不需要 |
| MulSen-AD | 15 | — | 多传感器,需下载 |
