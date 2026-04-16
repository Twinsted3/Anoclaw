#!/bin/bash
# Set up Qwen3-VL-8B-Instruct as local vLLM server for reproducibility baseline.
# Requires: ~16GB VRAM, one GPU

MODEL="Qwen/Qwen3-VL-8B-Instruct"
PORT=8000
GPU_ID=8  # use last GPU to leave others free for experiments

echo "=== Setting up Qwen3-VL-8B local server ==="
echo "GPU: $GPU_ID  Port: $PORT"

# Install vLLM if not available
pip show vllm >/dev/null 2>&1 || pip install vllm -q

# Download model via HF mirror (no proxy needed)
echo "Downloading $MODEL via hf-mirror.com ..."
HF_ENDPOINT=https://hf-mirror.com \
    huggingface-cli download "$MODEL" \
    --local-dir /hdd1/jiangxi/models/Qwen3-VL-8B-Instruct \
    --local-dir-use-symlinks False

echo "Starting vLLM server on GPU $GPU_ID port $PORT ..."
CUDA_VISIBLE_DEVICES=$GPU_ID \
    python -m vllm.entrypoints.openai.api_server \
    --model /hdd1/jiangxi/models/Qwen3-VL-8B-Instruct \
    --served-model-name Qwen3-VL-8B-Instruct \
    --port $PORT \
    --max-model-len 8192 \
    --limit-mm-per-prompt image=3 \
    --trust-remote-code &

echo "Server PID: $!"
echo "Waiting for server to start..."
sleep 15
curl -s http://localhost:$PORT/v1/models | python3 -c "import sys,json; d=json.load(sys.stdin); print('Models:', [m['id'] for m in d['data']])"
echo ""
echo "Set env: export QWEN_API_BASE=http://localhost:$PORT/v1"
echo "         export QWEN_MODEL=Qwen3-VL-8B-Instruct"
echo "         export QWEN_API_KEY=EMPTY"
