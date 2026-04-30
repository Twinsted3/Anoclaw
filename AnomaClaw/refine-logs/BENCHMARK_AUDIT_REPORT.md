# Benchmark Data Quality & Model Analysis Report

**Date**: 2026-03-31 | **Version**: V0-V3 Test Results Analysis

---

## Summary

**Data Quality Issues Found**: 3/7 domains have fundamental label/definition problems
**Model Bias Issue**: V0 exhibits systematic false-positive bias (Specificity << Sensitivity)
**Improvement Analysis**: V3-Debate structure helps in some domains but overcorrects in others

---

## 1. Manifest Statistics (All Balanced 50% Anomaly Ratio)

| Domain | Code | Dataset | Total Items | Calib | Dev | Test | Anomaly % |
|--------|------|---------|-------------|-------|-----|------|-----------|
| Industrial | D1 | MVTec-AD | 180 | 20 | 40 | 120 | 50% |
| Retail | D2 | GoodsAD | 180 | 20 | 40 | 120 | 50% |
| Maintenance | D4 | SDNET2018 | 180 | 20 | 40 | 120 | 50% |
| Medical | D5 | CheXpert | 180 | 20 | 40 | 120 | 50% |
| Remote Sensing | D6 | LEVIR-CD+ | 98 | 20 | 40 | 98 | 50% |
| Road | D7 | BDD100K | 180 | 20 | 40 | 120 | 50% |
| Surveillance | D8 | Avenue | 180 | 20 | 40 | 120 | 50% |

---

## 2. Confusion Matrices & Sensitivity/Specificity Analysis

### V0 Direct (Baseline)

| Domain | TP | FP | TN | FN | Sensitivity | Specificity | BA |
|--------|----|----|----|----|-------------|-------------|-----|
| D1 industrial | 58 | 31 | 29 | 2 | **96.7%** | 48.3% | 72.5% |
| D2 retail | 59 | 59 | 1 | 1 | 98.3% | **1.7%** 🔴 | 50.0% |
| D4 maintenance | 58 | 50 | 10 | 2 | 96.7% | 16.7% | 56.7% |
| D5 medical | 50 | 53 | 7 | 10 | 83.3% | **11.7%** 🔴 | 47.5% |
| D6 remote_sensing | 49 | 48 | 1 | 0 | 100.0% | 2.0% 🔴 | 51.0% |
| D7 road | 60 | 50 | 10 | 0 | 100.0% | 16.7% | 58.3% |
| D8 surveillance | 56 | 58 | 2 | 4 | 93.3% | **3.3%** 🔴 | 48.3% |

**V0 Problem**: **Extremely low Specificity across most domains** → Model systematically predicts "anomaly" even for normal samples.

### V3 Debate (Advocate + Skeptic)

| Domain | TP | FP | TN | FN | Sensitivity | Specificity | BA |
|--------|----|----|----|----|-------------|-------------|-----|
| D1 industrial | 53 | 18 | 42 | 7 | 88.3% | **70.0%** ✅ | 79.2% |
| D2 retail | 32 | 37 | 23 | 28 | 53.3% | 38.3% | 45.8% |
| D4 maintenance | 52 | 25 | 35 | 8 | 86.7% | **58.3%** ✅ | 72.5% |
| D5 medical | 30 | 35 | 25 | 30 | 50.0% | 41.7% | 45.8% |
| D6 remote_sensing | 33 | 22 | 27 | 16 | 67.3% | **55.1%** ✅ | 61.2% |
| D7 road | 32 | 9 | 51 | 28 | 53.3% | **85.0%** ✅ | 69.2% |
| D8 surveillance | 17 | 19 | 41 | 43 | 28.3% | **68.3%** ✅ | 48.3% |

**V3 Improvement**: Specificity improves dramatically (5-40% gain) in most domains, but **Sensitivity collapses** on D2/D5/D8.

---

