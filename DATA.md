# Data & Weights

AnomalyClaw is evaluated on **CrossDomainVAD-12**, a 12-domain reference-based
visual anomaly detection benchmark assembled from a set of public datasets
(MVTec-AD, MVTec-LOCO, VisA, GoodsAD, BMAD, MedMNIST, RetinalOCT, HyperKvasir,
ISIC, MVTec-3D, PIDray, RoadAnomaly21, LEVIR-CD, BDD100K, …).

We **do not redistribute the raw images** because most of these datasets
prohibit rehosting under their original licenses (notably the MVTec family).
You must download each one from its official upstream — see the per-dataset
table below.

What does ship with the repo (already in `benchmark/`):

- `manifests_v2/` — the CrossDomainVAD-12 split manifests (image lists + labels)
- `retrieval_index/D*_index.npz` — DINOv2 reference-retrieval indices (~13 MB)
- `results/subspacead_*.json`, `results/anomalyvfm_*.json` — per-item expert
  score caches (~3 MB) so you can reproduce the paper's headline numbers
  without rerunning every expert
- `results/v2/v12_passive_{test,test_seedvl,gpt55_test}/` — the v12 agent
  per-domain run outputs that back the paper Table 1 main results
  (Qwen3.5-VL-27B / Seed2.0-lite / GPT-5.5 respectively)

So once you have the raw images in place, `evaluate.py` and `agent_v12.py`
have everything they need.

## Quick start

```bash
# 1. Pick a location for the raw images and export it
export ANOMALYCLAW_DATA=$PWD/benchmark/data
mkdir -p "$ANOMALYCLAW_DATA"

# 2. Follow the per-dataset download table below to populate $ANOMALYCLAW_DATA
#    into the layout shown under "On-disk layout".

# 3. Run the agent (no further data step required)
bash benchmark/scripts/run_v12_passive_test.sh
```

## Manifest path convention

Every image path in `benchmark/manifests_v2/*.json` is stored as
`"{DATA_ROOT}/<relative path>"`. At load time, `infer.resolve_data_path`
replaces `{DATA_ROOT}` with `$ANOMALYCLAW_DATA` (defaulting to
`<repo>/benchmark/data`). So you only need to point `ANOMALYCLAW_DATA` at
your data root once; the manifests stay portable across machines.

## On-disk layout

```
$ANOMALYCLAW_DATA/
├── MMAD/                       # MMAD-bundle: MVTec-AD, MVTec-LOCO, VisA, GoodsAD
│   ├── MVTec-AD/
│   ├── MVTec-LOCO/
│   ├── VisA/
│   └── GoodsAD/
├── MVTec3D/                    # MVTec-3D-AD (RGB views only)
├── BMAD/                       # Brain (BraTS slices), Liver (hist_DIY)
├── HyperKvasir/                # GI endoscopy
├── ISIC/                       # Dermatology
├── MedMNIST/                   # DermaMNIST subset
├── RetinalOCT/                 # retinal OCT slices
├── SDNET2018/                  # bridge / wall cracks
├── PIDray/                     # X-ray contraband
├── RoadAnomaly21/              # road anomalies + obstacles
├── LEVIR-CD/                   # remote-sensing change
├── BDD100K_normal/             # road normals
└── Real3D-AD-RGB/              # Real-3D-AD (D4 industrial 3D)
```

## Per-dataset download

| Folder | Source | License | Redistribution |
|---|---|---|---|
| `MMAD/MVTec-AD`   | MVTec-AD via the MMAD benchmark release | MVTec-AD non-commercial | rehosting prohibited |
| `MMAD/MVTec-LOCO` | MVTec-LOCO via MMAD                     | MVTec-LOCO non-commercial | rehosting prohibited |
| `MMAD/VisA`       | VisA via MMAD                           | Apache-2.0              | rehosting allowed |
| `MMAD/GoodsAD`    | GoodsAD via MMAD                        | dataset-specific        | check upstream |
| `MVTec3D`         | https://www.mvtec.com/company/research/datasets/mvtec-3d-ad | MVTec non-commercial | rehosting prohibited |
| `BMAD`            | https://github.com/DorisBao/BMAD        | BMAD                    | check upstream |
| `HyperKvasir`     | https://datasets.simula.no/hyper-kvasir/ | CC-BY-4.0              | rehosting allowed |
| `ISIC`            | https://www.isic-archive.com/           | CC-0 / per-image varies | mostly allowed |
| `MedMNIST`        | https://medmnist.com/                   | CC-BY-4.0               | rehosting allowed |
| `RetinalOCT`      | OCT2017 (Kermany et al.)                | CC-BY-4.0               | rehosting allowed |
| `SDNET2018`       | https://digitalcommons.usu.edu/all_datasets/48/ | per-source       | check upstream |
| `PIDray`          | https://github.com/bywang2018/security-dataset | research only    | rehosting prohibited |
| `RoadAnomaly21`   | https://segmentmeifyoucan.com/          | per-source              | check upstream |
| `LEVIR-CD`        | https://justchenhao.github.io/LEVIR/    | per-source              | check upstream |
| `BDD100K`         | https://www.vis.xyz/bdd100k/            | BSD-3 + non-commercial  | check upstream |
| `Real3D-AD`       | https://github.com/M-3LAB/Real3D-AD     | per-source              | check upstream |

Each dataset must be obtained under its own terms. We **do not redistribute
raw images**.

## Regenerating the derived caches

If you want to rebuild the bundled artifacts from scratch instead of using
the shipped versions:

### Retrieval index

```bash
# Indices for D6 (Infrastructure) and D7 (Remote Sensing) need to be built
# locally because they were never frozen at release time.
python benchmark/scripts/build_retrieval_index.py
```

The script writes `D*_index.npz` into `benchmark/retrieval_index/`; override
with the `ANOMALYCLAW_INDEX_DIR` env var.

### Expert score caches

For SubspaceAD and AnomalyVFM, clone the upstream baselines into `experts/`
(see `experts/README.md`) and run their inference scripts on the manifests
in `benchmark/manifests_v2/`, then drop the per-item score JSONs at
`benchmark/results/{subspacead,anomalyvfm}_{calibration,test}.json` (same
schema as the shipped versions).
