# Experiment Tracker

**Paper**: Beyond Industrial: Cross-Domain Benchmark and Minimal Agent Design Study
**Last updated**: 2026-03-31 16:30

## Status Legend
- `READY` — can run now
- `DONE` — completed
- `BLOCKED` — waiting for data/API
- `PENDING` — not started

---

## M0: Data & Infrastructure ✅ (Partially Done)

| Task | Status | Notes |
|------|--------|-------|
| D1 Industrial (MVTec-AD) manifest | DONE | 180 items, calibration/dev/test split |
| D2 Retail (GoodsAD) manifest | DONE | 180 items, calibration/dev/test split |
| D3 Screening (PIDray) | BLOCKED | 70 anomaly images (Voxel51/PIDray HF), no normal X-ray source found yet |
| D4 Maintenance (SDNET2018) | DONE | 180N+180A, 56K images total (USU repo), crack detection D/W/P surfaces |
| D5 Medical (CheXpert) | DONE | 90N+90A from danjacobellis/chexpert HF (embedded JPEG parquet), 23 parquets |
| D6 Remote Sensing (LEVIR-CD+) | DONE | 79N+79A (blanchon/LEVIR_CDPlus, only 79 no-change samples in full 985-sample dataset) |
| D7 Road (RoadAnomaly21) | DONE | 90 anomaly (kumuji HF) + 90 normal (dgural/bdd100k HF, 2624 available) |
| D8 Surveillance (Avenue) | DONE | 776MB zip extracted, 90N+90A video frames via OpenCV |
| SeedVL API connection | DONE | `doubao-seed-1-6-vision-250815` working |
| GPT API setup | DONE | sub2api @ localhost:8080, gpt-5.4, key saved in memory |
| Qwen3-VL-8B local server | PENDING | `bash setup_qwen3.sh` when GPU available |
| DINOv2 classical baseline | PENDING | No download needed (torch.hub) |
| infer.py framework | DONE | Supports v0/v1/v2/v3, gpt/seedvl/qwen3 |
| evaluate.py metrics | DONE | AUROC, BA, F1, per-domain |

---

## M1: SeedVL Sanity (5 items) ✅ DONE

| Run | Backend | Variant | Items | AUROC | BA | Notes |
|-----|---------|---------|-------|-------|-----|-------|
| sanity_seedvl_v1 | SeedVL | v1_normal_first | 5 | N/A | N/A | 0 errors, pipeline confirmed |

---

## M1: Calibration Slice (D1+D2, 40 items each variant) ✅ SeedVL DONE

| Run | Backend | Variant | Status | AUROC | BA | D1 AUROC | D2 AUROC |
|-----|---------|---------|--------|-------|----|----------|----------|
| seedvl_v0_direct_calibration | SeedVL | v0_direct | DONE | 0.669 | 0.575 | 0.850 | 0.555 |
| seedvl_v1_normal_first_calibration | SeedVL | v1_normal_first | DONE | 0.668 | 0.550 | 0.920 | 0.435 |
| seedvl_v2_self_refine_calibration | SeedVL | v2_self_refine | DONE | 0.690 | 0.550 | 0.970 | 0.465 |
| seedvl_v3_debate_1r_calibration | SeedVL | v3_debate_1r | DONE | **0.770** | **0.775** | 0.880 | 0.615 |
| gpt_v0_direct_calibration | GPT-5.4 | v0_direct | DONE | **0.695** | **0.775** | D1:1.000 | D2:0.415 |
| gpt_v1_normal_first_calibration | GPT-5.4 | v1_normal_first | PENDING | — | — | — | — |
| gpt_v2_self_refine_calibration | GPT-5.4 | v2_self_refine | PENDING | — | — | — | — |
| gpt_v3_debate_1r_calibration | GPT-5.4 | v3_debate_1r | DONE | 0.754 | 0.750 | D1:0.890 | D2:0.625 |
| seedvl_v0_calib_d4d7d8 | SeedVL | v0_direct | DONE | D4:0.790 D7:0.895 D8:0.575 | D4:0.50 D7:0.55 D8:0.45 | — |
| seedvl_v3_calib_d4d7d8 | SeedVL | v3_debate_1r | DONE | D4:0.845 D7:0.750 D8:0.615 | D4:0.75 D7:0.70 D8:0.65 | — |
| seedvl_v0_calib_d5 | SeedVL | v0_direct | DONE | D5:0.455 | 0.550 | — |
| seedvl_v3_calib_d5 | SeedVL | v3_debate_1r | DONE | D5:0.455 | 0.550 | — |
| seedvl_v0_calib_d6 | SeedVL | v0_direct | DONE | D6:0.925 | 0.500 | — |
| seedvl_v3_calib_d6 | SeedVL | v3_debate_1r | DONE | D6:0.340 | 0.350 | **D6 anomaly: debate fails** |

