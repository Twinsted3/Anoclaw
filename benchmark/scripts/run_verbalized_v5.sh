#!/bin/bash
# Verbalized v5: re-run +Anchor / +L1 / +L2 / +L1+L2 on test split
# inside the §4 v12 ensemble (parallel-Direct + refutation, alpha=0.5).
# Rules go into refutation only; Direct stays vanilla.
set -u
export QWEN_API_BASE=${QWEN_API_BASE:-http://localhost:8200/v1}
export QWEN_MODEL=${QWEN_MODEL:-Qwen3.5-VL-27B}
export QWEN_API_KEY=${QWEN_API_KEY:-EMPTY}
export DESCRIPTOR_MODE=generic

ROOT=/hdd1/jiangxi/AD-Agent/benchmark/results/verbalized
MAN=/hdd1/jiangxi/AD-Agent/benchmark/manifests_v2
SCR=/hdd1/jiangxi/AD-Agent/benchmark/scripts/verbalized_v5.py

VARIANT="${1:-}"
if [ -z "$VARIANT" ]; then
    echo "usage: $0 <anchor|l1|l2|l1l2>"
    exit 2
fi

OUT=$ROOT/v5_eval_${VARIANT}
mkdir -p "$OUT"

DOMAINS=(D1 D2 D3 D4 D5 D6 D7 D8 D9 D10 D11 D12)
for D in "${DOMAINS[@]}"; do
    M=$(ls "$MAN/${D}_"*.json 2>/dev/null | grep -v domain_config | grep -v split_ids | grep -v full_manifest | head -1)
    O="$OUT/${D}_v5_${VARIANT}.json"
    if [ -f "$O" ] && [ "$(stat -c %s "$O")" -gt 1000 ]; then
        echo "[skip] $D"; continue
    fi
    echo "[v5-eval-${VARIANT}] $D ← $M"
    python3 "$SCR" eval-test \
        --manifest "$M" --out "$O" --variant "$VARIANT" \
        --backend qwen3 --max_turns 3 --workers 8 --top_k 3 \
        --w_direct 0.5 --w_v9 0.5 --resume \
        || echo "[warn] $D failed"
done
echo "[done] verbalized v5 ${VARIANT} all 12 domains"
