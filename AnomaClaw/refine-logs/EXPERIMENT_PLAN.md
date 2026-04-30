# Experiment Plan

**Paper**: Beyond Industrial: A Cross-Domain Benchmark and Minimal Agent Design Study for Training-Free MLLM Anomaly Detection

**Method Thesis**: A minimal reference-based agent that first states what normal looks like and then performs at most one bounded adversarial check is the smallest training-free MLLM design worth testing for cross-domain anomaly detection.

**Date**: 2026-03-31

## Claim Map

| Claim | Why It Matters | Minimum Convincing Evidence |
|---|---|---|
| C1. Industrial-only evaluation is misleading. | This is the paper's problem anchor. | Cross-domain rankings differ from industrial-only rankings, or some industrial winners fail badly outside industrial data. |
| C2. `Normal-First` is a real transfer prior. | This is the main mechanism claim. | `Normal-First` beats `Direct` on overall balanced accuracy and AUROC, with gains on at least 5 of 8 domains. |
| C3. One bounded refutation round is the maximum useful agent complexity under budget. | This is the agent-design claim. | `Bounded Debate` beats `Normal-First` on at least 3 domains or on the overall score per dollar, while `Two-Round Debate` shows weak or no additional gain. |
| C4. GPT and Seed fail differently. | This makes the backbone analysis worth publishing. | Error taxonomy and per-domain results show complementary strengths with consistent qualitative patterns. |
| Anti-claim A1. Any gain comes only from more calls. | Must be ruled out. | `Self-Refine` under the same call budget does not fully match `Bounded Debate`. |
| Anti-claim A2. Results are prompt noise. | Must be ruled out. | Main ranking remains stable under prompt paraphrase on a held-out sensitivity slice. |

## Scope Decisions Frozen

- Main paper is image-only.
- Surveillance is frame-based, not temporal-video reasoning.
- Main task is binary anomaly decision with optional coarse anomaly type.
- Localization is appendix-only.
- No active learning, memory, routing, retrieval, or fine-tuning.

## Benchmark Definition

Each item contains:

- query image
- up to two normal reference images
- binary anomaly label
- coarse anomaly type for anomalous items
- optional region annotation if available from the source dataset

The benchmark release should include:

- exact sampled filenames or frame indices
- reference-image mapping
- domain tag
- calibration, dev, and test split IDs
- anomaly taxonomy mapping

## Dataset Selection Per Domain

### D1. Industrial Manufacturing

- **Primary dataset**: `MVTec AD`
- **Secondary comparison dataset**: `VisA`
- **Main benchmark sample**: `180` items from `MVTec AD`
- **Composition**: `90 normal`, `90 anomalous`
- **Stratification**: balance object and texture categories; cap at `12` items per category
- **Reference images**: `2` normal train images from the same category
- **Why selected**: standard public industrial AD benchmark with masks; enables comparison with training-free classical baselines and existing industrial literature

### D2. Retail Shelf Monitoring

- **Primary dataset**: `gapDetectionDatasets` over `Grocery Products`, `WebMarket`, and `Grozi-120`
- **Main benchmark sample**: `180` shelf images
- **Composition**: `90 images with shelf-gap anomaly`, `90 images without annotated gap`
- **Stratification**: balance across the three source datasets
- **Reference images**: `1-2` normal shelf images from the same source dataset and similar shelf layout
- **Why selected**: public retail shelf anomaly annotations; close to real inventory or planogram failure

### D3. Parcel or Baggage Screening

- **Primary dataset**: `PIDray`
- **Main benchmark sample**: `180` X-ray images
- **Composition**: `90 clean baggage`, `90 prohibited-item images`
- **Stratification**: balance across easy, hard, and hidden subsets when available
- **Reference images**: `2` clean baggage images from the same acquisition subset
- **Why selected**: public real-world screening benchmark with strong occlusion and clutter

### D4. Maintenance or Infrastructure Inspection

