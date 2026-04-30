#!/bin/bash
# Sequential overnight pipeline.
# Phase A: MMAD dev (989) → analyze → thresholds
# Phase B: MMAD test (1500) → final per-type accuracy with tuned thresholds
# Phase C: Active learning on 6 pilot domains (D1, D4, D5, D7, D9, D12)
# Phase D: Summarize AL and update paper drafts
#
# Usage: overnight_pipeline.sh
# Expects vLLM replicas running on 8200-8202 and LB on 8210.

set -e
export QWEN_API_BASE="http://localhost:8210/v1"
export QWEN_MODEL="/hdd1/models/Qwen3.5-27B-FP8"
cd /hdd1/jiangxi/AD-Agent
PY=/hdd1/jiangxi/AD-Agent/.venv_qwen35/bin/python
RESULTS=benchmark/results

stamp() { date +%Y-%m-%d\ %H:%M:%S; }

echo "[$(stamp)] === Phase A: MMAD dev 989 ==="
if [ ! -f $RESULTS/mmad_v9_dev989.json ]; then
  $PY benchmark/scripts/mmad_eval_v9.py \
    --mmad_root MMAD/dataset/MMAD \
    --output $RESULTS/mmad_v9_dev989.json \
    --sample 989 --backend qwen3 --max_workers 8 --max_turns 3 --mode both \
    --seed 42 \
    2>&1 | tee -a /tmp/mmad_dev989.log
else
  echo "skip (file exists)"
fi

echo "[$(stamp)] === Phase A.2: analyze dev ==="
$PY benchmark/scripts/mmad_analyze.py --dev $RESULTS/mmad_v9_dev989.json \
  --out $RESULTS/mmad_v9_dev989_report.json 2>&1 | tee /tmp/mmad_dev989_analyze.log

echo "[$(stamp)] === Phase B: MMAD test 1500 (seed=100) ==="
if [ ! -f $RESULTS/mmad_v9_test1500.json ]; then
  $PY benchmark/scripts/mmad_eval_v9.py \
    --mmad_root MMAD/dataset/MMAD \
    --output $RESULTS/mmad_v9_test1500.json \
    --sample 1500 --backend qwen3 --max_workers 8 --max_turns 3 --mode both \
    --seed 100 \
    2>&1 | tee -a /tmp/mmad_test1500.log
else
  echo "skip (file exists)"
fi

echo "[$(stamp)] === Phase B.2: analyze dev+test ==="
$PY benchmark/scripts/mmad_analyze.py \
  --dev $RESULTS/mmad_v9_dev989.json \
  --test $RESULTS/mmad_v9_test1500.json \
  --out $RESULTS/mmad_v9_report.json 2>&1 | tee /tmp/mmad_report.log

echo "[$(stamp)] === Phase C: Active Learning pilot (6 domains) ==="
mkdir -p $RESULTS/active_learning
PILOT_DOMS="D1 D4 D5 D7 D9 D12"
for D in $PILOT_DOMS; do
  OUT=$RESULTS/active_learning/al_qwen35_${D}.json
  if [ -f "$OUT" ]; then echo "skip $D"; continue; fi
  echo "[$(stamp)] AL $D starting"
  $PY benchmark/scripts/active_learning.py \
    --manifest_dir benchmark/manifests_v2 \
    --domain $D --output $OUT --k 10 --fewshot_k 3 \
    --max_turns 4 --max_workers 6 --backend qwen3 \
    2>&1 | tee /tmp/al_${D}.log
  echo "[$(stamp)] AL $D done"
done

echo "[$(stamp)] === Phase D: summarize AL ==="
$PY benchmark/scripts/al_summarize.py \
  --dir $RESULTS/active_learning \
  --out $RESULTS/al_summary.json 2>&1 | tee /tmp/al_summary.log

echo "[$(stamp)] === ALL PHASES DONE ==="
