#!/usr/bin/env bash
# Download the CrossDomainVAD-12 dataset bundle and expert-score caches from
# Hugging Face Hub.
#
# Required env (set these before running, or accept the defaults):
#   ANOMALYCLAW_DATA — where dataset folders are placed
#                      (default: <repo>/benchmark/data)
#   HF_ENDPOINT      — HF mirror; set to https://hf-mirror.com inside China
#
# The HF repo names below are PLACEHOLDERS — replace once the dataset and
# weights bundles are published. Until then, follow the "Manual setup"
# section of DATA.md.

set -eu
REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

DATA_DIR="${ANOMALYCLAW_DATA:-$REPO_ROOT/benchmark/data}"
RESULTS_DIR="${ANOMALYCLAW_RESULTS_DIR:-$REPO_ROOT/benchmark/results}"
INDEX_DIR="${ANOMALYCLAW_INDEX_DIR:-$REPO_ROOT/benchmark/retrieval_index}"

# Placeholders — update with the real HF repo IDs once published.
HF_DATASET_REPO="${HF_DATASET_REPO:-<HF_DATASET_REPO>}"
HF_MODEL_REPO="${HF_MODEL_REPO:-<HF_MODEL_REPO>}"

mkdir -p "$DATA_DIR" "$RESULTS_DIR" "$INDEX_DIR"

if ! python -c "import huggingface_hub" 2>/dev/null; then
    echo "[error] huggingface_hub is required. Install with:"
    echo "        pip install -U huggingface_hub"
    exit 1
fi

if [[ "$HF_DATASET_REPO" == "<HF_DATASET_REPO>" ]]; then
    cat <<EOF
[warn] HF_DATASET_REPO is unset and no default is baked in.

The dataset bundle has not been wired up yet. Either:

  1. Export HF_DATASET_REPO=<org>/<repo> before re-running this script, or
  2. Follow the "Manual setup (per-dataset)" instructions in DATA.md to
     assemble \$ANOMALYCLAW_DATA from each upstream dataset by hand.

Skipping dataset download.
EOF
else
    echo "[info] Downloading dataset bundle from $HF_DATASET_REPO → $DATA_DIR"
    python - <<PY
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="$HF_DATASET_REPO",
    repo_type="dataset",
    local_dir="$DATA_DIR",
    local_dir_use_symlinks=False,
    resume_download=True,
)
PY
fi

if [[ "$HF_MODEL_REPO" == "<HF_MODEL_REPO>" ]]; then
    echo "[warn] HF_MODEL_REPO is unset; skipping expert-score-cache download."
    echo "       See DATA.md → 'Expert score caches'."
else
    echo "[info] Downloading expert-score caches from $HF_MODEL_REPO → $RESULTS_DIR"
    python - <<PY
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="$HF_MODEL_REPO",
    local_dir="$RESULTS_DIR",
    allow_patterns=["subspacead_*.json", "anomalyvfm_*.json"],
    local_dir_use_symlinks=False,
    resume_download=True,
)
PY
fi

echo "[done] Downloads complete. Build the DINOv2 retrieval index with:"
echo "       python benchmark/scripts/build_retrieval_index.py"