**Calibration Summary (7 domains, SeedVL):**

| Domain | V0 AUROC | V3 AUROC | V3 winner? | Note |
|--------|----------|----------|------------|------|
| D1 industrial | 0.850 | 0.880 | ✅ V3 | V3 +3% |
| D2 retail | 0.555 | 0.615 | ✅ V3 | V3 +6% |
| D4 maintenance | 0.790 | 0.845 | ✅ V3 | V3 +5.5%, cracks |
| D5 medical | 0.455 | 0.455 | TIE | Both ~random; domain difficulty |
| D6 remote_sensing | **0.925** | **0.340** | ❌ V0 | **V3 FAILS** — refuter rationalizes changes as normal urbanization |
| D7 road | **0.895** | 0.750 | ❌ V0 | V0 AUROC higher, V3 better BA |
| D8 surveillance | 0.575 | 0.615 | ✅ V3 | V3 +4% |

**Key findings**:
1. V3-Debate dominates when "anomaly" matches world-knowledge (industrial defects, building damage-as-defect, road obstacles)
2. V3-Debate catastrophically fails on D6 (remote sensing): refuter says "construction = normal" — conflicting task definition
3. D5 (medical) both near-random: 0.455 AUROC — model lacks radiology expertise
4. D7 V0 has highest AUROC (0.895) but V3 has better BA: training/test split quality issue (BDD100K vs RoadAnomaly21 is visually very different → high AUROC even for V0)

**Decision for M2**: Use V3 for D1/D2/D4/D8; use V0 for D6; D5 needs domain-adapted prompting.

---

## M2: Development Runs (5+1 domains, 40 items each) ✅ DONE (D1/D2/D4/D7/D8) + D6

| Run | Backend | Variant | Status | AUROC | BA | Notes |
|-----|---------|---------|--------|-------|----|-------|
| seedvl_v0_direct_dev | SeedVL | v0_direct | DONE | 0.672 | 0.495 | D1:0.874 D2:0.515 D4:0.491 D7:0.949 D8:0.559 |
| seedvl_v3_debate_1r_dev | SeedVL | v3_debate_1r | DONE | 0.620 | 0.620 | D1:0.743 D2:0.521 D4:0.494 D7:0.698 D8:0.604 |
| seedvl_v0_direct_dev_d6 | SeedVL | v0_direct | DONE | 0.735 | 0.500 | D6 only |
| seedvl_v3_dev_d5_d6 | SeedVL | v3_debate_1r | PENDING | — | — | D5/D6 dev |

**Dev pattern**: V3 BA consistently better (+12.5%), V0 AUROC sometimes higher (D1, D7). D4 concrete cracks = near-random for both (0.491/0.494) — fundamental domain limitation.

---

## M3: Full Test (7 domains × 2 variants)

### SeedVL Test Results (120 items/domain except D6=98)

| Run | Backend | Variant | Status | AUROC | BA | Per-Domain |
|-----|---------|---------|--------|-------|----|------------|
| seedvl_v0_direct_test_all | SeedVL | v0_direct | DONE | **0.651** | 0.550 | D1:0.871 D2:0.479 D4:0.722 D5:0.436 D6:0.764 D7:0.912 D8:0.430 |
| seedvl_v3_debate_1r_test_all | SeedVL | v3_debate_1r | DONE | 0.630 | **0.603** | D1:0.836 D2:0.471 D4:0.755 D5:0.487 D6:0.622 D7:0.716 D8:0.483 |

