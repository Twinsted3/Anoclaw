#!/bin/bash
# Run Passive v9 (no rulebook) on manifests_v2 TEST split for all 12 domains.
# This is the correct baseline for §5 because manifests_v2 test items differ
# from §4's v1 test items on most domains.
set -u
export QWEN_API_BASE=${QWEN_API_BASE:-http://localhost:8210/v1}
export QWEN_MODEL=Qwen3.5-VL-27B
export QWEN_API_KEY=${QWEN_API_KEY:-EMPTY}
OUT=/hdd1/jiangxi/AD-Agent/benchmark/results/verbalized/passive_test
mkdir -p "$OUT"
MAN=/hdd1/jiangxi/AD-Agent/benchmark/manifests_v2
SCR=/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v9.py
DOMAINS=(D1 D5 D2 D6 D3 D4 D7 D8 D9 D10 D11 D12)
for D in "${DOMAINS[@]}"; do
    M=$(ls "$MAN/${D}_"*.json | head -1)
    O="$OUT/${D}_passive_test.json"
    if [ -f "$O" ] && [ $(stat -c %s "$O") -gt 1000 ]; then
        echo "[skip] $D"; continue
    fi
    echo "[passive-test] $D"
    python3 "$SCR" --manifest "$M" --split test --backend qwen3 \
        --output "$O" --max_turns 3 --max_workers 6 --resume \
        || echo "[warn] $D failed"
done
echo "[done] passive_test all 12"
