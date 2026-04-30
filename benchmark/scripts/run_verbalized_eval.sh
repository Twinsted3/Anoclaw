#!/bin/bash
# Stage 4: test-split eval for 4 variants × 12 domains.
# Depends on run_verbalized_pipeline.sh having produced:
#   benchmark/results/verbalized/l1/*.json
#   benchmark/results/verbalized/l2/*.json
#   benchmark/results/verbalized/stack/*_l1l2.json
# Plus: an existing Passive v9 test result (any variant) as the baseline.
#
# Variants produced here:
#   eval_l1/     — Passive v9 + L1 rulebook injected
#   eval_l2/     — Passive v9 + L2 rulebook injected
#   eval_l1l2/   — Passive v9 + L1+L2 stacked rulebook injected
# Passive baseline is not re-run; we reuse main-table results.
set -u
export QWEN_API_BASE=${QWEN_API_BASE:-http://localhost:8210/v1}
export QWEN_MODEL=Qwen3.5-VL-27B
export QWEN_API_KEY=${QWEN_API_KEY:-EMPTY}

ROOT=/hdd1/jiangxi/AD-Agent
SCR=$ROOT/benchmark/scripts/verbalized_learning.py
MAN=$ROOT/benchmark/manifests_v2
OUT=$ROOT/benchmark/results/verbalized
DOMAINS=(D1 D5 D2 D6 D3 D4 D7 D8 D9 D10 D11 D12)

for VARIANT in l1 l2 l1l2; do
    mkdir -p "$OUT/eval_$VARIANT"
    SRCDIR="$OUT/$VARIANT"
    if [ "$VARIANT" = "l1l2" ]; then SRCDIR="$OUT/stack"; fi
    for D in "${DOMAINS[@]}"; do
        M=$(ls "$MAN/${D}_"*.json 2>/dev/null | head -1)
        [ -z "$M" ] && continue
        RB=$(ls "$SRCDIR/${D}_"*.json 2>/dev/null | head -1)
        [ -z "$RB" ] && { echo "[skip] $D eval $VARIANT: rulebook missing ($SRCDIR/${D}_*.json)"; continue; }
        O="$OUT/eval_$VARIANT/${D}_eval_$VARIANT.json"
        if [ -f "$O" ] && [ $(stat -c %s "$O") -gt 1000 ]; then
            echo "[skip] $D $VARIANT eval exists"
            continue
        fi
        echo "[eval-$VARIANT] $D  (rulebook=$(basename $RB))"
        python3 "$SCR" eval-test \
            --manifest "$M" \
            --rulebook "$RB" \
            --out "$O" \
            --backend qwen3 \
            --max_turns 3 \
            --workers 6 \
            || echo "[warn] $D $VARIANT failed"
    done
done

echo "=== eval pipeline done ==="
