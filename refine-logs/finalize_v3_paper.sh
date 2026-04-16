#!/bin/bash
# Final pipeline once both v3 runs complete: analyse + update paper + recompile.
set -e
cd /hdd1/jiangxi/AD-Agent

# 1. Compute v3 macro AUROC + paired bootstrap vs fusion on the same items.
python -u refine-logs/update_paper_with_v3.py 2>&1 | tee refine-logs/V3_FINAL_ANALYSIS.txt

# 2. Recompile paper.
cd paper
tectonic -X compile main.tex --keep-intermediates 2>&1 | tail -3
echo "Pages: $(pdfinfo main.pdf | grep Pages)"
grep -cE "Citation.*undefined|Reference.*undefined" main.log || true
