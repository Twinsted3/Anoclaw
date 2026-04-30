#!/bin/bash
# Single-variant eval runner: processes one of {l1, l2, l1l2} across all 12 domains.
# Designed for running 3 variants in parallel (each as its own process).
set -u
VARIANT=$1  # l1 | l2 | l1l2
export QWEN_API_BASE=${QWEN_API_BASE:-http://localhost:8210/v1}
export QWEN_MODEL=Qwen3.5-VL-27B
export QWEN_API_KEY=${QWEN_API_KEY:-EMPTY}

ROOT=/hdd1/jiangxi/AD-Agent
SCR=$ROOT/benchmark/scripts/verbalized_learning.py
MAN=$ROOT/benchmark/manifests_v2
OUT=$ROOT/benchmark/results/verbalized
DOMAINS=(D1 D5 D2 D6 D3 D4 D7 D8 D9 D10 D11 D12)

mkdir -p "$OUT/eval_$VARIANT"
SRCDIR="$OUT/$VARIANT"
[ "$VARIANT" = "l1l2" ] && SRCDIR="$OUT/stack"

for D in "${DOMAINS[@]}"; do
    M=$(ls "$MAN/${D}_"*.json 2>/dev/null | head -1)
    [ -z "$M" ] && continue
    RB=$(ls "$SRCDIR/${D}_"*.json 2>/dev/null | head -1)
    [ -z "$RB" ] && { echo "[skip] $D eval $VARIANT: rulebook missing"; continue; }
    O="$OUT/eval_$VARIANT/${D}_eval_$VARIANT.json"
    if [ -f "$O" ] && [ $(stat -c %s "$O") -gt 1000 ]; then
        echo "[skip] $D $VARIANT eval exists"
        continue
    fi
    echo "[eval-$VARIANT] $D"
    python3 "$SCR" eval-test \
        --manifest "$M" --rulebook "$RB" --out "$O" \
        --backend qwen3 --max_turns 3 --workers 6 \
        || echo "[warn] $D $VARIANT failed"
done

echo "[done] eval-$VARIANT"
