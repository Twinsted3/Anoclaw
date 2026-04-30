<!-- ARIS:BEGIN -->
## ARIS Skill Scope
For ARIS workflows in this project, use only the project-local ARIS skills under `.claude/skills/aris`.
Do not use global skills or non-ARIS project skills unless the user explicitly asks to mix them.
<!-- ARIS:END -->

## Experiment Integrity Context

Before running `/experiment-plan`, `/experiment-bridge`, `/result-to-claim`, or `/research-refine` on this project, read `docs/EXPERIMENT_LESSONS.md`. It contains AnomalyClaw v6 retrospective rules: 5 pre-flight integrity checks, sanity protocol (degenerate output / D5d-D6 pathology / A6000 throughput), plan requirements (label budget, per-tool causal ablation, test-split discipline), and the fair-comparison method-design principle.
