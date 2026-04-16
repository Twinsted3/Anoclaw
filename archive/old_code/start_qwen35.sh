#!/bin/bash
# Start Qwen3.5-27B-FP8 (dense) via vLLM on port 8001
# Using TP=2 for faster throughput, enforce-eager to skip slow torch.compile
# MoE model (35B-A3B-FP8) produces gibberish with vLLM 0.19.0, so using dense instead

export CUDA_VISIBLE_DEVICES=1,2

VENV_PYTHON=/hdd1/jiangxi/AD-Agent/.venv_qwen35/bin/python
MODEL=/hdd1/models/Qwen3.5-27B-FP8
PORT=8001
LOG=/tmp/qwen35_vllm.log

echo "Starting vLLM server for Qwen3.5-27B-FP8 (dense, TP=2) on port $PORT"
echo "GPUs: $CUDA_VISIBLE_DEVICES"
echo "Log: $LOG"
echo "Started at: $(date)"

exec $VENV_PYTHON -m vllm.entrypoints.openai.api_server \
    --model $MODEL \
    --port $PORT \
    --tensor-parallel-size 2 \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.90 \
    --trust-remote-code \
    --served-model-name qwen3.5 \
    --enforce-eager \
    --dtype auto \
    2>&1
