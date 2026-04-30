#!/bin/bash
# VisualAD baseline (zero-shot, train_on_visa checkpoint to avoid D1 leakage).
set -u
GPU=${GPU:-1}
OUT=/hdd1/jiangxi/AD-Agent/benchmark/results/baselines/visualad
MAN=/hdd1/jiangxi/AD-Agent/benchmark/manifests_v2
CKPT=/hdd1/jiangxi/AD-Agent/experts/VisualAD/weight/train_on_visa/CLIP.pth
mkdir -p "$OUT"

DOMAINS=(D1 D2 D3 D4 D5 D6 D7 D8 D9 D10 D11 D12)
for D in "${DOMAINS[@]}"; do
    M=$(ls "$MAN/${D}_"*.json 2>/dev/null | grep -v domain_config | grep -v split_ids | grep -v full_manifest | head -1)
    O="$OUT/${D}.json"
    if [ -f "$O" ] && [ "$(stat -c %s "$O")" -gt 1000 ]; then
        echo "[skip] $D"; continue
    fi
    echo "[$(date +%H:%M:%S)] VisualAD $D ← $M"
    CUDA_VISIBLE_DEVICES=$GPU python3 \
        /hdd1/jiangxi/AD-Agent/benchmark/scripts/baseline_visualad.py \
        --manifest "$M" --split test --output "$O" \
        --device cuda:0 --checkpoint "$CKPT" --resume \
        || echo "[warn] $D failed"
done
echo "[$(date +%H:%M:%S)] VisualAD done."