## 3. Root Cause Analysis by Domain

### ✅ GOOD DOMAINS (Specificity > 40%)

#### **D1 Industrial (MVTec-AD)** — AUROC: 0.871 (V0), 0.836 (V3)

**Why it works:**
- **Clear domain definition**: "Defect = visible physical anomaly on manufacturing part"
- **Distinct normal vs anomaly**: Normal = undamaged surface (texture, pattern, embossing); Anomaly = broken/deformed/frayed/stained
- **Model reasoning is valid**: Correctly identifies texture differences as defects

**Example True Negative (V0):**
```
Item: bottle normal
Score: 0.10
Reasoning: "ring structure, surface texture, and reflective patterns align with normal
reference states, showing no distinct anomalies"
✅ CORRECT: Model recognizes consistent texture
```

**Example True Positive (V0):**
```
Item: carpet anomaly (frayed/knotted)
Score: 0.90
Reasoning: "irregular cluster of threads in middle of woven texture, differing from
uniform pattern of references"
✅ CORRECT: Detects actual physical defect
```

**Example False Positive (V0):**
```
Item: grid normal (but visually different shading)
Score: 0.90
Reasoning: "lacks 3D shading/highlighting present in reference, showing flat uniform diamond"
❌ INCORRECT: Treats lighting/shading difference as defect (minor issue)
```

---

#### **D7 Road (BDD100K)** — AUROC: 0.912 (V0), 0.716 (V3)

**Why it works:**
- **Clear semantic meaning**: Anomaly = road hazards (obstacle, debris, unusual object)
- **Strong visual separation**: Normal road = clear lane; Anomaly = person/object in road
- **V0 excels here**: Sensitivity=100%, but overfits on V3 (Sensitivity drops to 53%)

**V3 Problem on D7**: Debate structure makes the model too conservative, missing actual hazards.

---

### ❌ PROBLEMATIC DOMAINS (Specificity < 20%)

#### **D2 Retail (GoodsAD)** — AUROC: 0.479 (V0), 0.471 (V3)

**The Core Problem:**
- **Ambiguous task definition**: What is "anomaly"?
  - Option A: "Visual difference from reference" → Treats any product variant as anomaly
  - Option B: "Actual product damage/defect" → Cannot distinguish from Option A

**Evidence from data:**

| Sample Type | GT | Pred (V0) | Model Reasoning |
|---|---|---|---|
| Tsingtao beer can | Normal | Normal (✅ TN) | "Consistent with reference design and appearance" |
| Mengniu strawberry milk carton | Normal | Anomaly (❌ FP) | "Different product type and packaging [vs reference beer can]" |
| Cigarette box (red/Chinese text) | **Anomaly** | Anomaly (✅ TP) | "Different design, red background, differing from Great Wall pack" |

**The Problem**: V0 correctly detects that "carton != can", but this is the same reasoning that correctly detects "red box != gold box". **Model cannot distinguish between acceptable product variance and true defects.**

**Why V3 doesn't help**:
- Advocate (V1) identifies "different product type" as anomaly
- Skeptic argues "different product could be normal variant"
- But skeptic **has no basis** to decide — references are insufficient

**Data Quality Issue**:
- **Reference set too narrow**: All normal references are the same category (e.g., all cans or all cans)
- **Test set mixes product types**: Some "normal" are different from "reference normal" but same product
- **Recommendation**: Either expand reference diversity OR clarify if anomaly = "defect within category"

---

#### **D5 Medical (CheXpert)** — AUROC: 0.436 (V0), 0.487 (V3)

**The Core Problem:**
- **Medical images have natural variation**: No "perfect normal" X-ray
- **Model mistakes normal variation for pathology**: Shadows, patient positioning, rotation angles

**Evidence:**

