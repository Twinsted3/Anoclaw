#!/bin/bash
# IAD-R1 in native zero-shot mode (--n_refs 0): no reference image,
# only the query + the prompt "Are there any defects in the test image?".
# Matches the official inference script's --few_shot_model 0 default.
set -u
GPU=${GPU:-0}
DOMAINS=${DOMAINS:-"D1 D5 D2 D6 D3 D4 D7 D8 D9 D10 D11 D12"}
OUT=/hdd1/jiangxi/AD-Agent/benchmark/results/baselines/iad_r1_zeroshot
MAN=/hdd1/jiangxi/AD-Agent/benchmark/manifests_v2
MODEL='/hdd1/jiangxi/IAD-R1-checkpoints/IAD-R1(Qwen2.5-VL-Instruct-7B)'
mkdir -p "$OUT"

for D in $DOMAINS; do
    M=$(ls "$MAN/${D}_"*.json 2>/dev/null | grep -v domain_config | grep -v split_ids | grep -v full_manifest | head -1)
    O="$OUT/${D}.json"
    if [ -f "$O" ] && [ "$(stat -c %s "$O")" -gt 1000 ]; then
        echo "[skip] $D"; continue
    fi
    echo "[$(date +%H:%M:%S)] IAD-R1-zs $D ← $M (GPU=$GPU)"
    CUDA_VISIBLE_DEVICES=$GPU python3 \
        /hdd1/jiangxi/AD-Agent/benchmark/scripts/baseline_iad_r1.py \
        --manifest "$M" --split test --output "$O" \
        --model_path "$MODEL" --device cuda:0 --n_refs 0 \
        --max_new_tokens 300 \
        --prompt 'Are there any defects in the test image?' \
        --resume \
        || echo "[warn] $D failed"
done
echo "[$(date +%H:%M:%S)] IAD-R1-zs done (GPU=$GPU)."
