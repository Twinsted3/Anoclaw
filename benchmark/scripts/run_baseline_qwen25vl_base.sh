#!/bin/bash
# Base Qwen2.5-VL-7B-Instruct baseline (no IAD fine-tuning).
# Same yes/no logits scoring + 4-shot ensemble as AD-Copilot, so the
# row is directly comparable to AD-Copilot (Qwen2.5-VL + SFT on Chat-AD)
# and IAD-R1 (Qwen2.5-VL + GRPO).
set -u
GPU=${GPU:-0}
DOMAINS=${DOMAINS:-"D1 D5 D2 D6 D3 D4 D7 D8 D9 D10 D11 D12"}
SHOTS=${SHOTS:-4}
OUT=/hdd1/jiangxi/AD-Agent/benchmark/results/baselines/qwen25vl_base_${SHOTS}shot
MAN=/hdd1/jiangxi/AD-Agent/benchmark/manifests_v2
MODEL=${MODEL:-/hdd1/jiangxi/AD-Copilot/Qwen/Qwen2.5-VL-7B-Instruct}
mkdir -p "$OUT"

for D in $DOMAINS; do
    M=$(ls "$MAN/${D}_"*.json 2>/dev/null | grep -v domain_config | grep -v split_ids | grep -v full_manifest | head -1)
    O="$OUT/${D}.json"
    if [ -f "$O" ] && [ "$(stat -c %s "$O")" -gt 1000 ]; then
        echo "[skip] $D"; continue
    fi
    echo "[$(date +%H:%M:%S)] Qwen2.5-VL-7B-base $D ← $M (GPU=$GPU, shots=$SHOTS)"
    CUDA_VISIBLE_DEVICES=$GPU python3 \
        /hdd1/jiangxi/AD-Agent/benchmark/scripts/baseline_ad_copilot.py \
        --manifest "$M" --split test --output "$O" \
        --model_path "$MODEL" --device cuda:0 --n_refs $SHOTS --resume \
        || echo "[warn] $D failed"
done
echo "[$(date +%H:%M:%S)] Qwen2.5-VL-7B-base done (GPU=$GPU)."
