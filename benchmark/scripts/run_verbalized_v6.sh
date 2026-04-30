#!/bin/bash
# v6: rules in BOTH Direct and refutation branches (vs v5: refutation only).
# Goal: push macro AUROC from v12 passive 0.748 to >=0.778.
set -u
export QWEN_API_BASE=${QWEN_API_BASE:-http://localhost:8200/v1}
export QWEN_MODEL=${QWEN_MODEL:-Qwen3.5-VL-27B}
export QWEN_API_KEY=${QWEN_API_KEY:-EMPTY}
export DESCRIPTOR_MODE=generic

ROOT=/hdd1/jiangxi/AD-Agent/benchmark/results/verbalized
MAN=/hdd1/jiangxi/AD-Agent/benchmark/manifests_v2
SCR=/hdd1/jiangxi/AD-Agent/benchmark/scripts/verbalized_v6.py

VARIANT="${1:-}"
SPLIT="${2:-test}"
if [ -z "$VARIANT" ]; then
    echo "usage: $0 <anchor|l1|l2|l1l2> [test|dev]"
    exit 2
fi

OUT=$ROOT/v6_${SPLIT}_${VARIANT}
mkdir -p "$OUT"

DOMAINS=(D1 D2 D3 D4 D5 D6 D7 D8 D9 D10 D11 D12)
for D in "${DOMAINS[@]}"; do
    M=$(ls "$MAN/${D}_"*.json 2>/dev/null | grep -v domain_config | grep -v split_ids | grep -v full_manifest | head -1)
    O="$OUT/${D}_v6_${VARIANT}.json"
    if [ -f "$O" ] && [ "$(stat -c %s "$O")" -gt 1000 ]; then
        echo "[skip] $D"; continue
    fi
    echo "[v6-${SPLIT}-${VARIANT}] $D ← $M"
    python3 "$SCR" eval \
        --manifest "$M" --split "$SPLIT" --out "$O" --variant "$VARIANT" \
        --backend qwen3 --max_turns 3 --workers 8 --top_k 3 \
        --w_direct 0.5 --w_v9 0.5 \
        --direct_rules --refut_rules --resume \
        || echo "[warn] $D failed"
done
echo "[done] verbalized v6 ${SPLIT} ${VARIANT}"
