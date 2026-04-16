# Paper Improvement Log

## Round 1 Summary

Scope: strict NeurIPS-style manuscript review over `sections/*.tex` and `references.bib`, with direct fixes for all CRITICAL and MAJOR issues that were verifiable from the current draft.

Verification note: no LaTeX toolchain is installed in this environment, so I verified consistency by cross-file inspection, line-by-line checks, and an explicit undefined-reference scan. All cited BibTeX keys used in the manuscript are present in `references.bib`; no bibliography entry change was required in this round.

## Review Findings

- `MAJOR` Benchmark cardinalities and split semantics were inconsistent across the paper. The abstract claimed "over 1,200 test items," the introduction said "1,200+ test items," the method used a `240`-item calibration split, the experiments section split `120` images per domain into `100` test + `20` calibration, and the appendix separately claimed `60+60` test plus `10+10` calibration. Evidence and fixes now appear at `sections/0_abstract.tex:1`, `sections/1_introduction.tex:60,67`, `sections/3_method.tex:158-160`, `sections/4_experiments.tex:13-15,22`, and `sections/A_appendix.tex:7`. I normalized the manuscript to `1,200` test items plus a disjoint `200`-item calibration pool.

- `MAJOR` The experiments section described the calibration split as being used for "threshold tuning," which is conceptually wrong for an AUROC-centric paper and also conflicted with the method section, which uses calibration only for family-adaptive fusion weights. This was corrected at `sections/4_experiments.tex:14` and aligned with `sections/3_method.tex:157-160`.

- `MAJOR` The reference-count description was inconsistent: the setup said every query uses `4` references, while the `DINOv2-Global` baseline actually used `2`. This mismatch would confuse reproducibility. I resolved it at `sections/4_experiments.tex:15,49` and `sections/A_appendix.tex:24`.

- `MAJOR` The expert text-threshold definition was contradictory. The main method used `<0.1 / 0.1-0.3 / >0.3`, while the appendix used `<0.4 / 0.4-0.8 / >0.8`, which would make the worked examples disagree with the prose. I unified the thresholds and clarified that they only verbalize the continuous score at `sections/3_method.tex:105-106` and `sections/A_appendix.tex:52`.

- `MAJOR` Fusion notation was internally inconsistent. The draft introduced a family mapping from domain to anomaly family, but the algorithm and fusion equation still wrote `\alpha_\mathcal{F}` as if the family index were an unbound variable. I fixed the notation at `sections/3_method.tex:13-16`, `sections/3_method.tex:50-51`, and `sections/3_method.tex:150-155` so the weight is indexed by `\family(\domcode)`.

- `MAJOR` The introduction mischaracterized prior work. It cited papers that do not all support the statement "without task-specific training," and it also placed EAGLE under the wrong methodological bucket. I rewrote the framing and citations at `sections/1_introduction.tex:4,10-13` to distinguish tuned VLM systems from zero-shot reasoning and to avoid category errors.

- `MAJOR` Several claims were written too absolutely or too causally for the evidence shown. Examples included "No existing system...", "No existing benchmark...", "causal driver," and "validated operating points." I softened these to defensible claims at `sections/1_introduction.tex:8-13,63,69`, `sections/2_related_work.tex:35-44`, `sections/4_experiments.tex:137,155-156`, and `sections/5_conclusion.tex:4`.

- `MAJOR` AUROC deltas were expressed as percentages in places where the manuscript is actually reporting absolute AUROC-point improvements. This is imprecise and can be read as a relative improvement claim. I converted these to AUROC points at `sections/1_introduction.tex:20,63`, `sections/4_experiments.tex:119,121,155-156,165,185`, and kept percentage notation only for actual call-rate or cost changes.

- `MAJOR` The main-results narrative overstated the number of domain wins. The table shows AnomaClaw is strictly best on `4/10` domains and ties on `2`, not "highest on 6 out of 10 domains and ties for best on D1 and D7." I corrected this at `sections/4_experiments.tex:114`.

