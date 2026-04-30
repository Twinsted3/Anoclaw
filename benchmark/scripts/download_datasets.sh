#!/bin/bash
# Download missing benchmark datasets.
# Run each section independently as needed.
# Priority: direct/mirror first, proxy as fallback.

DATA_DIR="/hdd1/jiangxi/AD-Agent/benchmark/data"
mkdir -p "$DATA_DIR"

# ─── D8: UCSD Avenue ──────────────────────────────────────────────────────────
# Small dataset (~300MB), direct download
download_avenue() {
    echo "=== D8: Avenue Dataset ==="
    mkdir -p "$DATA_DIR/Avenue"
    cd "$DATA_DIR/Avenue"
    # Official source (CUHK)
    wget -c "http://www.cse.cuhk.edu.hk/leojia/projects/detectabnormal/Avenue_Dataset.zip" \
        -O Avenue_Dataset.zip || \
    # Fallback: HuggingFace mirror
    wget -c "https://hf-mirror.com/datasets/UCSD-Avenue/avenue/resolve/main/Avenue_Dataset.zip" \
        -O Avenue_Dataset.zip
    unzip -q Avenue_Dataset.zip && echo "Avenue: OK"
}

# ─── D7: RoadAnomaly21 ────────────────────────────────────────────────────────
download_roadanomaly() {
    echo "=== D7: RoadAnomaly21 ==="
    mkdir -p "$DATA_DIR/RoadAnomaly21"
    cd "$DATA_DIR/RoadAnomaly21"
    # Official page: https://segmentmeifyoucan.com/datasets
    # Download via gdown (Google Drive)
    pip install gdown -q
    # RoadAnomaly21 test set (~2GB)
    gdown --fuzzy "https://drive.google.com/file/d/1zt2a-EXDOidBaJLNBmcHOIXr4J3pGAJg" \
        -O RoadAnomaly21.zip || \
    echo "  [WARN] RoadAnomaly21 requires manual download from https://segmentmeifyoucan.com/"
    [ -f RoadAnomaly21.zip ] && unzip -q RoadAnomaly21.zip && echo "RoadAnomaly21: OK"

    # BDD100K normal frames (subset) — use val split
    echo "  [INFO] BDD100K normal negatives: download from https://www.bdd100k.com/"
    echo "  Register and download val images (~1GB subset needed)"
}

# ─── D6: SDNET2018 ───────────────────────────────────────────────────────────
download_sdnet() {
    echo "=== D6: SDNET2018 ==="
    mkdir -p "$DATA_DIR/SDNET2018"
    cd "$DATA_DIR/SDNET2018"
    # Mendeley Data (direct)
    wget -c "https://data.mendeley.com/public-files/datasets/z44wpry24t/files/ba3c31fe-55d2-4f5e-b2ac-81fb4e1e3a96/file_downloaded" \
        -O SDNET2018.zip || \
    echo "  [WARN] SDNET2018: download from https://data.mendeley.com/datasets/z44wpry24t"
    [ -f SDNET2018.zip ] && unzip -q SDNET2018.zip && echo "SDNET2018: OK"
}

# ─── D2: PIDray ──────────────────────────────────────────────────────────────
download_pidray() {
    echo "=== D2: PIDray (X-ray baggage) ==="
    mkdir -p "$DATA_DIR/PIDray"
    cd "$DATA_DIR/PIDray"
    # Official GitHub: https://github.com/bywang2018/security-dataset
    # Usually requires request — check for mirror
    echo "  [INFO] PIDray: request access at https://github.com/bywang2018/security-dataset"
    echo "  Alternatively use SIXray: pip install huggingface_hub"
    python3 -c "
from huggingface_hub import snapshot_download
try:
    snapshot_download(repo_id='SIXray/SIXray', repo_type='dataset',
                      local_dir='/hdd1/jiangxi/AD-Agent/benchmark/data/SIXray',
                      endpoint='https://hf-mirror.com')
    print('SIXray downloaded as D2 fallback')
except Exception as e:
    print(f'SIXray download failed: {e}')
    print('Try: HF_ENDPOINT=https://hf-mirror.com huggingface-cli download ...')
" 2>/dev/null || echo "  [WARN] PIDray/SIXray: manual download needed"
}

