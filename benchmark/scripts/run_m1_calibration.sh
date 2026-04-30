#!/bin/bash
# M1: Run calibration slice (160 items) with GPT + SeedVL
# Variants: Direct, Normal-First, Self-Refine, Debate-1R
#
# Usage:
#   bash benchmark/scripts/run_m1_calibration.sh seedvl   # SeedVL only
#   bash benchmark/scripts/run_m1_calibration.sh gpt      # GPT only
#   bash benchmark/scripts/run_m1_calibration.sh all      # both
#   bash benchmark/scripts/run_m1_calibration.sh sanity   # 10-item sanity check

set -e
cd /hdd1/jiangxi/AD-Agent

MANIFEST="benchmark/manifests/full_manifest.json"
RESULTS="benchmark/results"
mkdir -p "$RESULTS"

BACKEND=${1:-seedvl}
SPLIT=calibration
WORKERS=4
DOMAINS="D1 D5"   # Start with available domains only

run_variant() {
    local backend=$1
    local variant=$2
    local out="$RESULTS/${backend}_${variant}_${SPLIT}.json"
    echo "  Running: $backend / $variant → $out"
    python3 benchmark/scripts/infer.py \
        --manifest "$MANIFEST" \
        --split "$SPLIT" \
        --backend "$backend" \
        --variant "$variant" \
        --output "$out" \
        --domains $DOMAINS \
        --max_workers "$WORKERS" \
        --resume
    python3 benchmark/scripts/evaluate.py \
        --results "$out" \
        --output "${out%.json}_metrics.json"
}

run_sanity() {
    local backend=$1
    echo "=== SANITY CHECK: $backend, 10 items ==="
    local out="$RESULTS/${backend}_v1_normal_first_sanity.json"
    python3 benchmark/scripts/infer.py \
        --manifest "$MANIFEST" \
        --split calibration \
        --backend "$backend" \
        --variant v1_normal_first \
        --output "$out" \
        --domains D1 \
        --max_items 10 \
        --max_workers 2
    python3 benchmark/scripts/evaluate.py \
        --results "$out" \
        --output "${out%.json}_metrics.json"
    echo "Sanity done. Check $out"
}

case "$BACKEND" in
    sanity)
        run_sanity seedvl
        ;;
    seedvl)
        echo "=== M1 Calibration: SeedVL ==="
        for variant in v0_direct v1_normal_first v2_self_refine v3_debate_1r; do
            run_variant seedvl "$variant"
        done
        ;;
    gpt)
        echo "=== M1 Calibration: GPT ==="
        for variant in v0_direct v1_normal_first v2_self_refine v3_debate_1r; do
            run_variant gpt "$variant"
        done
        ;;
    all)
        echo "=== M1 Calibration: SeedVL + GPT ==="
        for variant in v0_direct v1_normal_first v2_self_refine v3_debate_1r; do
            run_variant seedvl "$variant" &
            run_variant gpt "$variant" &
            wait
        done
        ;;
    *)
        echo "Usage: $0 [sanity|seedvl|gpt|all]"
        exit 1
        ;;
esac

echo ""
echo "=== M1 Complete ==="
echo "Results in: $RESULTS/"
ls -lh "$RESULTS/"*.json 2>/dev/null | tail -20
