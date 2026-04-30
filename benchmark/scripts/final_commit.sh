#!/bin/bash
# Final commit of MMAD v9 + AL results for morning handoff.
set -e
cd /hdd1/jiangxi/AD-Agent

# Stage
git add \
    benchmark/results/mmad_v9_dev*.json \
    benchmark/results/mmad_v9_test*.json \
    benchmark/results/mmad_v9_report.json \
    benchmark/results/active_learning/ \
    benchmark/results/al_summary.json \
    paper/sections/4x_mmad_fulltype.tex \
    RESUME.md \
    2>/dev/null || true

# Drop intermediates/logs
git reset HEAD /tmp/*.log 2>/dev/null || true

git status --short | head -30
git commit -m "$(cat <<'EOF'
Overnight autonomous run: MMAD v9 full-type + active learning pilot

- MMAD v9 unified agent run on dev (stratified n=500..989) + analysis:
  per-type accuracy for all 9 MMAD question types + per-class
  AD threshold calibration.
- Active learning pilot on 6 domains (D1, D6, D3, D7, D9, D12) with
  K=10 oracle queries per domain, DINOv2 CLS few-shot retrieval.
- Paper section 4x_mmad_fulltype.tex updated with numbers.
- RESUME.md extended with v9 + AL summary.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)" 2>&1 | tail -5
