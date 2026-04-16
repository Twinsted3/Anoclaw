# Experiment Bridge Guide for AnomalyClaw

This document specifies all experiments needed to populate the paper's `\tbd{}` placeholders.
Use with `/experiment-bridge` to implement and run these experiments.

## 1. Dataset Reorganization

### New Domain Coding (CRITICAL: must match paper)
The 12 domains have been re-encoded sequentially by type:

| New Code | Domain | Source | Old Code | Status |
|----------|--------|--------|----------|--------|
| D1 | Industrial Manufacturing | MVTec-AD | D1 | ✅ Ready |
| D2 | Retail Products | GoodsAD | D2 | ✅ Ready |
| D3 | Complex Industrial | VisA | D10 | ✅ Ready |
| D4 | Infrastructure | SDNET2018 | D4 | ✅ Ready |
| D5 | Logical Anomaly | MVTec-LOCO | D9 | ✅ Ready |
| D6 | 3D Product (RGB) | Real3D-AD | NEW | ⚠️ Needs rendering |
| D7 | Remote Sensing | LEVIR-CD+ | D6 | ✅ Ready (158 items) |
| D8 | Dermatology | DermaMNIST/ISIC | D5 | ✅ Ready |
| D9 | Brain MRI | BraTS2021 | D5b | ✅ Ready |
| D10 | Liver CT | BMAD-Liver | D5c | ✅ Ready |
| D11 | GI Endoscopy | HyperKvasir | D5d | ✅ Ready |
| D12 | Road Safety | BDD100K + RA21 | D7 | ✅ Ready |

### New Domains

**D6: Real3D-AD (3D Product Inspection)**
- Data location: `/hdd3/ljq/3dad_demo_more_pcd/`
- Format: Point clouds (.pcd), needs rendering to 2D RGB
- Rendering script: `benchmark/scripts/render_real3d.py`
- Run: `python benchmark/scripts/render_real3d.py --data_root /hdd3/ljq/3dad_demo_more_pcd --output_dir benchmark/data/Real3D-AD-RGB`
- Categories: airplane, candybar, diamond, duck, fish, seahorse, shell, starfish, etc.
- Normal = `*_good.pcd`, Anomaly = `*_bulge.pcd`, `*_sink.pcd`, etc.

**D7: LEVIR-CD+ (Remote Sensing)**
- Data location: `benchmark/data/LEVIR-CD/`
- Already has 1970 extracted images and manifest (D6 in old system)
- Remap: old D6 → new D7

**MVTec-3D (optional, needs download)**
- Download from: https://www.mvtec.com/company/research/datasets/mvtec-3d-ad/downloads
- Requires registration. Has real RGB images alongside 3D point clouds.
- Can be added as D13 or replace D6 once downloaded.

### VisA (D3) Category Selection
Select categories that showcase multi-object and complex textures:
- **Multi-object**: PCB1, PCB2, PCB3, PCB4 (circuit boards with multiple components)
- **Complex texture**: Capsules, Candle, Cashew, Macaroni1, Macaroni2
- Sample 60 normal + 60 anomalous across these categories proportionally

### Action Items
- [ ] Run `python benchmark/scripts/render_real3d.py` to render Real3D-AD point clouds
- [ ] Run `python benchmark/scripts/build_manifest_v2.py` to build D1-D12 manifests
- [ ] Verify VisA (D3) emphasizes multi-object and complex categories
- [ ] Keep 120 images per domain (60 normal, 60 anomalous)
- [ ] Fixed random seed = 42

## 2. Core System Implementation: Adversarial Debate

### 2.1 Proposer-Refuter → Proposer-Advocate ✅ DONE
- ✅ Renamed Refuter → Normality Advocate in `vad2_prompts.py`
- ✅ Expert evidence integrated into Proposer prompts
- ✅ `vad2_system.py` now accepts `query_path`, `ref_paths`, `domain_code`
- ✅ Prompts switched to English for VLM-agnostic compatibility

### 2.2 Expert Pool Implementation ✅ DONE (`experts.py`)
Created with 3 experts:

1. **Visual retrieval expert** (partially exists):
   - DINOv2 CLS-token retrieval already implemented
   - Need: Generate structured text report (similarity scores, rank info)

2. **Texture statistics expert** (new):
   - Compute Gram matrix statistics between query and reference features
   - Report texture similarity score and notable deviations

3. **Expert interface**: Each expert should implement:
   ```python
   def analyze(query_image, reference_images, domain_code) -> str:
       """Return structured text report."""
   ```

### 2.3 Autonomous Controller
New component. Implement in `controller.py` or extend `vad2_system.py`:

1. **Expert selection logic**:
   - Always run retrieval expert (lightweight)
   - Run patch expert unless global similarity > 0.95 (clearly normal)
   - Run texture expert for industrial domains (D1-D4)
   - Domain-specific experts triggered by domain code

