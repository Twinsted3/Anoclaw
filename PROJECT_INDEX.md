# AnomalyClaw Project Index

**Last updated**: 2026-04-16
**Status**: Qwen3.5 agent validated (+6.28pp over direct, significant). GPT/SeedVL pending.

---

## 1. Resources

### VLM Backends
| Backend | Model | Endpoint | Status |
|---------|-------|----------|--------|
| Qwen3.5-VL-27B | /hdd1/models/Qwen3.5-27B-FP8 | localhost:8200-8203 (4 replicas) | Active |
| SeedVL | doubao-seed-2-0-lite-260215 | ark.cn-beijing.volces.com | Active (key in infer.py) |
| GPT-5.4 | chatgpt-4o-latest | localhost:8080/v1 (sub2api) | Broken (routes to gpt-5.1) |

### Expert Models
| Expert | Backbone | Checkpoint | Cache Files |
|--------|----------|------------|-------------|
| SubspaceAD | DINOv2-giant, PCA 99%EV | experts/SubspaceAD/ | subspacead_calibration.json, subspacead_test.json |
| AnomalyVFM | DINOv2 + LoRA decoder | experts/AnomalyVFM/checkpoints/dinov2_model.pkl | anomalyvfm_calibration.json, anomalyvfm_test.json |
| DINOv2 Patch-kNN | DINOv2-giant 48x48 grid | (computed from backbone) | classical_dinov2_patch_test_all.json |
| DINOv2 Global | DINOv2-giant CLS token | (computed from backbone) | classical_dinov2_global_test_all.json |

