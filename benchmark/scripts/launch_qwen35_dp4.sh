#!/bin/bash
# Native vLLM data-parallel: 1 API server on port 8200, internally managing
# 4 engine workers on GPUs 0,1,2,7. No external LB needed.
set -u
MODEL_PATH="/hdd1/models/Qwen3.5-27B-FP8"
SERVED_NAME="Qwen3.5-VL-27B"
MAX_LEN=16384
MM_LIMIT=12
UTIL=0.85
LOG=/tmp/v6_vllm_logs/vllm_dp4.log
mkdir -p /tmp/v6_vllm_logs
VENV_PY=/hdd1/jiangxi/AD-Agent/.venv_qwen35/bin/python

echo "[launch] DP=4 on GPUs 0,1,2,7 -> port 8200 (log: $LOG)"
CUDA_VISIBLE_DEVICES=0,1,2,7 nohup "$VENV_PY" -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --served-model-name "$SERVED_NAME" \
    --port 8200 \
    --tensor-parallel-size 1 \
    --data-parallel-size 4 \
    --data-parallel-size-local 4 \
    --data-parallel-backend mp \
    --max-model-len $MAX_LEN \
    --limit-mm-per-prompt "{\"image\":$MM_LIMIT}" \
    --gpu-memory-utilization $UTIL \
    --trust-remote-code \
    --enforce-eager \
    --dtype auto \
    >"$LOG" 2>&1 &
echo "PID $!"
echo "Wait ~3-5 min for all 4 engines to load. Tail: tail -f $LOG"
