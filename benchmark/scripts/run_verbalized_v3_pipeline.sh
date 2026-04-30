#!/bin/bash
# v3 pipeline: L1 invariants (+12) -> L2 cluster (+12) -> 4-variant eval (+48)
set -u
export QWEN_API_BASE=${QWEN_API_BASE:-http://localhost:8210/v1}
export QWEN_MODEL=Qwen3.5-VL-27B
export QWEN_API_KEY=${QWEN_API_KEY:-EMPTY}

ROOT=/hdd1/jiangxi/AD-Agent
SCR=$ROOT/benchmark/scripts/verbalized_v3.py
MAN=$ROOT/benchmark/manifests_v2
OUT=$ROOT/benchmark/results/verbalized
PDEV=$OUT/passive_dev
L1=$OUT/v3_l1
L2=$OUT/v3_l2
mkdir -p "$L1" "$L2"

DOMAINS=(D1 D2 D3 D4 D5 D6 D7 D8 D9 D10 D11 D12)

echo "=== Stage 1: L1 v3 invariant extraction ==="
for D in "${DOMAINS[@]}"; do
    M=$(ls "$MAN/${D}_"*.json | head -1)
    O="$L1/${D}_l1.json"
    if [ -f "$O" ] && [ $(stat -c %s "$O") -gt 200 ]; then
        echo "[skip] $D L1 v3 exists"; continue
    fi
    echo "[L1 v3] $D"
    python3 "$SCR" build-l1 --manifest "$M" --out "$O" --n_refs 8 --seed 0 || echo "[warn] $D L1 v3 failed"
done

echo "=== Stage 2: L2 v3 cluster-based ==="
for D in "${DOMAINS[@]}"; do
    M=$(ls "$MAN/${D}_"*.json | head -1)
    P="$PDEV/${D}_passive_dev.json"
    [ ! -f "$P" ] && { echo "[skip] $D L2 v3: passive_dev missing"; continue; }
    O="$L2/${D}_l2.json"
    if [ -f "$O" ] && [ $(stat -c %s "$O") -gt 200 ]; then
        echo "[skip] $D L2 v3 exists"; continue
    fi
    echo "[L2 v3] $D"
    python3 "$SCR" build-l2 --manifest "$M" --passive_dev "$P" --out "$O" \
        --k 10 --seed 0 --selection_frac 0.5 || echo "[warn] $D L2 v3 failed"
done

echo "=== v3 build pipeline done ==="