### Benchmark
| Item | Path |
|------|------|
| Manifest (v1, 12 domain codes) | benchmark/manifests/full_manifest.json |
| Manifest (v2, 12 domains renumbered) | benchmark/manifests_v2/full_manifest.json |
| Retrieval index | benchmark/retrieval_index/*_index.npz |
| Domain data | benchmark/data/, MMAD/dataset/ |

---

## 2. Key Code Files

### Active (current agent)
| File | Purpose |
|------|---------|
| `benchmark/scripts/run_anomaclaw_v3.py` | **Main agent runner**: ReAct + fusion + tools + per-domain plan |
| `benchmark/scripts/react_skill.py` | Skill prompt: teaches VLM when/how to use each tool |
| `benchmark/scripts/additional_tools.py` | image_diff, segment_and_count, anomaly_heatmap_text |
| `benchmark/scripts/infer.py` | Core inference: run_v0, run_v3, call_llm, scoring, prompts |
| `benchmark/scripts/agent_tools.py` | tool_visual_retrieval, tool_domain_knowledge, tool_expert_ad_score |
| `benchmark/scripts/expert_subspacead.py` | SubspaceAD benchmark wrapper |
| `benchmark/scripts/expert_anomalyvfm.py` | AnomalyVFM benchmark wrapper |
| `benchmark/scripts/vllm_lb.py` | Round-robin load balancer for 4 vLLM replicas |

### Analysis scripts
| File | Purpose |
|------|---------|
| `refine-logs/aggregate_strategy_matrix.py` | Per-(backbone, domain, strategy) AUROC matrix |
| `refine-logs/per_domain_w.py` | Per-domain optimal fusion weight from calibration |
| `refine-logs/per_domain_strategy_calib.py` | Per-domain best strategy comparison |
| `refine-logs/expert_per_domain.py` | SubspaceAD vs AnomalyVFM per-domain comparison |
| `refine-logs/update_paper_with_v3.py` | Compute agent macro AUROC + bootstrap CI |
| `refine-logs/eval_anomaclaw_v3.py` | Quick per-domain agent evaluation |

### Paper
| File | Purpose |
|------|---------|
| `paper/main.tex` | Main document (NeurIPS 2025 template) |
| `paper/sections/{0-5,A}_*.tex` | Abstract, intro, related, method, experiments, conclusion, appendix |
| `paper/references.bib` | 30 entries |
| `paper/figures/gen_*.py` | 13 figure generation scripts |

---

## 3. Exploration History

### Strategy variants tested (all on Qwen3.5 test, n=1418)

| Variant | Macro AUROC | vs Direct | File |
|---------|-------------|-----------|------|
| Direct VLM (v0) | 0.776 | baseline | qwen35_v0_direct_test_all_v2.json |
| Normal-first (v1) | — | tested calib only | qwen35_v1_normal_first_calibration_egra.json |
| Self-refine (v2) | — | -5.9pp on GPT calib | qwen35_v2_self_refine_calibration_egra.json |
| Debate 1-round (v3) | 0.659 | -11.7pp | qwen35_v3_debate_1r_test_all_v2.json |
| EGRA interpret | 0.778 | +0.2pp | qwen35_egra_test_all_v2.json |
| Grounded debate | 0.665 | -11.1pp (GPT only) | gpt54_v3_grounded_test_all_v2.json |
| Fusion (w=0.2, SubspaceAD) | 0.831 | +5.5pp | (computed from v0 + subs) |
| **Agent v4 (per-domain calib argmax)** | **0.831** | **+5.5pp** | anomaclaw_v4_qwen35_test.json |
| **Agent final (react + multi-expert)** | **0.839** | **+6.3pp** | (combined from react + fusion files) |

### Per-domain tool/expert/strategy exploration

#### D1 Industrial (MVTec-AD, 15 categories)
- **Direct**: 0.903. FN=10 (subtle scratches), FP=4 (capsule logo hallucination)
- **Fusion(SubspaceAD)**: 0.976. Expert catches all 10 FN items
- **React v1**: 0.975. hotspot_cropper fixed 3 FN (D1_0095, D1_0166, D1_0104); reference_profiler fixed all 4 FP
- **React v2**: 0.976. Marginal improvement over v1
- **Best**: react ≈ fusion. Tools add interpretability + fix specific FP

#### D2 Retail (GoodsAD, 6 categories)
- **Direct**: 0.672. 48/60 FN (80% miss rate!)
- **Fusion(SubspaceAD)**: 0.828. Expert fusion recovers many FN
- **React v2**: 0.854 (+2.6pp over fusion). reference_profiler learns product patterns
- **Best**: react. Reference retrieval not yet tested (could help with category matching)

#### D4 Infrastructure (SDNET2018, 3 categories: deck/wall/pavement)
- **Direct**: 0.712. 33 FN (thin cracks), 7 FP
- **Fusion(SubspaceAD)**: 0.600 on calibration (SubspaceAD AUROC=0.50, near random)
- **Fusion(AnomalyVFM)**: 0.744 (+3.2pp over direct). AnomalyVFM calib=0.72 much better
- **Best**: fusion_avfm. Expert selection matters here

#### D5 Dermoscopy (DermaMNIST)
- **Direct**: 0.762. 12 FN, 21 FP
- **Fusion(SubspaceAD)**: 0.808. Expert helps
- **React**: not tested directly; calibration zoom_fusion was 0.825
- **Best**: fusion_subs

#### D5b Brain MRI (BraTS2021)
- **Direct**: 0.849. 1 FN, 33 FP (massive over-detection!)
- **Fusion(SubspaceAD)**: 0.942. Expert corrects most FP
- **React v2**: 0.963 (+2.1pp over fusion). Asymmetric policy + crop verify FP
- **Best**: react. Tools reduce FP on brain MRI

#### D5c Liver CT (BMAD)
- **Direct**: 0.684. 36 FN (VLM misses focal lesions)
- **Fusion(SubspaceAD)**: 0.771. Expert catches lesions
- **React (all variants)**: 0.664-0.687. FN drops to 0-1 but FP explodes (5→60)
- **Best**: fusion_subs. React too aggressive on liver CT

#### D5d GI Endoscopy (HyperKvasir)
- **Direct**: 0.918. VLM-strong domain
- **Fusion(SubspaceAD)**: 0.912. Expert slightly hurts (-0.7pp)
- **Best**: direct. Expert is mild distractor

#### D6 LEVIR Change Detection
- **Direct**: 0.828. Semantic task, VLM world-knowledge critical
- **Fusion(SubspaceAD)**: 0.725. Expert is major distractor (-10.3pp)
- **image_diff tool**: implemented but not yet tested on D6
- **Best**: direct. Expert must be avoided

#### D7 Road/BDD + HyperKvasir GI
- **Direct**: 0.911
- **SubspaceAD-only**: 0.984 (near perfect, calib=0.97)
- **Best**: subs_only. 0 VLM calls needed. Expert dominates

#### D8 Road/Pedestrian (Avenue/BDD)
- **Direct**: 0.598. Hardest domain, 48 FN
- **Fusion(SubspaceAD)**: 0.598. No SubspaceAD coverage → falls back to direct
- **Best**: nothing helps. Behavioral anomaly out of scope for appearance-based methods

#### D9 Logical Anomaly (MVTec-LOCO, 5 categories)
- **Direct**: 0.676. 30 FN, 11 FP
- **Fusion(SubspaceAD)**: 0.741
- **Fusion(AnomalyVFM)**: 0.710. AnomalyVFM better on calibration (0.83 vs 0.76)
- **React + component_counter**: 0.622-0.706. Counter adds noise, hurts FP
- **Best**: fusion_avfm. Component counting needs better implementation

#### D10 VisA Industrial (12 categories)
- **Direct**: 0.800. 24 FN
- **Fusion(SubspaceAD)**: 0.914 (+11.4pp). Expert very strong
- **React v2**: 0.909. Close but fusion slightly better
- **Best**: fusion_subs

---

## 4. Final Agent Architecture

```
Per-image:
  1. Look up plan(domain) → {strategy, expert, tools}
  2. If strategy=react:
     Call 1: VLM sees [refs, query, expert_signal] → {label, confidence, tool_calls}
     Execute tools: hotspot_cropper, reference_profiler (VLM-based RAG), etc.
     Call 2: VLM sees [refs, query, tool_results] → final label
     Asymmetric: if Call1=anomalous, keep it; if Call1=normal, take Call2
     Blend with expert score
  3. If strategy=fusion(expert):
     1 VLM call → blend 0.8*vlm + 0.2*sigmoid(expert)
  4. If strategy=direct:
     1 VLM call → score
  5. If strategy=subs_only:
     0 VLM calls → sigmoid(expert score)
```

---

## 5. Agent Plans

### Qwen3.5 Final Plan (refine-logs/QWEN35_AGENT_PLAN_REACT.json)
| Domain | Strategy | Expert | Avg calls/item |
|--------|----------|--------|----------------|
| D1 | react | SubspaceAD | 1.2 |
| D2 | react | SubspaceAD | 1.0 |
| D4 | fusion_avfm | AnomalyVFM | 1.0 |
| D5 | fusion_subs | SubspaceAD | 1.0 |
| D5b | react | SubspaceAD | 1.2 |
| D5c | fusion_subs | SubspaceAD | 1.0 |
| D5d | direct | — | 1.0 |
| D6 | direct | — | 1.0 |
| D7 | subs_only | SubspaceAD | 0.0 |
| D8 | fusion_subs | SubspaceAD | 1.0 |
| D9 | fusion_avfm | AnomalyVFM | 1.0 |
| D10 | fusion_subs | SubspaceAD | 1.0 |
