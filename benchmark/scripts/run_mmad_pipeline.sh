#!/bin/bash
# Full MMAD v9 pipeline: dev calibration + analysis.
#
# Usage: run_mmad_pipeline.sh [PHASE]
#   PHASE ∈ {dev, test, analyze, all}

set -e
PHASE=${1:-all}
export QWEN_API_BASE="http://localhost:8210/v1"
export QWEN_MODEL="/hdd1/models/Qwen3.5-27B-FP8"

cd /hdd1/jiangxi/AD-Agent
mkdir -p benchmark/results

PY=/hdd1/jiangxi/AD-Agent/.venv_qwen35/bin/python
DEV_OUT=benchmark/results/mmad_v9_dev_n500.json
TEST_OUT=benchmark/results/mmad_v9_test_n2000.json
REPORT=benchmark/results/mmad_v9_report.json

if [ "$PHASE" = "dev" ] || [ "$PHASE" = "all" ]; then
  echo "=== [$(date +%H:%M:%S)] DEV phase: 500 images × 9 types ==="
  $PY benchmark/scripts/mmad_eval_v9.py \
      --mmad_root MMAD/dataset/MMAD \
      --output $DEV_OUT \
      --sample 500 --backend qwen3 --max_workers 8 --max_turns 3 --mode both \
      --seed 42 --resume \
      2>&1 | tee -a /tmp/mmad_dev.log
fi

if [ "$PHASE" = "test" ] || [ "$PHASE" = "all" ]; then
  echo "=== [$(date +%H:%M:%S)] TEST phase: 2000 images × 9 types (seed=100) ==="
  $PY benchmark/scripts/mmad_eval_v9.py \
      --mmad_root MMAD/dataset/MMAD \
      --output $TEST_OUT \
      --sample 2000 --backend qwen3 --max_workers 8 --max_turns 3 --mode both \
      --seed 100 --resume \
      2>&1 | tee -a /tmp/mmad_test.log
fi

if [ "$PHASE" = "analyze" ] || [ "$PHASE" = "all" ]; then
  echo "=== [$(date +%H:%M:%S)] ANALYSIS ==="
  $PY benchmark/scripts/mmad_analyze.py \
      --dev $DEV_OUT \
      --test $TEST_OUT \
      --out $REPORT \
      2>&1 | tee -a /tmp/mmad_analyze.log
fi

echo "=== [$(date +%H:%M:%S)] pipeline done ==="
