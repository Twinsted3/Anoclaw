#!/bin/bash
# 4 independent vLLM Qwen3.5-27B-FP8 servers, ports 8200-8203.
# max-model-len 24576 (24K) to accommodate v8-tools richer observations.
VENV_PYTHON=/hdd1/jiangxi/AD-Agent/.venv_qwen35/bin/python
MODEL=/hdd1/models/Qwen3.5-27B-FP8
GPUS=(0 1 2 7)

for idx in 0 1 2 3; do
    PORT=$((8200 + idx))
    GPU=${GPUS[$idx]}
    LOG=/tmp/qwen35_vllm_r${idx}.log
    echo "Launching replica $idx on port $PORT, GPU $GPU (log: $LOG)"
    CUDA_VISIBLE_DEVICES=$GPU nohup $VENV_PYTHON -m vllm.entrypoints.openai.api_server \
        --model $MODEL \
        --served-model-name Qwen3.5-VL-27B \
        --port $PORT \
        --tensor-parallel-size 1 \
        --max-model-len 24576 \
        --limit-mm-per-prompt '{"image":16}' \
        --gpu-memory-utilization 0.88 \
        --trust-remote-code \
        --enforce-eager \
        --dtype auto > $LOG 2>&1 &
    echo "  PID: $!"
done
echo "All 4 replicas launching. Use 'curl http://localhost:820N/v1/models' to check readiness."
