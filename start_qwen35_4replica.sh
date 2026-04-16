#!/bin/bash
# 4 independent vLLM Qwen3.5-27B-FP8 servers, ports 8200-8203, GPUs 0..3.
VENV_PYTHON=/hdd1/jiangxi/AD-Agent/.venv_qwen35/bin/python
MODEL=/hdd1/models/Qwen3.5-27B-FP8

for i in 0 1 2 3; do
    PORT=$((8200 + i))
    LOG=/tmp/qwen35_vllm_r${i}.log
    echo "Launching replica $i on port $PORT, GPU $i (log: $LOG)"
    CUDA_VISIBLE_DEVICES=$i nohup $VENV_PYTHON -m vllm.entrypoints.openai.api_server \
        --model $MODEL \
        --port $PORT \
        --tensor-parallel-size 1 \
        --max-model-len 4096 \
        --gpu-memory-utilization 0.85 \
        --trust-remote-code \
        --enforce-eager \
        --dtype auto > $LOG 2>&1 &
    echo "  PID: $!"
done
echo "All 4 replicas launching. Use 'curl http://localhost:820N/v1/models' to check readiness."