- **Primary dataset**: `SDNET2018`
- **Main benchmark sample**: `180` image patches
- **Composition**: `90 non-cracked`, `90 cracked`
- **Stratification**: balance bridge deck, wall, and pavement subsets
- **Reference images**: `2` non-cracked images from the same structure type
- **Why selected**: public inspection dataset with realistic nuisance factors such as shadows, stains, and debris

### D5. Medical Radiology

- **Primary dataset**: `NIH ChestXray14`
- **Main benchmark sample**: `180` frontal chest X-rays
- **Composition**: `90 No Finding`, `90 abnormal`
- **Abnormal subset rule**: use only single-label abnormal cases from `{pneumothorax, mass, effusion, consolidation}` to reduce label noise
- **Reference images**: `2` `No Finding` images matched by view position and sex when metadata is available
- **Why selected**: public and large enough for clean sampling; supports a medically distinct visual domain without fine-tuning

### D6. Remote Sensing Disaster Damage

- **Primary dataset**: `xBD`
- **Main benchmark sample**: `180` post-disaster tiles
- **Composition**: `90 no-damage`, `90 damaged`
- **Damage rule**: collapse `{minor, major, destroyed}` into anomalous for the main binary task
- **Reference images**: the corresponding pre-disaster tile plus one no-damage post-disaster tile from the same event if available
- **Why selected**: public remote sensing anomaly setting with natural paired references

### D7. Road or Traffic Scene Anomaly

- **Primary positive dataset**: `RoadAnomaly21`
- **Primary negative dataset**: `Cityscapes val` or `BDD100K val` normal frames
- **Main benchmark sample**: `180` road-scene images
- **Composition**: `90 anomalous`, `90 normal`
- **Positive stratification**: balance small-object, medium-object, and large-object anomalies when possible
- **Reference images**: `2` normal urban road scenes matched by daylight and scene type
- **Why selected**: public unexpected-obstacle anomaly setting; natural test for context-sensitive visual anomalies

### D8. Surveillance Frame Anomaly

- **Primary dataset**: `Avenue`
- **Secondary robustness dataset**: `UCSD Ped2` for appendix
- **Main benchmark sample**: `180` frames from `Avenue`
- **Composition**: `90 normal`, `90 anomalous`
- **Sampling rule**: one frame every `>= 15` frames; at most `2` anomalous frames per anomaly episode
- **Reference images**: `2` normal training frames from the same camera scene
- **Why selected**: public frame-level abnormal surveillance benchmark with spatial annotations

## Split Structure

Each domain contributes:

- `20` calibration items: `10 normal`, `10 anomaly`
- `40` dev items: `20 normal`, `20 anomaly`
- `120` test items: `60 normal`, `60 anomaly`

Total benchmark size: `1,440` items.

## Sampling Protocol

### Global Rules

- Sample only from official public test or validation splits unless the source dataset lacks them.
- Keep train-only normal images only for reference selection, never as query test items.
- Never place near-duplicate images, frames from the same short clip segment, or patient duplicates across calibration, dev, and test.
- Release the exact sampled IDs and the exact reference mapping.
- Freeze the sampled benchmark once created; do not resample after seeing results.

### Domain-Specific Leakage Controls

- `MVTec AD`: no duplicate textures or nearly identical neighboring captures across splits.
- `gapDetectionDatasets`: split by original shelf image, not by crop.
- `PIDray`: split by original image ID; no object-crop leakage.
- `SDNET2018`: split by source structure subset and original image group if recoverable.
- `ChestXray14`: patient-level split only.
- `xBD`: event-level split; do not place tiles from the same disaster event across dev and test.
- `RoadAnomaly21`: keep negatives from scene IDs not reused in the positive-matching pool.
- `Avenue`: split by video clip and anomaly episode, not by frame.

### Reference Selection Rules

- Use at most `2` reference images per query.
- References must be normal.
- References must be selected from the same domain and closest available subcategory or scene.
- Use deterministic reference selection: nearest metadata match first, then fixed random seed within the candidate pool.

## Shared Anomaly Taxonomy

Use the following coarse types for anomalous items:

