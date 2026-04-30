#!/bin/bash
# Master orchestrator: resume passive_dev + build all L1/L2/stack.
# Safe to re-run: every stage skips already-complete outputs.
set -u
export QWEN_API_BASE=${QWEN_API_BASE:-http://localhost:8200/v1}
export QWEN_MODEL=Qwen3.5-VL-27B
export QWEN_API_KEY=${QWEN_API_KEY:-EMPTY}

ROOT=/hdd1/jiangxi/AD-Agent
SCR=$ROOT/benchmark/scripts/verbalized_learning.py
AGENT=$ROOT/benchmark/scripts/agent_v9.py
MAN=$ROOT/benchmark/manifests_v2
OUT=$ROOT/benchmark/results/verbalized
PDEV=$OUT/passive_dev
mkdir -p "$PDEV" "$OUT/l1" "$OUT/l2" "$OUT/stack"

DOMAINS=(D1 D5 D2 D6 D3 D4 D7 D8 D9 D10 D11 D12)

echo "=== Stage 0: passive_dev (resume) ==="
for D in "${DOMAINS[@]}"; do
    M=$(ls "$MAN/${D}_"*.json | head -1)
    O="$PDEV/${D}_passive_dev.json"
    # Only skip if file has real scored items (not all 0.5 placeholder garbage).
    if [ -f "$O" ] && [ $(stat -c %s "$O") -gt 1000 ]; then
        BAD=$(python3 -c "
import json
r=json.load(open('$O'))
print('bad' if (len(r) >= 1 and all(abs(x.get('anomaly_score',0.5)-0.5)<1e-6 for x in r)) else 'ok')
")
        if [ "$BAD" = "ok" ]; then
            echo "[skip] $D passive_dev ok"
            continue
        fi
        echo "[redo] $D passive_dev was all 0.5, rerunning"
        rm -f "$O"
    fi
    echo "[passive] $D"
    python3 "$AGENT" --manifest "$M" --split dev --backend qwen3 \
        --output "$O" --max_turns 3 --max_workers 8 --resume \
        || echo "[warn] $D passive failed"
done

echo "=== Stage 1: L1 rulebooks (resume) ==="
for D in "${DOMAINS[@]}"; do
    M=$(ls "$MAN/${D}_"*.json | head -1)
    O="$OUT/l1/${D}_l1.json"
    if [ -f "$O" ] && [ $(stat -c %s "$O") -gt 500 ]; then continue; fi
    python3 "$SCR" build-l1 --manifest "$M" --out "$O" --n_refs 8 --seed 0 || echo "[warn] $D L1 failed"
done

echo "=== Stage 2: L2 rulebooks (with tuple-bug fix) ==="
for D in "${DOMAINS[@]}"; do
    M=$(ls "$MAN/${D}_"*.json | head -1)
    P="$PDEV/${D}_passive_dev.json"
    [ ! -f "$P" ] && { echo "[skip] $D L2: passive_dev missing"; continue; }
    O="$OUT/l2/${D}_l2.json"
    # Skip only if file exists AND has >0 rules.
    if [ -f "$O" ]; then
        RC=$(python3 -c "import json;d=json.load(open('$O'));print(sum(len(u.get('rules',[])) for u in d.get('units',[])))" 2>/dev/null)
        if [ -n "$RC" ] && [ "$RC" -gt 0 ]; then
            echo "[skip] $D L2 has $RC rules"
            continue
        fi
    fi
    echo "[L2] $D"
    python3 "$SCR" build-l2 --manifest "$M" --passive_dev "$P" --out "$O" \
        --k 10 --seed 0 --selection_frac 0.5 || echo "[warn] $D L2 failed"
done

echo "=== Stage 3: stack L1+L2 ==="
for D in "${DOMAINS[@]}"; do
    L1="$OUT/l1/${D}_l1.json"
    L2="$OUT/l2/${D}_l2.json"
    S="$OUT/stack/${D}_l1l2.json"
    [ ! -f "$L1" ] || [ ! -f "$L2" ] && { echo "[skip] $D stack: inputs missing"; continue; }
    if [ -f "$S" ] && [ $(stat -c %s "$S") -gt 200 ]; then continue; fi
    python3 "$SCR" stack --l1 "$L1" --l2 "$L2" --out "$S" || echo "[warn] $D stack failed"
done

echo "=== master pipeline done ==="