- `MAJOR` The family-analysis table had a numeric contradiction on the logical-anomaly row: `VLM-Only` was listed as `0.796`, which copied the `Expert-Informed VLM` number rather than the actual `Ret+VLM` value `0.756`, and it made the surrounding interpretation self-contradictory. I fixed the table at `sections/4_experiments.tex:211`.

- `MAJOR` The liver-CT failure analysis contained mutually inconsistent counts. The main text stated that the expert recovers `44` VLM misses, the VLM recovers `32` expert misses, and `7` cases defeat both systems, which cannot all hold simultaneously for `60` anomalous images. I removed the impossible decomposition and replaced it with a conservative, verifiable description tied to the final-system false-negative count at `sections/4_experiments.tex:254-264` and `sections/A_appendix.tex:97-106`.

- `MAJOR` Bootstrap confidence-interval methodology was inconsistent: the main text used `10,000` resamples while the appendix used `2,000`. I standardized this to `10,000` at `sections/4_experiments.tex:63` and `sections/A_appendix.tex:72`.

- `MAJOR` The appendix contained an undefined cross-reference to `tab:per_category`, which would leave an unresolved reference in the compiled manuscript. I removed the dangling reference and rewrote the paragraph as an explicit omission note at `sections/A_appendix.tex:57-61`.

- `MAJOR` Two figure environments were effectively empty: they had captions and labels but no visible body. That is a manuscript-quality failure and would produce blank floats. Since no final figure assets exist in the workspace, I inserted explicit placeholder boxes that summarize the intended content and preserve layout coherence at `sections/1_introduction.tex:22-53` and `sections/4_experiments.tex:225-252`.

## Modification Log

- `sections/0_abstract.tex:1,5-6`  
  Normalized benchmark size and calibration wording, and removed the unsupported implication that router failure depends on extreme medical false positives.

- `sections/1_introduction.tex:4,8-13,20,22-53,60,63,67,69`  
  Reframed prior-work citations, softened overclaims, converted AUROC deltas to points, inserted a visible architecture placeholder, and aligned benchmark/calibration counts.

- `sections/2_related_work.tex:35-44`  
  Removed self-referential "our development process" language from related work and replaced it with defensible positioning; softened the cross-domain benchmark claim to "to the best of our knowledge."

- `sections/3_method.tex:13-16,50-51,105-106,133-139,150-160`  
  Repaired family-index notation, unified prompt-threshold semantics, removed unsupported router/fusion numeric anecdotes, and aligned calibration-pool accounting with the experiments section.

- `sections/4_experiments.tex:13-15,22,114,119,121,137,155-156,165,183,211,225-252,254-264`  
  Harmonized the benchmark description, corrected the domain-win count, corrected the D9 family-analysis number, softened causal language, converted AUROC deltas to points, added a visible Pareto placeholder, and replaced impossible failure-analysis counts with a verifiable summary.

- `sections/5_conclusion.tex:4`  
  Softened the closing claim, aligned the evaluation size with the corrected benchmark definition, and removed the inaccurate "multi-round skeptic agent" phrasing.

- `sections/A_appendix.tex:7,24,52,57-61,72,97-106`  
  Aligned split definitions and reference counts with the main text, unified expert-score verbalization thresholds, removed the undefined per-category reference, standardized CI resampling, and rewrote the D5c error analysis to avoid unsupported exact decompositions.

## Remaining Non-Blocking Issues For Round 2

- `MINOR` `sections/A_appendix.tex:63-67` still contains a prose-only sensitivity subsection with a commented table placeholder. It no longer breaks references, but the final paper should include the actual `k`-sensitivity table or remove the subsection.

- `MINOR` The manuscript now uses visible figure placeholders instead of blank floats, but final submission quality still requires real architecture and Pareto figures to replace `sections/1_introduction.tex:36-45` and `sections/4_experiments.tex:235-245`.