1. `surface_defect`
2. `breakage_or_deformation`
3. `missing_or_extra_object`
4. `contamination_or_artifact`
5. `damage_or_change`
6. `hazard_or_prohibited_object`
7. `pathology_or_lesion`
8. `contextual_abnormality`
9. `other`

This taxonomy is for benchmark standardization and error analysis. It is not a claimed standalone contribution.

## Backbones

### Proprietary Backbones

- `GPT-4o` or `GPT-4.1` vision endpoint
- `Seed1.5-VL` via Volcano or Ark API

### Open Reproducibility Baseline

- `Qwen2.5-VL-7B-Instruct`

Reason for choosing `Qwen2.5-VL-7B-Instruct`:

- open weights
- Apache-2.0 license
- strong multimodal reasoning baseline
- tractable local inference on a single 24 GB GPU with 4-bit quantization
- active community use and stable model card

## Baseline List

### Classical Baselines

Run across all domains where possible:

1. `DINOv2-GlobalNN`
   - image embedding of query vs normal reference pool
   - anomaly score = `1 - max cosine similarity`

2. `DINOv2-PatchNN`
   - patch-level nearest-neighbor distance against normal reference images
   - anomaly score = max or top-k patch distance

3. `CLIP-ZeroShot-Abnormality`
   - prompt pairs such as `normal / abnormal / defective / damaged / suspicious`
   - optional reference-image similarity added as a score feature

Industrial-only comparison where implementation time permits:

4. `WinCLIP`

5. `UniVAD` or nearest available official implementation

### MLLM Non-Agent Baselines

1. `Direct Single-Pass`
2. `Normal-First Single-Pass`
3. `Self-Refine Two-Pass`

### Agent Variants

1. `Debate-1R`
   - proposer + refuter

2. `Debate-2R`
   - second proposer-refuter round only for uncertain outputs

### Backbone Settings

- Apply the same prompt family to `GPT-4o/4.1`, `Seed1.5-VL`, and `Qwen2.5-VL-7B-Instruct`.
- Use deterministic decoding if supported: `temperature = 0`.
- Resize long side to `512` by default for fairness and cost control.
- Use at most `2` reference images.
- Cap output length to `700` tokens.

## Prompt Variants to Freeze

### P0. Direct

```text
You are a visual anomaly inspector.
Given one query image and up to two normal reference images, decide whether the query is abnormal relative to the normal references.
Return JSON only with image_label, anomaly_type, evidence, confidence, and optional bbox.
```

### P1. Normal-First

```text
You are a visual anomaly inspector.
First summarize what normal looks like in these references and in this domain.
Then state whether the query departs from that normal state.
Return JSON only with normal_profile, claims, and image_label.
```

### P2. Self-Refine

```text
Here is your previous JSON.
Revise it once for consistency and possible non-anomalous explanations.
Do not add new evidence that is not visible.
Return JSON only.
```

### P3. Refuter

```text
You are an anomaly refuter.
For each proposed anomaly claim, try to explain it as normal variation, lighting, viewpoint, occlusion, expected context, or imaging artifact.
Return JSON only with refute_confidence, counter_evidence, and likely_cause.
```

## Metrics

### Primary Metrics

- `Balanced Accuracy`
- `AUROC` using the model anomaly score
- `Macro-F1` on binary anomaly decision

### Secondary Metrics

- `Anomaly-Type Macro-F1` on anomalous items only
- `Cost per 100 images`
- `Latency per image`

### Appendix Metrics

- `Localization Hit@1`: predicted bbox center falls inside GT mask or box
- `Brier score` for calibration if confidence values are stable enough

### Domain Reporting

Report all primary metrics:

- per domain
- overall macro average across domains
- overall micro average across all items

Do not let large domains dominate the headline result.

## Cost Budget Breakdown

Total proprietary API budget cap: `$280`

### Stage S0. Benchmark Construction and Local Classical Baselines

- Cost type: local CPU/GPU only
- API budget: `$0`
- Outputs: sampled benchmark JSON, reference map, DINOv2 and CLIP baseline scores