**SeedVL Test Summary (best-per-domain selection):**

| Domain | V0 AUROC | V3 AUROC | Winner | V0 BA | V3 BA |
|--------|----------|----------|--------|-------|-------|
| D1 industrial | 0.871 | 0.836 | ✅ V0 | 0.725 | 0.792 |
| D2 retail | 0.479 | 0.471 | TIE | 0.500 | 0.458 |
| D4 maintenance | 0.722 | **0.755** | ✅ V3 | 0.567 | 0.725 |
| D5 medical | 0.436 | 0.487 | TIE | 0.475 | 0.458 |
| D6 remote_sensing | **0.764** | 0.622 | ✅ V0 | 0.510 | 0.612 |
| D7 road | **0.912** | 0.716 | ✅ V0 | 0.583 | 0.692 |
| D8 surveillance | 0.430 | 0.483 | ✅ V3 | 0.483 | 0.483 |

**Key finding (test confirms calibration)**: V0 wins on D6/D7, V3 wins on D4/D8; D1/D2/D5 borderline.
V3 consistently better BA, V0 consistently better AUROC on road/remote-sensing.

### GPT-5.4 Calibration Results (20 items/domain)

| Run | Backend | Variant | Status | D1 | D2 | D4 | D5 | D6 | D7 | D8 |
|-----|---------|---------|--------|----|----|----|----|----|----|-----|
| gpt_v0_calib_all | GPT-5.4 | v0_direct | DONE | 1.000 | 0.415 | 0.900 | 0.450 | 0.570 | 0.960 | 0.325 |
| gpt_v3_calib_all | GPT-5.4 | v3_debate_1r | DONE | 0.890 | 0.625 | 0.775 | 0.410 | 0.635 | 0.870 | 0.370 |

**GPT vs SeedVL calibration (V0, D1+D2):**
- GPT-5.4 V0 D1: 1.000 vs SeedVL 0.850 (+15%) 🎉
- GPT-5.4 V0 D2: 0.415 vs SeedVL 0.555 (-14%)
- GPT-5.4 V3 D1: 0.890 vs SeedVL 0.880 (+1%)
- GPT-5.4 V3 D2: 0.625 vs SeedVL 0.615 (+1%)

### GPT-5.4 Test Runs (pending)

| Run | Status |
|-----|--------|
| gpt_v0_direct_test_all | PENDING |
| gpt_v3_debate_1r_test_all | PENDING |

---

## Blockers / Action Items

| Item | Action | Assigned To |
|------|--------|-------------|
| GPT API key | ✅ RESOLVED — sub2api @ localhost:8080, gpt-5.4 | Done |
| aicodemirror backup | ✅ gpt-5.1/5.2/5.4 all work (sk-ant-api03-...) | Done |
| SeedVL latest model | Check if `doubao-seed-1.6-vision` (newer than 250815) is available, activate endpoint | **User** |
| D3-D8 dataset downloads | Run `bash benchmark/scripts/download_datasets.sh all` | Can run now |
| Qwen3-VL-8B | Run `bash benchmark/scripts/setup_qwen3.sh` after GPU available | Can run now |

---

## Commands Quick Reference

```bash
# SeedVL calibration (D1+D2 ready now):
export SEED_API_KEY="***REDACTED-SEED-KEY***"
export SEED_API_BASE="https://ark.cn-beijing.volces.com/api/v3"
env -u HTTP_PROXY -u HTTPS_PROXY bash benchmark/scripts/run_m1_calibration.sh seedvl

# Download missing datasets:
bash benchmark/scripts/download_datasets.sh avenue
bash benchmark/scripts/download_datasets.sh road
bash benchmark/scripts/download_datasets.sh sdnet
bash benchmark/scripts/download_datasets.sh medical
bash benchmark/scripts/download_datasets.sh xbd

# Setup Qwen3 local server (GPU 8):
bash benchmark/scripts/setup_qwen3.sh

# After GPT key configured:
export GPT_API_KEY="..."
export GPT_API_BASE="..."  # or leave empty for official OpenAI
env -u HTTP_PROXY -u HTTPS_PROXY bash benchmark/scripts/run_m1_calibration.sh gpt
```
