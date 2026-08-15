#!/bin/bash
# Stage A for v12: Passive v12 (learning_enabled=False) on dev to capture
# v12's v9_rationale + direct_rationale so verbalized_v4 can partition and
# re-learn meta-rules grounded in v12's actual trajectory phrasing.
set -u
REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
export QWEN_API_BASE=${QWEN_API_BASE:-http://localhost:8210/v1}
export QWEN_MODEL=${QWEN_MODEL:-Qwen3.5-VL-27B}
export QWEN_API_KEY=${QWEN_API_KEY:-EMPTY}
export DESCRIPTOR_MODE=generic

OUT=${REPO_ROOT}/benchmark/results/verbalized/v12_passive_dev
MAN=${REPO_ROOT}/benchmark/manifests_v2
SCR=${REPO_ROOT}/benchmark/scripts/agent_v12.py
mkdir -p "$OUT"

DOMAINS=(D1 D5 D2 D6 D3 D4 D7 D8 D9 D10 D11 D12)
for D in "${DOMAINS[@]}"; do
    M=$(ls "$MAN/${D}_"*.json 2>/dev/null | grep -v domain_config | grep -v split_ids | grep -v full_manifest | head -1)
    O="$OUT/${D}.json"
    if [ -f "$O" ] && [ $(stat -c %s "$O") -gt 1000 ]; then
        echo "[skip] $D"; continue
    fi
    echo "[v12-passive-dev] $D"
    python3 "$SCR" --manifest "$M" --split dev --backend qwen3 \
        --output "$O" --max_turns 3 --max_workers 8 --resume \
        || echo "[warn] $D failed"
done
echo "[done] v12 passive dev all 12 domains"
