#!/bin/bash
# Run Passive v9 on dev split across all 12 CrossDomainVAD-11 domains.
# Outputs per-domain JSON under benchmark/results/verbalized/passive_dev/.
# Feeds verbalized_learning.py build-l2.
set -u
export QWEN_API_BASE=${QWEN_API_BASE:-http://localhost:8200/v1}
# IMPORTANT: the served model name on this LB is the model PATH, not
# "Qwen3.5-VL-27B". Using the wrong name gives 404 on every request
# and silent "json parse failed" items with score=0.5. Force the
# correct path here even if the caller's env has a legacy value.
export QWEN_MODEL=Qwen3.5-VL-27B
export QWEN_API_KEY=${QWEN_API_KEY:-EMPTY}
OUT_DIR=/hdd1/jiangxi/AD-Agent/benchmark/results/verbalized/passive_dev
mkdir -p "$OUT_DIR"
MANIFEST_DIR=/hdd1/jiangxi/AD-Agent/benchmark/manifests_v2
SCRIPT=/hdd1/jiangxi/AD-Agent/benchmark/scripts/agent_v9.py

DOMAINS=(D1 D5 D2 D6 D3 D4 D7 D8 D9 D10 D11 D12)
for D in "${DOMAINS[@]}"; do
    MANIFEST=$(ls "$MANIFEST_DIR/${D}_"*.json 2>/dev/null | head -1)
    if [ -z "$MANIFEST" ]; then
        echo "[skip] $D: manifest missing"
        continue
    fi
    OUT="$OUT_DIR/${D}_passive_dev.json"
    if [ -f "$OUT" ] && [ $(stat -c %s "$OUT") -gt 1000 ]; then
        echo "[skip] $D: $OUT already populated"
        continue
    fi
    echo "[run] $D -> $OUT  (manifest=$MANIFEST)"
    python3 "$SCRIPT" \
        --manifest "$MANIFEST" \
        --split dev \
        --backend qwen3 \
        --output "$OUT" \
        --max_turns 3 \
        --max_workers 6 \
        --resume \
        || echo "[warn] $D failed, continuing"
done
echo "[done] passive_dev sweep across 12 domains"
