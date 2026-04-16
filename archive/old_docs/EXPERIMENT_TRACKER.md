# Experiment Tracker

| Run ID | Milestone | Purpose | System / Variant | Split | Metrics | Priority | Status | Notes |
|--------|-----------|---------|------------------|-------|---------|----------|--------|-------|
| R001 | M0 | sanity: smoke-test generic prompt on 20 items | Qwen3.5-27B-FP8 + `build_prompt_v0_generic()` | test first 20 | parse rate, sample AUROC | MUST | TODO | `localhost:8200/v1` |
| R002 | M0 | sanity: smoke-test generic prompt on 20 items | SeedVL doubao-seed-2-0-lite + `build_prompt_v0_generic()` | test first 20 | parse rate, sample AUROC | MUST | TODO | `localhost:8080/v1` |
| R003 | M1 | full Qwen3.5 generic-descriptor test sweep | Qwen3.5-27B-FP8 + generic | test n=1298 | macro AUROC + per-domain | MUST | TODO | ~1 h; reuse existing manifest |
| R004 | M2 | full SeedVL generic-descriptor test sweep | doubao-seed-2-0-lite + generic | test n=1298 | macro AUROC + per-domain | MUST | TODO | ~1 h; watch rate limits |
| R005 | M3 | paired bootstrap + per-domain table | 3 backbones × 2 descriptors | test n=1298 | Δ, 95% CI, paired bootstrap | MUST | TODO | reuse `paper/figures/gen_bootstrap_cis.py` |
| R006 | M4 | paper update (abstract, Fig 1, Appendix C) | n/a (writing) | n/a | n/a | MUST | TODO | code checkpoint: update `gen_intuition.py` to 3-backbone panel (a) |
| R007 | B4 | calibration cross-check (nice-to-have) | existing caches | calibration n=220 | macro AUROC | NICE | TODO | only if test results borderline |

## Expected outputs
- `benchmark/results/qwen35_v0_direct_generic_test.json` + `_metrics.json`
- `benchmark/results/seedvl_v0_direct_generic_test.json` + `_metrics.json`
- `paper/figures/bootstrap_cis_descriptor.json` (new — 6 comparisons: 3 backbones × generic-vs-task, plus 3 cross-checks)
- Updated `paper/sections/0_abstract.tex` (rephrased descriptor claim)
- Updated `paper/sections/4_experiments.tex` (Finding 1 + figure references)
- Updated `paper/sections/A_appendix.tex` (expanded `tab:descriptor_ablation` with SeedVL + Qwen3.5 sections)
- Regenerated `paper/figures/fig_intuition.pdf` (Panel (a) becomes 3-backbone grouped bars)

## Code to write (once)

1. `build_prompt_v0_generic(domain_code: str, has_refs: bool) -> str` in `benchmark/scripts/infer.py`:
   ```python
   def build_prompt_v0_generic(domain_code: str, has_refs: bool) -> str:
       """Domain-agnostic, generic descriptor baseline (no task-specific normal/anomaly definition)."""
       ref_note = " The first image(s) show the normal reference state." if has_refs else ""
       return (
           "You are a visual anomaly inspector.{ref_note}\n"
           "Decide whether the query image is abnormal relative to the reference(s).\n"
           "Return JSON only:\n{OUTPUT_SCHEMA_V0}"
       )
   ```

2. Add `--descriptor {task,generic}` CLI flag to `run_v0()` entry point (or duplicate the relevant script section and call the generic prompt builder).

3. Launcher commands:
   ```bash
   # Qwen3.5 (needs TENSOR_PARALLEL=1 env to hit the 8200 server)
   MODEL_ENDPOINT=http://localhost:8200/v1 MODEL_NAME=/hdd1/models/Qwen3.5-27B-FP8 \
     python -m benchmark.scripts.infer --variant v0_direct --descriptor generic \
       --manifest benchmark/manifests/full_manifest.json --split test \
       --out benchmark/results/qwen35_v0_direct_generic_test.json

   # SeedVL
   MODEL_ENDPOINT=http://localhost:8080/v1 MODEL_NAME=doubao-seed-2-0-lite-260215 \
     API_KEY=$SEEDVL_API_KEY \
     python -m benchmark.scripts.infer --variant v0_direct --descriptor generic \
       --manifest benchmark/manifests/full_manifest.json --split test \
       --out benchmark/results/seedvl_v0_direct_generic_test.json
   ```

## Decision gates

- **Before launching R003**: verify R001 output has ≥18/20 successfully parsed JSON responses with scores in [0,1].
- **Before launching R004**: same as above for R002.
- **After R003 + R004 complete**: if either macro AUROC vs task-anchored is significantly *worse* (wrong direction), hold analysis, re-read prompt wording and responses to see if the generic prompt accidentally steers the model away from the task.
- **After R005**: if all three 95% CIs exclude zero and point in the positive direction, declare C1 supported across 3 backbones and proceed to paper update. Otherwise, re-scope Finding 1 in the paper.
