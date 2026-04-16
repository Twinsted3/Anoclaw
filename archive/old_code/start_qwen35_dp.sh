#!/bin/bash
# Multi-GPU data-parallel vLLM for Qwen3.5-27B-FP8.
# DP=4 (4 replicas, 1 GPU each), TP=1; throughput ~4x single replica.
export CUDA_VISIBLE_DEVICES=0,1,2,3
VENV_PYTHON=/hdd1/jiangxi/AD-Agent/.venv_qwen35/bin/python
MODEL=/hdd1/models/Qwen3.5-27B-FP8
PORT=8200
LOG=/tmp/qwen35_vllm_dp.log
echo "Starting vLLM DP=4 for Qwen3.5-27B-FP8 on port $PORT, GPUs $CUDA_VISIBLE_DEVICES"
echo "Log: $LOG"
exec $VENV_PYTHON -m vllm.entrypoints.openai.api_server \
    --model $MODEL \
    --port $PORT \
    --data-parallel-size 4 \
    --tensor-parallel-size 1 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.85 \
    --trust-remote-code \
    --enforce-eager \
    --dtype auto
