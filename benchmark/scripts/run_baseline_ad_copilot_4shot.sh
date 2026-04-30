#!/bin/bash
# AD-Copilot 4-shot variant: ensemble P(Yes) across 4 (ref_i,query) passes.
# Sharded across GPUs by domain list (e.g. GPU=0 DOMAINS="D1 D5 D2 D6").
set -u
GPU=${GPU:-0}
DOMAINS=${DOMAINS:-"D1 D5 D2 D6 D3 D4 D7 D8 D9 D10 D11 D12"}
OUT=/hdd1/jiangxi/AD-Agent/benchmark/results/baselines/ad_copilot_4shot
MAN=/hdd1/jiangxi/AD-Agent/benchmark/manifests_v2
MODEL=${MODEL:-/hdd1/jiangxi/AD-Copilot/AD-Copilot}
mkdir -p "$OUT"

for D in $DOMAINS; do
    M=$(ls "$MAN/${D}_"*.json 2>/dev/null | grep -v domain_config | grep -v split_ids | grep -v full_manifest | head -1)
    O="$OUT/${D}.json"
    if [ -f "$O" ] && [ "$(stat -c %s "$O")" -gt 1000 ]; then
        echo "[skip] $D"; continue
    fi
    echo "[$(date +%H:%M:%S)] AD-Copilot-4shot $D ← $M (GPU=$GPU)"
    CUDA_VISIBLE_DEVICES=$GPU python3 \
        /hdd1/jiangxi/AD-Agent/benchmark/scripts/baseline_ad_copilot.py \
        --manifest "$M" --split test --output "$O" \
        --model_path "$MODEL" --device cuda:0 --n_refs 4 --resume \
        || echo "[warn] $D failed"
done
echo "[$(date +%H:%M:%S)] AD-Copilot-4shot done (GPU=$GPU)."