### Stage S1. Calibration Slice Sweep

- Data: `20` items per domain = `160` total
- Models: `GPT-4o/4.1`, `Seed1.5-VL`
- Variants: `Direct`, `Normal-First`, `Self-Refine`, `Debate-1R` on all items; `Debate-2R` only on flagged uncertain cases after the first four domains
- Expected proprietary calls: about `2,160`
- Budget cap: `$55`
- Purpose: choose the main agent variants and freeze thresholds

### Stage S2. Development Runs

- Data: `40` items per domain = `320` total
- Models: `GPT-4o/4.1`, `Seed1.5-VL`
- Variants: keep top `3` from Stage S1, expected to be `Direct`, `Normal-First`, `Debate-1R`
- Expected proprietary calls: about `2,560`
- Budget cap: `$55`
- Purpose: freeze final prompt wording and aggregator thresholds

### Stage S3. Full Test Runs

- Data: `120` items per domain = `960` total
- Models: `GPT-4o/4.1`, `Seed1.5-VL`
- Variants: `Direct`, `Normal-First`, `Debate-1R`
- Expected proprietary calls: about `7,680`
- Budget cap: `$160`
- Purpose: main paper tables

### Stage S4. Prompt Sensitivity Slice

- Data: `5` items per domain = `40` total
- Models: proprietary backbones only
- Variants: `Normal-First`, `Debate-1R`
- Runs: one prompt paraphrase
- Expected proprietary calls: about `240`
- Budget cap: `$10`

### Total

- Expected proprietary call count: about `12,640`
- Expected proprietary API spend: about `$280`

### Budget-Cut Option To Stay Near `$250`

If Stage S1 or S2 already shows `Debate-2R` is not useful, cut it immediately.

Budget-capped target:

- Stage S1 without `Debate-2R` after first `4` domains if clearly weak
- Stage S2 run only `Direct`, `Normal-First`, `Debate-1R`
- Stage S4 skipped if the ranking margin is already large on the dev split

Target capped spend after these cuts: `$240-$260`

## Run Order

### M0. Data and Metric Sanity

- Build the benchmark manifest for all `1,440` items
- Verify reference mapping
- Verify binary labels and taxonomy labels
- Implement metrics and JSON parsers
- Run `DINOv2-GlobalNN` on `40` random items
- Decision gate: if parser or reference selection is unstable, do not launch API runs

### M1. Cheapest Early Signal

- Run `GPT-4o/4.1` and `Seed1.5-VL` on the `160`-item calibration slice
- Compare `Direct` vs `Normal-First`
- Decision gate: if `Normal-First` is not better than `Direct` overall or on at least `4` domains, rewrite the paper thesis before scaling

### M2. Extra-Call Control

- On the same `160` calibration items, run `Self-Refine` and `Debate-1R`
- Decision gate: if `Self-Refine` matches `Debate-1R`, do not sell debate as a major result

### M3. Diminishing Returns Check

- Run `Debate-2R` only on calibration items where `Debate-1R` is uncertain or wrong
- Decision gate: if gains are marginal, cut `Debate-2R` from the main paper

### M4. Full Development Freeze

- Run selected main variants on the `320` dev items
- Freeze thresholds, prompt wording, and any bbox postprocessing
- Decision gate: no method changes after this point

### M5. Full Test

- Run selected main variants on the `960` test items
- Run `Qwen2.5-VL-7B-Instruct` on `Direct`, `Normal-First`, and `Debate-1R`
- Aggregate overall and per-domain tables

### M6. External Comparability

- Run the chosen industrial variants on:
  - a sampled `MMAD` subset using the existing codebase
  - `VisA` industrial subset if time permits
- Purpose: link the new benchmark to existing industrial MLLM evaluation

## Statistical Protocol

### Fixed-Split Evaluation

- Tune thresholds only on the calibration split.
- Use the dev split only to freeze the final variant list and prompt wording.
- Report the test split once, after everything is frozen.

