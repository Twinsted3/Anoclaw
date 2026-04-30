#!/bin/bash
# Launch 4 Qwen3.5-VL-27B-FP8 replicas on GPUs 0,1,2,7 -> ports 8200-8203.
# - Each replica has --served-model-name Qwen3.5-VL-27B so callers can use
#   either the friendly alias or the raw path.
# - max-model-len raised to 16384 (4096 was too short for rulebook+refs).
# - Starts the round-robin LB on port 8210 afterwards.
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
    echo "[launch] GPU $gpu -> port $port (log: $log)"
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

# Custom GPU->port pairing (contiguous ports for LB simplicity).
launch_one 0 8200
launch_one 1 8201
launch_one 2 8202
launch_one 7 8203

echo ""
echo "Launched 4 replicas on GPUs 0,1,2,7 -> ports 8200,8201,8202,8203."
echo "Wait ~3-5 minutes for all to serve /v1/models."
echo "Then start LB with:  LB_N_REPLICAS=4 LB_BASE_PORT=8200 nohup python3 benchmark/scripts/vllm_lb.py > /tmp/v6_vllm_logs/lb.log 2>&1 &"