# ─── D3: CheXpert (NIH ChestXray14 is large; use CheXpert-small as fallback) ─
download_medical() {
    echo "=== D3: Medical Chest X-ray ==="
    mkdir -p "$DATA_DIR/CheXpert"
    cd "$DATA_DIR/CheXpert"
    # CheXpert-small (direct from Stanford)
    wget -c "https://stanfordaimi.azurewebsites.net/datasets/8cbd9ed4-2eb9-4565-affc-111cf4f7ebe2" \
        -O chexpert_info.html 2>/dev/null || true
    # Use HuggingFace mirror for CheXpert-small
    python3 -c "
from huggingface_hub import snapshot_download
try:
    snapshot_download(repo_id='StanfordAIMI/CheXpert-v1.0-small', repo_type='dataset',
                      local_dir='/hdd1/jiangxi/AD-Agent/benchmark/data/CheXpert',
                      endpoint='https://hf-mirror.com')
    print('CheXpert-small downloaded')
except Exception as e:
    print(f'CheXpert download failed: {e}')
    print('[WARN] Manual download: https://stanfordaimi.azurewebsites.net/datasets/edead88e-e8eb-4f5a-9d45-a2e8f8e46ed1')
"
}

# ─── D4: xBD (xView2 Building Damage) ────────────────────────────────────────
download_xbd() {
    echo "=== D4: xBD Remote Sensing ==="
    echo "  [INFO] xBD requires registration at https://xview2.org/"
    echo "  After download, place at: $DATA_DIR/xBD/"
    echo "  Alternative: use LEVIR-CD (change detection) as proxy"
    mkdir -p "$DATA_DIR/LEVIR-CD"
    python3 -c "
from huggingface_hub import snapshot_download
try:
    snapshot_download(repo_id='LEVIR/LEVIR-CD', repo_type='dataset',
                      local_dir='/hdd1/jiangxi/AD-Agent/benchmark/data/LEVIR-CD',
                      endpoint='https://hf-mirror.com')
    print('LEVIR-CD downloaded as D4 fallback')
except Exception as e:
    print(f'LEVIR-CD: {e}')
"
}

# ─── Main ─────────────────────────────────────────────────────────────────────
echo "Starting dataset downloads (D1/D5 already available via MMAD)..."
echo "Using direct links first; set USE_PROXY=1 to enable proxy"
echo ""

if [ "${1}" == "avenue" ] || [ "${1}" == "all" ]; then download_avenue; fi
if [ "${1}" == "road"   ] || [ "${1}" == "all" ]; then download_roadanomaly; fi
if [ "${1}" == "sdnet"  ] || [ "${1}" == "all" ]; then download_sdnet; fi
if [ "${1}" == "pidray" ] || [ "${1}" == "all" ]; then download_pidray; fi
if [ "${1}" == "medical"] || [ "${1}" == "all" ]; then download_medical; fi
if [ "${1}" == "xbd"    ] || [ "${1}" == "all" ]; then download_xbd; fi

if [ -z "${1}" ]; then
    echo "Usage: bash download_datasets.sh [avenue|road|sdnet|pidray|medical|xbd|all]"
    echo ""
    echo "Status of domains:"
    echo "  D1 Industrial:   READY (MVTec-AD in MMAD)"
    echo "  D5 Retail:       READY (GoodsAD in MMAD)"
    echo "  D2 Screening:    NEEDS DOWNLOAD (PIDray or SIXray)"
    echo "  D6 Maintenance:  NEEDS DOWNLOAD (SDNET2018)"
    echo "  D3 Medical:      NEEDS DOWNLOAD (CheXpert-small)"
    echo "  D4 RemoteSens:   NEEDS DOWNLOAD (xBD or LEVIR-CD)"
    echo "  D7 Road:         NEEDS DOWNLOAD (RoadAnomaly21 + BDD100K)"
    echo "  D8 Surveillance: NEEDS DOWNLOAD (Avenue)"
fi