### Confidence Intervals

- Use `1,000` bootstrap resamples for domain-level and overall balanced accuracy and AUROC.
- Report `95%` confidence intervals.

### Paired Significance Tests

- Use `McNemar` for paired binary decision comparisons on the test split.
- Main pairwise tests:
  - `Direct` vs `Normal-First`
  - `Normal-First` vs `Debate-1R`
  - `Self-Refine` vs `Debate-1R` on the calibration slice and dev split
- Apply Benjamini-Hochberg correction over the main comparison family.

### Prompt Sensitivity

- Use one prompt paraphrase on the held-out sensitivity slice.
- Report whether the ranking of `Direct`, `Normal-First`, and `Debate-1R` changes.

### Error Analysis Protocol

Manually inspect at least `20` failures per backbone from the test split and tag them as:

1. hallucinated anomaly
2. missed subtle anomaly
3. wrong normal prior
4. reference mismatch
5. contextual misunderstanding
6. localization failure
7. domain-specific vocabulary failure

## Table and Figure Targets

### Main Paper Tables

1. `Table 1`: benchmark composition by domain, source dataset, and sample counts
2. `Table 2`: overall and per-domain results for `Direct`, `Normal-First`, and `Debate-1R`
3. `Table 3`: cost, latency, and gain-per-dollar for the same variants
4. `Table 4`: GPT vs Seed vs Qwen backbone comparison

### Main Paper Figures

1. `Figure 1`: benchmark construction and reference-based task definition
2. `Figure 2`: minimal agent schematic
3. `Figure 3`: domain-wise delta of `Normal-First - Direct`
4. `Figure 4`: domain-wise delta of `Debate-1R - Normal-First`
5. `Figure 5`: error taxonomy heatmap by backbone and domain

### Appendix

- `Debate-2R` ablation
- localization results
- MMAD subset comparison
- `VisA` industrial comparison
- prompt sensitivity details

## Success Criteria

The paper is submission-ready if the test split supports at least:

- `Normal-First > Direct` overall and on `>= 5/8` domains
- `Debate-1R > Normal-First` either overall or with clear gains on at least `3` high-value domains under matched cost
- `Debate-2R` adds little, which defends simplicity
- GPT and Seed show non-trivial complementary failure patterns

If these are not met, reframe:

- benchmark paper with negative findings on agentic complexity
- not a method paper

## Risks and Mitigations

- **Risk**: benchmark too small for strong claims
  - **Mitigation**: fixed release, bootstrap CIs, per-domain significance, exact sampling protocol

- **Risk**: debate gains vanish after cost matching
  - **Mitigation**: make the paper's center `benchmark + minimal design principles`, not debate alone

- **Risk**: retail or road domain feels weakly defined
  - **Mitigation**: publish the exact anomaly definition and reference mapping, and keep taxonomy coarse

- **Risk**: proprietary backbones harm reproducibility
  - **Mitigation**: include `Qwen2.5-VL-7B-Instruct` and release prompts, parsing code, and benchmark JSON

- **Risk**: medical labels are noisy
  - **Mitigation**: restrict to single-label cases and matched normal references; avoid medical overclaiming

## First Three Runs To Launch

1. Build the `1,440`-item benchmark manifest and reference map, then run `DINOv2-GlobalNN` sanity checks.
2. Run `Direct` and `Normal-First` on the `160`-item calibration slice with `GPT-4o/4.1` and `Seed1.5-VL`.
3. Run `Self-Refine` and `Debate-1R` on the same `160` items to isolate "extra call" vs "adversarial check".

## Final Checklist

- [ ] Benchmark task is frozen and reference-based
- [ ] Domain sampling protocol is explicit and releasable
- [ ] Classical baselines are implemented before API sweeps
- [ ] `Normal-First` is tested before full debate sweeps
- [ ] Extra-call confound is controlled by `Self-Refine`
- [ ] Cost per variant is tracked from the first run
- [ ] Test split is evaluated only after thresholds and prompts are frozen