| Sample Type | GT | Pred (V0) | Model Reasoning |
|---|---|---|---|
| Normal chest X-ray (PA view, clear lungs) | Normal | Anomaly (❌ FP) | "Increased opacity in lower lung fields, likely consolidation/fluid" |
| Normal chest X-ray (with medical lines) | Normal | Anomaly (❌ FP) | "Additional medical lines/tubes not in reference" |
| Actual abnormal X-ray (pneumonia) | Anomaly | Anomaly (✅ TP) | "Opacification in lower lung fields, possible consolidation" |

**Why this is hard:**
1. Normal CheXpert images contain clinical variation (positioning, equipment, patient differences)
2. Model interprets differences as pathology
3. **Only 7/60 normal samples correctly classified (TN)**
4. Requires domain expertise to distinguish "normal variation" from "clinically significant change"

**Data Quality Issue:**
- **References vs queries are too different**: If references are all frontal (PA) and queries are lateral, model fails
- **No context about what constitutes "abnormal"**: Is mild infiltrate abnormal? Where's the threshold?
- **Recommendation**: Add radiologist labels/explanations; clarify binary definition of "abnormal"

---

#### **D6 Remote Sensing (LEVIR-CD+)** — AUROC: 0.764 (V0), 0.622 (V3)

**The Core Problem:**
- **Ambiguous change detection**: What counts as "change"?
  - Natural growth: Tree growth, seasonal changes (normal?)
  - Urban development: New building, road construction (anomaly?)
  - Disaster: Destruction, collapse (anomaly?)

**Evidence:**
- V0: TP=49 (detected all "changes"), FP=48 (flagged many as anomalies)
- Only 1 true negative → Model almost never says "no change"
- All normal samples treated as having some change

**Why this fails:**
- The dataset conflates "change detection" with "anomaly detection"
- Building new construction = change ≠ anomaly from security perspective
- Needs clear domain definition: "anomaly = unauthorized/disaster change" vs "anomaly = any change"

**V3 helps more (Spe 55% vs 2%)**, suggesting debate structure is useful here to filter out benign changes.

---

#### **D8 Surveillance (Avenue)** — AUROC: 0.430 (V0), 0.483 (V3)

**Similar to D6**: Ambiguity about what behavior is "anomalous"
- Normal activity: Pedestrian walking, standing
- Anomaly: Unusual trajectory, crowd, abandoned object

**Model issues:**
- Only 2/60 normal samples correctly classified
- High false positive rate suggests model sees many behaviors as "unusual"
- Requires context and temporal understanding (single frames insufficient)

**Data Quality Issue**: Surveillance is **inherently ambiguous** without temporal context. Single frame cannot determine if pedestrian behavior is "anomalous".

---

### ⚠️ INTERMEDIATE DOMAINS

#### **D4 Maintenance (SDNET2018)** — AUROC: 0.722 (V0), 0.755 (V3)

- More balanced than others
- V3 improves significantly (BA: 56.7% → 72.5%)
- Crack detection benefits from debate: distinguishes structural cracks from surface marks

---

## 4. Model Behavior Analysis: V0 vs V3

### V0's Behavior: High Sensitivity, Low Specificity
- **Bias**: Predicts "anomaly" unless image exactly matches reference
- **Reason**: Prompt likely emphasizes "identify any difference"
- **Failure mode**: Treats normal variance as anomaly
- **Works on**: Domains with clear, single-category references (D1)
- **Fails on**: Domains with natural variation or product diversity (D2, D5, D6, D8)

### V3's Behavior: Debate Improves Specificity
- **Advocate (V1)**: Identifies all differences (similar to V0)
- **Skeptic**: Filters unlikely/benign differences
- **Effect**: Significantly improves specificity (+20-40% typically)
- **Cost**: Sometimes overcorrects, reducing sensitivity
- **Best for**: Domains where V0 false positives are benign (D1, D7, D4)
- **Worst for**: Domains where true anomalies are subtle (D5, D8)

---

## 5. Why V3 Doesn't Uniformly Win

