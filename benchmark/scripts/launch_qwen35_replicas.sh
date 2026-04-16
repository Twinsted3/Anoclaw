#!/bin/bash
# Launch 4 Qwen3.5-VL-27B-FP8 replicas on GPUs 0-3, ports 8200-8203.
# vllm_lb.py routes requests round-robin on port 8210.

set -u
MODEL_PATH="/hdd1/models/Qwen3.5-27B-FP8"
SERVED_NAME="Qwen3.5-VL-27B"
MAX_LEN=16384
MM_LIMIT=12
UTIL=0.85
LOG_DIR=/tmp/v6_vllm_logs
mkdir -p "$LOG_DIR"

VENV_PY=/hdd1/jiangxi/AD-Agent/.venv_qwen35/bin/python

launch_one() {
    local gpu=$1
    local port=$2
    local log="$LOG_DIR/vllm_gpu${gpu}_port${port}.log"
    echo "[launch] GPU $gpu → port $port (log: $log)"
    CUDA_VISIBLE_DEVICES=$gpu nohup "$VENV_PY" -m vllm.entrypoints.openai.api_server \
        --model "$MODEL_PATH" \
        --served-model-name "$SERVED_NAME" \
        --port "$port" \
        --tensor-parallel-size 1 \
        --max-model-len $MAX_LEN \
        --limit-mm-per-prompt "{\"image\":$MM_LIMIT}" \
        --gpu-memory-utilization $UTIL \
        --trust-remote-code \
        --enforce-eager \
        --dtype auto \
        >"$log" 2>&1 &
    echo "  PID $!"
}

for i in 0 1 2 3; do
    launch_one $i $((8200 + i))
done

echo
echo "Launched 4 replicas. Tail logs: tail -f $LOG_DIR/vllm_gpu*.log"
echo "Wait ~3-5 minutes for all to serve /v1/models."
