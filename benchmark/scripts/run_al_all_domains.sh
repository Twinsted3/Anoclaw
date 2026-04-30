#!/bin/bash
# Run active learning on all 12 domains sequentially.
#
# Usage: run_al_all_domains.sh [K]   # K = oracle queries per domain (default 10)

set -e
K=${1:-10}
DOMAINS=${AL_DOMAINS:-"D1 D5 D2 D6 D3 D4 D7 D8 D9 D10 D11 D12"}

export QWEN_API_BASE="http://localhost:8210/v1"
export QWEN_MODEL="/hdd1/models/Qwen3.5-27B-FP8"

cd /hdd1/jiangxi/AD-Agent
mkdir -p benchmark/results/active_learning

for D in $DOMAINS; do
    OUT=benchmark/results/active_learning/al_qwen35_${D}.json
    if [ -f "$OUT" ]; then
        echo "[AL] $D output exists, skipping"
        continue
    fi
    echo "=== [AL] $D starting at $(date +%H:%M:%S) ==="
    /hdd1/jiangxi/AD-Agent/.venv_qwen35/bin/python \
        benchmark/scripts/active_learning.py \
        --manifest_dir benchmark/manifests_v2 \
        --domain $D --output $OUT \
        --k $K --fewshot_k 3 \
        --max_turns 2 --max_workers 8 --backend qwen3 \
        --max_test ${AL_MAX_TEST:-40} \
        2>&1 | tee -a /tmp/al_${D}.log
    echo "=== [AL] $D done at $(date +%H:%M:%S) ==="
done

echo "All domains complete."
