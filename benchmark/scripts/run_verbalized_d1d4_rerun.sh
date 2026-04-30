#!/bin/bash
# Rerun L2 + stack for D1-D4 after the tuple-bug fix.
# Assumes main pipeline has completed (or at least passive_dev D1-D4 is
# real data, and l1/D[1-4]_l1.json exist).
set -u
export QWEN_API_BASE=${QWEN_API_BASE:-http://localhost:8200/v1}
export QWEN_MODEL=Qwen3.5-VL-27B
export QWEN_API_KEY=${QWEN_API_KEY:-EMPTY}

ROOT=/hdd1/jiangxi/AD-Agent
SCR=$ROOT/benchmark/scripts/verbalized_learning.py
MAN=$ROOT/benchmark/manifests_v2
OUT=$ROOT/benchmark/results/verbalized

DOMAINS=(D1 D2 D3 D4)

echo "=== L2 rerun: D1-D4 ==="
for D in "${DOMAINS[@]}"; do
    M=$(ls "$MAN/${D}_"*.json | head -1)
    P="$OUT/passive_dev/${D}_passive_dev.json"
    if [ ! -f "$P" ]; then echo "[skip] $D: passive_dev missing"; continue; fi
    O="$OUT/l2/${D}_l2.json"
    if [ -f "$O" ] && [ $(stat -c %s "$O") -gt 500 ]; then
        RC=$(python3 -c "import json;d=json.load(open('$O'));print(sum(len(u.get('rules',[])) for u in d.get('units',[])))")
        if [ "$RC" -gt 0 ]; then echo "[skip] $D: L2 already has $RC rules"; continue; fi
    fi
    echo "[L2] $D"
    python3 "$SCR" build-l2 \
        --manifest "$M" --passive_dev "$P" --out "$O" \
        --k 10 --seed 0 --selection_frac 0.5 || echo "[warn] $D L2 failed"
done

echo "=== Stack: all 12 ==="
for D in D1 D2 D3 D4 D5 D6 D7 D8 D9 D10 D11 D12; do
    L1="$OUT/l1/${D}_l1.json"
    L2="$OUT/l2/${D}_l2.json"
    S="$OUT/stack/${D}_l1l2.json"
    if [ ! -f "$L1" ] || [ ! -f "$L2" ]; then
        echo "[skip] $D stack: inputs missing"
        continue
    fi
    if [ -f "$S" ] && [ $(stat -c %s "$S") -gt 200 ]; then
        echo "[skip] $D stack exists"
        continue
    fi
    python3 "$SCR" stack --l1 "$L1" --l2 "$L2" --out "$S" || echo "[warn] $D stack failed"
done

echo "=== D1-D4 rerun + stack done ==="
