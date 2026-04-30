#!/bin/bash
# v11 meta-only ablation: run v11 on test with a rulebook containing only
# meta-rules (routing), no invariants/correctives. Isolates routing signal.
set -u
export QWEN_API_BASE=${QWEN_API_BASE:-http://localhost:8210/v1}
export QWEN_MODEL=${QWEN_MODEL:-Qwen3.5-VL-27B}
export QWEN_API_KEY=${QWEN_API_KEY:-EMPTY}
export DESCRIPTOR_MODE=generic

OUT=/hdd1/jiangxi/AD-Agent/benchmark/results/verbalized/v11_eval_test_meta_only
RULEBOOK_DIR=/hdd1/jiangxi/AD-Agent/benchmark/results/verbalized/v4_rulebook_meta_only
MAN=/hdd1/jiangxi/AD-Agent/benchmark/manifests_v2
SCR=/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v11.py
mkdir -p "$OUT"

DOMAINS=(D1 D2 D3 D4 D5 D6 D7 D8 D9 D10 D11 D12)
for D in "${DOMAINS[@]}"; do
    M=$(ls "$MAN/${D}_"*.json 2>/dev/null | grep -v domain_config | grep -v split_ids | grep -v full_manifest | head -1)
    O="$OUT/${D}.json"
    if [ -f "$O" ] && [ $(stat -c %s "$O") -gt 1000 ]; then
        echo "[skip] $D"; continue
    fi
    echo "[v11-meta-only] $D"
    python3 "$SCR" --manifest "$M" --split test --backend qwen3 \
        --output "$O" --max_turns 3 --max_workers 8 --resume \
        --learning_enabled \
        --rulebook_dir "$RULEBOOK_DIR" \
        --controller_max_tokens 400 \
        || echo "[warn] $D failed"
done
echo "[done] v11 meta-only ablation"
