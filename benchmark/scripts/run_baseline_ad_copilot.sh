#!/bin/bash
# AD-Copilot baseline (Qwen2.5-VL-7B fine-tuned for IAD).
# Score = P(Yes) over {Yes,No} from first-token logits in response to a
# yes/no anomaly question with (1 ref, query) image pair.
set -u
GPU=${GPU:-2}
OUT=/hdd1/jiangxi/AD-Agent/benchmark/results/baselines/ad_copilot
MAN=/hdd1/jiangxi/AD-Agent/benchmark/manifests_v2
MODEL=${MODEL:-/hdd1/jiangxi/AD-Copilot/AD-Copilot}
mkdir -p "$OUT"

DOMAINS=(D1 D2 D3 D4 D5 D6 D7 D8 D9 D10 D11 D12)
for D in "${DOMAINS[@]}"; do
    M=$(ls "$MAN/${D}_"*.json 2>/dev/null | grep -v domain_config | grep -v split_ids | grep -v full_manifest | head -1)
    O="$OUT/${D}.json"
    if [ -f "$O" ] && [ "$(stat -c %s "$O")" -gt 1000 ]; then
        echo "[skip] $D"; continue
    fi
    echo "[$(date +%H:%M:%S)] AD-Copilot $D ← $M"
    CUDA_VISIBLE_DEVICES=$GPU python3 \
        /hdd1/jiangxi/AD-Agent/benchmark/scripts/baseline_ad_copilot.py \
        --manifest "$M" --split test --output "$O" \
        --model_path "$MODEL" --device cuda:0 --resume \
        || echo "[warn] $D failed"
done
echo "[$(date +%H:%M:%S)] AD-Copilot done."