### Domains where V3 helps most:
- **D1, D4**: False positives are spurious texture variations; skeptic correctly filters them
- **D7**: Debate reduces over-sensitivity to background objects; improves specificity dramatically

### Domains where V3 hurts:
- **D2**: Advocate is right that "product differs from reference," but skeptic has no basis to override → becomes random
- **D5**: True anomalies are subtle (mild opacities); debate filter misses them
- **D8**: Temporal context needed; static debate cannot help

---

## 6. Recommendations for Benchmark Improvement

### **Critical (must fix before paper)**

1. **D2 Retail**:
   - Clarify task: Is anomaly = "product defect" or "any product mismatch"?
   - If defect: Expand normal references to include product variants
   - If mismatch: Rename task and compare to exact-match baseline

2. **D5 Medical**:
   - Add radiologist input: Which variations are pathological?
   - Provide structured anomaly definitions (e.g., "consolidation > 5mm", "pleural effusion")
   - Or use dataset with clearer pathology labels (CheXpert already has disease labels — use them!)

3. **D6 Remote Sensing**:
   - Define scope: Disaster detection vs change detection?
   - Add temporal context if available (multi-year comparison)
   - Or filter changes to known disaster categories

### **Important (helpful for analysis)**

4. **D8 Surveillance**:
   - Add temporal sequences (5+ frames) instead of single frames
   - Define anomaly: Unusual motion? Crowd? Abandoned object?

5. **Data splits**:
   - Ensure test set doesn't have distribution shift vs calibration/dev
   - For D1: Check if calibration/dev categories are well-represented in test

### **For Model Improvement**

6. **Domain-adaptive prompting**:
   - D2: Add prompt like "Ignore product type; focus on physical damage only"
   - D5: "You are a radiologist. Distinguish clinically significant findings from normal variation"
   - D6/D8: "Focus on sudden/large changes, ignore gradual growth/shadow"

7. **V3 refinement**:
   - Current skeptic reasoning is surface-level; needs domain knowledge
   - Alternative: Instead of generic skeptic, use domain-specific validator
     - D1: "Check if differences are within manufacturing tolerance"
     - D5: "Is this a known normal finding?"

---

## 7. Per-Domain Summary Table

| Domain | Status | AUROC (V0) | Specificity Issue | Root Cause | Fix Priority |
|--------|--------|-----------|---|---|---|
| D1 | ✅ Good | 0.871 | No (48%) | None | N/A |
| D2 | ❌ Bad | 0.479 | Critical (2%) | Task definition ambiguity | HIGH |
| D4 | ⚠️ OK | 0.722 | Moderate (17%) | Crack texture vs real cracks | MEDIUM |
| D5 | ❌ Bad | 0.436 | Critical (12%) | Domain complexity (medical expertise) | HIGH |
| D6 | ⚠️ Marginal | 0.764 | High (2%) | Change vs anomaly conflation | HIGH |
| D7 | ✅ Good | 0.912 | Moderate (17%) | None (but V3 regresses) | N/A |
| D8 | ❌ Bad | 0.430 | Critical (3%) | Temporal context missing | HIGH |

---

## 8. Conclusion

**The benchmark is partially broken:**
- **2/7 domains work well** (D1, D7) → suitable for publication
- **3/7 domains have fundamental issues** (D2, D5, D8) → need clarification/relabeling
- **2/7 domains are borderline** (D4, D6) → usable but need caveats

**The model improvements (V3) are real but limited:**
- Debate structure significantly improves specificity
- But **does not solve domain ambiguity** (D2, D5)
- Works best on domains with clear definitions (D1, D4, D7)

**Next steps:**
1. Fix D2/D5/D8 task definitions
2. Either retrain models on corrected tasks or adjust evaluation scope (test on "good" domains only)
3. Consider publishing as "3-domain benchmark" (D1, D4, D7) + case study on why other domains fail
