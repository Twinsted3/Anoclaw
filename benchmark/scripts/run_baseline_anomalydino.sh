#!/bin/bash
# AnomalyDINO baseline over manifests_v2 test split, all 12 domains.
# Config: DINOv2-ViT-B/14 + edge=448 + k=4 refs + PCA-masking + no rotation.
# Rotation is intentionally disabled because our 12 domains include several
# non-rotation-symmetric modalities (CT, MRI, endoscopy, remote-sensing,
# road) where rotation augmentation distorts the few-shot memory bank.
set -u
REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
GPU=${GPU:-0}
OUT=${REPO_ROOT}/benchmark/results/baselines/anomalydino
MAN=${REPO_ROOT}/benchmark/manifests_v2
mkdir -p "$OUT"

DOMAINS=(D1 D5 D2 D6 D3 D4 D7 D8 D9 D10 D11 D12)
for D in "${DOMAINS[@]}"; do
    M=$(ls "$MAN/${D}_"*.json 2>/dev/null | grep -v domain_config | grep -v split_ids | grep -v full_manifest | head -1)
    O="$OUT/${D}.json"
    if [ -f "$O" ] && [ "$(stat -c %s "$O")" -gt 1000 ]; then
        echo "[skip] $D"; continue
    fi
    echo "[$(date +%H:%M:%S)] AnomalyDINO $D ← $M"
    CUDA_VISIBLE_DEVICES=$GPU python3 \
        ${REPO_ROOT}/benchmark/scripts/baseline_anomalydino.py \
        --manifest "$M" --split test --output "$O" \
        --device cuda:0 --model_name dinov2_vitb14 --smaller_edge_size 448 \
        --max_refs 4 --no_rotation --faiss_on_cpu --resume \
        || echo "[warn] $D failed"
done
echo "[$(date +%H:%M:%S)] AnomalyDINO done."
