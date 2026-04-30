#!/bin/bash
# Stage A: Run Passive v11 (learning_enabled=False == v10) on manifests_v2 dev.
# Collects per-item (v9_score, v9_rationale, direct_score, direct_rationale)
# so verbalized_v4 can partition disagreement cases and reflect meta-rules.
set -u
export QWEN_API_BASE=${QWEN_API_BASE:-http://localhost:8210/v1}
export QWEN_MODEL=${QWEN_MODEL:-Qwen3.5-VL-27B}
export QWEN_API_KEY=${QWEN_API_KEY:-EMPTY}
# v10 Direct branch must use the descriptor-free generic prompt to match the
# Table 1 Qwen3.5 0.732 baseline definition.
export DESCRIPTOR_MODE=generic

OUT=/hdd1/jiangxi/AD-Agent/benchmark/results/verbalized/v11_passive_dev
MAN=/hdd1/jiangxi/AD-Agent/benchmark/manifests_v2
SCR=/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v11.py
mkdir -p "$OUT"

DOMAINS=(D1 D5 D2 D6 D3 D4 D7 D8 D9 D10 D11 D12)

for D in "${DOMAINS[@]}"; do
    M=$(ls "$MAN/${D}_"*.json 2>/dev/null | grep -v domain_config | grep -v split_ids | grep -v full_manifest | head -1)
    O="$OUT/${D}.json"
    if [ -f "$O" ] && [ $(stat -c %s "$O") -gt 1000 ]; then
        echo "[skip] $D (already have $O)"
        continue
    fi
    echo "[v11-passive-dev] $D ← $M"
    python3 "$SCR" --manifest "$M" --split dev --backend qwen3 \
        --output "$O" --max_turns 3 --max_workers 8 --resume \
        || echo "[warn] $D failed"
done
echo "[done] v11 passive dev all 12 domains"
