#!/bin/bash
# AD-Copilot baseline (Qwen2.5-VL-7B fine-tuned for IAD).
# Score = P(Yes) over {Yes,No} from first-token logits in response to a
# yes/no anomaly question with (1 ref, query) image pair.
set -u
REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
GPU=${GPU:-2}
OUT=${REPO_ROOT}/benchmark/results/baselines/ad_copilot
MAN=${REPO_ROOT}/benchmark/manifests_v2
MODEL=${MODEL:-${AD_COPILOT_DIR}/AD-Copilot}
mkdir -p "$OUT"

DOMAINS=(D1 D5 D2 D6 D3 D4 D7 D8 D9 D10 D11 D12)
for D in "${DOMAINS[@]}"; do
    M=$(ls "$MAN/${D}_"*.json 2>/dev/null | grep -v domain_config | grep -v split_ids | grep -v full_manifest | head -1)
    O="$OUT/${D}.json"
    if [ -f "$O" ] && [ "$(stat -c %s "$O")" -gt 1000 ]; then
        echo "[skip] $D"; continue
    fi
    echo "[$(date +%H:%M:%S)] AD-Copilot $D ← $M"
    CUDA_VISIBLE_DEVICES=$GPU python3 \
        ${REPO_ROOT}/benchmark/scripts/baseline_ad_copilot.py \
        --manifest "$M" --split test --output "$O" \
        --model_path "$MODEL" --device cuda:0 --resume \
        || echo "[warn] $D failed"
done
echo "[$(date +%H:%M:%S)] AD-Copilot done."
