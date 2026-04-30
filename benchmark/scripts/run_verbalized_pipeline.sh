#!/bin/bash
# Full verbalized-learning pipeline across 12 CrossDomainVAD-11 domains.
#   Stage 1: build L1 ref-only rulebooks (0 oracle)
#   Stage 2: build L2 dev-oracle rulebooks (K=10, no L1 context — §5.2)
#   Stage 3: stack L1+L2 offline
# Outputs under benchmark/results/verbalized/ .
set -u
export QWEN_API_BASE=${QWEN_API_BASE:-http://localhost:8200/v1}
# IMPORTANT: served name is the PATH, not "Qwen3.5-VL-27B". See
# run_passive_dev_all.sh for the same gotcha.
export QWEN_MODEL=Qwen3.5-VL-27B
export QWEN_API_KEY=${QWEN_API_KEY:-EMPTY}

ROOT=/hdd1/jiangxi/AD-Agent
SCR=$ROOT/benchmark/scripts/verbalized_learning.py
MAN=$ROOT/benchmark/manifests_v2
OUT=$ROOT/benchmark/results/verbalized
PDEV=$OUT/passive_dev
mkdir -p "$OUT/l1" "$OUT/l2" "$OUT/stack"

DOMAINS=(D1 D2 D3 D4 D5 D6 D7 D8 D9 D10 D11 D12)
SEED=0

echo "=== Stage 1: L1 rulebooks ==="
for D in "${DOMAINS[@]}"; do
    M=$(ls "$MAN/${D}_"*.json 2>/dev/null | head -1)
    [ -z "$M" ] && { echo "[skip] $D: manifest missing"; continue; }
    O="$OUT/l1/${D}_l1.json"
    if [ -f "$O" ] && [ $(stat -c %s "$O") -gt 200 ]; then
        echo "[skip] $D L1 exists"
        continue
    fi
    echo "[L1] $D"
    python3 "$SCR" build-l1 --manifest "$M" --out "$O" --n_refs 8 --seed $SEED || echo "[warn] $D L1 failed"
done

echo "=== Stage 2: L2 rulebooks (dev-only, no L1 context) ==="
for D in "${DOMAINS[@]}"; do
    M=$(ls "$MAN/${D}_"*.json 2>/dev/null | head -1)
    [ -z "$M" ] && continue
    P="$PDEV/${D}_passive_dev.json"
    [ ! -f "$P" ] && { echo "[skip] $D L2: passive_dev missing"; continue; }
    O="$OUT/l2/${D}_l2.json"
    if [ -f "$O" ] && [ $(stat -c %s "$O") -gt 200 ]; then
        echo "[skip] $D L2 exists"
        continue
    fi
    echo "[L2] $D"
    python3 "$SCR" build-l2 \
        --manifest "$M" \
        --passive_dev "$P" \
        --out "$O" \
        --k 10 --seed $SEED --selection_frac 0.5 || echo "[warn] $D L2 failed"
done

echo "=== Stage 3: stack L1+L2 offline ==="
for D in "${DOMAINS[@]}"; do
    L1="$OUT/l1/${D}_l1.json"
    L2="$OUT/l2/${D}_l2.json"
    S="$OUT/stack/${D}_l1l2.json"
    [ ! -f "$L1" ] || [ ! -f "$L2" ] && { echo "[skip] $D stack: inputs missing"; continue; }
    if [ -f "$S" ] && [ $(stat -c %s "$S") -gt 200 ]; then
        echo "[skip] $D stack exists"
        continue
    fi
    echo "[stack] $D"
    python3 "$SCR" stack --l1 "$L1" --l2 "$L2" --out "$S" || echo "[warn] $D stack failed"
done

echo "=== pipeline done ==="