2. **Debate depth control**:
   - D_max = 1 if initial Proposer confidence > 0.8 or < 0.2 (clear case)
   - D_max = 2 otherwise (default)
   - D_max = 3 for domains with known difficulty (medical)

3. **Verdict logic** (already in `_aggregate()`):
   - Any Valid claim → anomalous
   - All Invalid or no claims → normal
   - TBD remains → uncertain

## 3. Experiments to Run

### 3.1 Main Results Table (Table 3 in paper)
Run ALL of the following on all 10 domains:

**Expert-only baselines:**
- `CLIP-ZeroShot`: Zero-shot CLIP with "normal/defective" prompt templates
- `WinCLIP`: Official WinCLIP implementation (or reimplementation)
- `PatchCore Expert`: Existing patch expert, k=4, top-1%

**Single-pass VLM baselines:**
- `VLM-Direct`: VLM sees only query image, no references
- `Retrieval+VLM`: DINOv2 retrieval + VLM comparison (existing Ret+VLM)
- `Expert-Informed VLM`: Retrieval + patch expert text + single VLM call (existing Expert-Informed VLM)

**Multi-round/agent baselines:**
- `AgentIAD`: Implement their iterative tool-calling strategy (or use their codebase)
- `Symmetric Debate`: Two identical VLM agents debating (same prompt, no Proposer/Advocate roles, no expert evidence)

**Our method:**
- `AnomalyClaw`: Full system with debate + expert pool + autonomous controller

### 3.2 Debate Ablation (Table 4)
All on 10 domains, same VLM backend:
| Config | Expert | Debate |
|--------|--------|--------|
| Single-pass, no expert | None | No |
| Single-pass, with expert | Patch+Retrieval | No |
| Symmetric debate, no expert | None | Symmetric |
| Symmetric debate, with expert | Patch+Retrieval | Symmetric |
| AnomalyClaw (asymmetric) | Patch+Retrieval | Asymmetric |

### 3.3 Expert Pool Ablation (Table 5)
All use asymmetric debate:
| Config | Experts used |
|--------|-------------|
| Debate only | None |
| Retrieval only | Retrieval |
| Patch only | Patch |
| Patch + Retrieval | Patch + Retrieval |
| Patch + Retrieval + Texture | All |

### 3.4 Debate Depth Ablation (Table 6)
AnomalyClaw with D_max = {1, 2, 3, 4}
Report: Macro AUROC + average VLM calls per query

### 3.5 Multi-VLM Generalization (Table 7)
Run AnomalyClaw + single-pass baseline with:
- GPT-4o (or GPT-4.1)
- GPT-5.4
- At least one open-source VLM (InternVL, Qwen2.5-VL, or similar)

For each VLM, report both single-pass and AnomalyClaw AUROC.

### 3.6 Cost-Accuracy Pareto Plot
Compute for each method:
- Total VLM tokens per 100 queries
- Macro AUROC
Plot Pareto frontier. AnomalyClaw should dominate symmetric debate.

### 3.7 Per-Domain Analysis
For the analysis section, compute:
- Debate gain per domain: AnomalyClaw AUROC - Expert-Informed VLM AUROC
- Average debate depth per domain
- Expert selection frequency per domain
- Identify worst domain and prepare failure analysis

## 4. Implementation Priority

### Phase 1: Core (must have)
1. Dataset reorganization (new D1-D10 mapping)
2. Expert evidence → Proposer prompt integration
3. Basic autonomous controller (expert selection + depth)
4. Run main results table (Table 3)

### Phase 2: Ablations
5. Debate ablation (Table 4)
6. Expert pool ablation (Table 5)
7. Depth ablation (Table 6)

### Phase 3: Generalization
8. Multi-VLM experiments (Table 7)
9. Cost-accuracy analysis
10. Failure analysis

## 5. Expected Results

Based on codebase analysis, the debate mechanism (vad2_system.py) already shows:
- Multi-round convergence with TBD resolution
- Proposer-Refuter asymmetry
- JSON-structured claims with confidence scores

Key hypotheses to validate:
1. **Debate > single-pass**: The built-in self-verification should catch VLM hallucinations
2. **Asymmetric > symmetric**: Proposer-Advocate asymmetry prevents collective delusion
3. **Expert grounding helps debate**: Structured evidence anchors claims in quantitative data
4. **Autonomous control saves cost**: Easy queries (D10 road safety) should converge in 1 round

## 6. Files to Modify

| File | Change |
|------|--------|
| `vad2_system.py` | Add expert evidence to Proposer prompt; rename Refuter → Advocate |
| `vad2_prompts.py` | Update prompt templates with expert evidence slots |
| `vad2_tools_mm.py` | Add retrieval expert and texture expert modules |
| `inference.py` | Update dataset loading for new D1-D10 codes |
| `utils.py` | Update domain mapping |
| New: `controller.py` | Autonomous controller logic |
| New: `experts.py` | Expert pool interface and implementations |
| New: `baselines/` | Baseline implementations (CLIP-ZeroShot, WinCLIP, etc.) |
