# Data & Weights

AnomalyClaw is evaluated on **CrossDomainVAD-12**, a 12-domain reference-based
anomaly detection benchmark assembled from 14 public sources. The raw image
data and pre-computed expert-score caches are released on Hugging Face Hub
because they total ~43 GB of images plus ~2 GB of expert weights.

This file documents how to fetch them.

## Quick start

```bash
# 1. Install the HF CLI (if you don't already have it)
pip install -U huggingface_hub

# 2. Point ANOMALYCLAW_DATA at where you want the data to land
export ANOMALYCLAW_DATA=$PWD/benchmark/data

# 3. One-shot wrapper that pulls everything
bash benchmark/scripts/download_datasets.sh
```

`benchmark/scripts/download_datasets.sh` uses
`huggingface_hub.snapshot_download` to pull the dataset bundle and the
expert-score caches into the expected on-disk layout. In mainland China the
script picks up `HF_ENDPOINT=https://hf-mirror.com` if set.

> **Companion repos (TODO — fill these in once uploaded):**
> - Dataset bundle: `<HF_DATASET_REPO>`
> - Model / expert weights: `<HF_MODEL_REPO>`

Until the HF repos are published, follow the **manual setup** section
below.

## Manifest path convention

Every image path in `benchmark/manifests_v2/*.json` is stored as
`"{DATA_ROOT}/<relative path>"`. At load time, `infer.resolve_data_path`
replaces `{DATA_ROOT}` with `$ANOMALYCLAW_DATA` (defaulting to
`<repo>/benchmark/data`). So you only need to point `ANOMALYCLAW_DATA` at
your data root once; the manifests stay portable.

## Manual setup (per-dataset)

If you want to assemble the data yourself rather than going through the HF
bundle, the on-disk layout is:

```
$ANOMALYCLAW_DATA/
├── MMAD/                       # MMAD-derived: MVTec-AD, MVTec-LOCO, VisA, GoodsAD
│   ├── MVTec-AD/
│   ├── MVTec-LOCO/
│   ├── VisA/
│   └── GoodsAD/
├── MVTec3D/                    # MVTec-3D-AD (RGB only)
├── BMAD/                       # Brain (BraTS slices), Liver (hist_DIY)
├── HyperKvasir/                # GI endoscopy
├── ISIC/                       # Dermatology
├── MedMNIST/                   # DermaMNIST subset
├── RetinalOCT/                 # retinal OCT slices
├── SDNET2018/                  # bridge/wall cracks
├── PIDray/                     # X-ray contraband
├── RoadAnomaly21/              # road anomalies + obstacles
├── LEVIR-CD/                   # remote-sensing change
├── BDD100K_normal/             # road normals
└── Real3D-AD-RGB/              # real-3D-AD (D4)
```

### Source links and licenses

| Folder | Source | License |
|---|---|---|
| `MMAD/MVTec-AD` | MVTec-AD via the MMAD benchmark release | MVTec-AD non-commercial |
| `MMAD/MVTec-LOCO` | MVTec-LOCO via MMAD | MVTec-LOCO non-commercial |
| `MMAD/VisA` | VisA via MMAD | VisA Apache-2.0 |
| `MMAD/GoodsAD` | GoodsAD via MMAD | dataset-specific |
| `MVTec3D` | https://www.mvtec.com/company/research/datasets/mvtec-3d-ad | MVTec non-commercial |
| `BMAD` | https://github.com/DorisBao/BMAD | BMAD license |
| `HyperKvasir` | https://datasets.simula.no/hyper-kvasir/ | CC BY 4.0 |
| `ISIC` | https://www.isic-archive.com/ | CC-0 / per-image varies |
| `MedMNIST` | https://medmnist.com/ | CC BY 4.0 |
| `RetinalOCT` | OCT2017 (Kermany et al.) | CC BY 4.0 |
| `SDNET2018` | https://digitalcommons.usu.edu/all_datasets/48/ | per-source |
| `PIDray` | https://github.com/bywang2018/security-dataset | research only |
| `RoadAnomaly21` | https://segmentmeifyoucan.com/ | per-source |
| `LEVIR-CD` | https://justchenhao.github.io/LEVIR/ | per-source |
| `BDD100K` | https://www.vis.xyz/bdd100k/ | BSD-3 + non-commercial |
| `Real3D-AD` | https://github.com/M-3LAB/Real3D-AD | per-source |

Each dataset must be obtained under its own terms; we **do not redistribute
raw images**.

## Expert score caches

The agent's expert tools (`SubspaceAD`, `AnomalyVFM`) consume per-item
anomaly scores cached as JSON under `benchmark/results/`. The HF model
repo ships these caches so you can reproduce the headline numbers without
rerunning every expert from scratch:

```
benchmark/results/
├── subspacead_calibration.json
├── subspacead_test.json
├── anomalyvfm_calibration.json
└── anomalyvfm_test.json
```

If you want to regenerate them yourself, clone the upstream baselines into
`experts/` (see `experts/README.md`) and run their inference scripts on the
manifests in `benchmark/manifests_v2/`.

## Retrieval index

The DINOv2 reference-retrieval index (`benchmark/retrieval_index/*.npz`) is
small (~13 MB total) and can be rebuilt locally from any normal-only
reference bank:

```bash
python benchmark/scripts/build_retrieval_index.py
```

It will write `D*_index.npz` files into `benchmark/retrieval_index/`
(override with `ANOMALYCLAW_INDEX_DIR`).
