#!/bin/bash
# v2 eval: run one variant across all 12 domains.
# Variants: anchor | l1 | l2 | l1l2
set -u
VARIANT=$1
export QWEN_API_BASE=${QWEN_API_BASE:-http://localhost:8210/v1}
export QWEN_MODEL=Qwen3.5-VL-27B
export QWEN_API_KEY=${QWEN_API_KEY:-EMPTY}

ROOT=/hdd1/jiangxi/AD-Agent
SCR=$ROOT/benchmark/scripts/verbalized_v2.py
MAN=$ROOT/benchmark/manifests_v2
OUT=$ROOT/benchmark/results/verbalized/v2_eval_$VARIANT
mkdir -p "$OUT"
DOMAINS=(D1 D5 D2 D6 D3 D4 D7 D8 D9 D10 D11 D12)

for D in "${DOMAINS[@]}"; do
    M=$(ls "$MAN/${D}_"*.json 2>/dev/null | head -1)
    [ -z "$M" ] && continue
    O="$OUT/${D}_v2_$VARIANT.json"
    if [ -f "$O" ] && [ $(stat -c %s "$O") -gt 1000 ]; then
        echo "[skip] $D $VARIANT"; continue
    fi
    echo "[v2-$VARIANT] $D"
    python3 "$SCR" \
        --manifest "$M" --out "$O" --variant "$VARIANT" \
        --backend qwen3 --max_turns 3 --workers 6 --top_k 3 \
        || echo "[warn] $D $VARIANT failed"
done

echo "[done] v2-$VARIANT"
