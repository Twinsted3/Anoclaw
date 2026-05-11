# AnomalyClaw

A training-free visual anomaly detection (VAD) agent that judges through
**multi-turn refutation** against normal references. AnomalyClaw runs an
inner refutation trajectory over a 13-tool catalog (visual inspection,
reference understanding, frozen expert probes) and blends its score with a
parallel direct VLM judgment on the same backbone — no fine-tuning, no
per-domain training, no offline fusion weights.

This repository accompanies the paper *"AnomalyClaw: Multi-Turn Refutation
for Training-Free Cross-Domain Visual Anomaly Detection"* (under review).
It contains:

- **Agent code** (canonical `v12` family) under `benchmark/scripts/`.
- **CrossDomainVAD-12 manifests** — 12 cross-domain VAD splits (1,958 items
  total; 1,418 test) under `benchmark/manifests_v2/`.
- **Pre-computed baseline & main-table result JSONs** under
  `benchmark/results/` for headline-number reproducibility.
- **Paper sources** (`paper/`) and figure-generation scripts.

## Headline results (paper §4)

CrossDomainVAD-12 macro-AUROC, AnomalyClaw vs single-pass Direct
(same backbone, both training-free):

| Backbone | Direct | AnomalyClaw | Δ |
|:--|:--:|:--:|:--:|
| GPT-5.5 | — | — | **+6.23 pp** |
| Seed2.0-Lite | — | — | **+7.93 pp** |
| Qwen3.5-VL-27B | — | — | **+3.52 pp** |

All $P(\Delta>0)=1.000$ under a paired-bootstrap test. An optional
**verbalized self-evolution** extension (rulebook generated online with
zero oracle labels) adds another **+2.08 pp** on Qwen3.5-VL-27B.

## Installation

```bash
git clone https://github.com/<org>/AnomalyClaw.git
cd AnomalyClaw
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # see below for the canonical set
```

Required runtime: Python 3.10+, an OpenAI-compatible VLM endpoint
(local vLLM or hosted API). The agent itself has no neural training step.

## Quickstart

Most users will reproduce results in three steps.

### 1. Get the data

The repo already ships everything *derived* — split manifests, DINOv2
retrieval indices, expert score caches, and the v12 main-table run outputs.
You only need to fetch the **raw images** yourself, since most upstream
datasets (MVTec family in particular) prohibit redistribution.

```bash
export ANOMALYCLAW_DATA=$PWD/benchmark/data    # default; override if needed
mkdir -p "$ANOMALYCLAW_DATA"
```

Then follow the per-dataset download table in `DATA.md` to populate
`$ANOMALYCLAW_DATA` into the documented layout. Manifest paths use a
portable `{DATA_ROOT}/...` placeholder that the loader resolves to
`$ANOMALYCLAW_DATA` at runtime — no manual rewriting needed.

### 2. Bring up a VLM backend

```bash
# Local Qwen3.5-VL-27B with 4-replica vLLM load balancer (the paper setup):
bash benchmark/scripts/launch_qwen35_replicas.sh
# Or point at any OpenAI-compatible endpoint:
export QWEN_API_BASE=http://localhost:8210/v1
export QWEN_MODEL=Qwen3.5-VL-27B
export QWEN_API_KEY=EMPTY
```

For GPT or SeedVL backends, set `GPT_API_KEY`/`GPT_API_BASE` or
`SEED_API_KEY`/`SEED_API_BASE` respectively. No keys are baked into the
code.

### 3. Run the agent

The canonical entry-point is `agent_v12.py`. Each call evaluates one domain
manifest. The reference run from the paper:

```bash
bash benchmark/scripts/run_v12_eval_test.sh
```

This iterates the 12 test manifests under `benchmark/manifests_v2/` and
writes one result JSON per domain into
`benchmark/results/verbalized/v12_eval_test/D*.json`. Aggregate macro
AUROC and the paired-bootstrap CI with:

```bash
python benchmark/scripts/evaluate.py \
       --pred benchmark/results/verbalized/v12_eval_test \
       --report-bootstrap
```

## Repository map

```
benchmark/
├── BENCHMARK_SPEC.json          # CrossDomainVAD-12 spec (12 domains, splits)
├── manifests_v2/                # canonical manifests (paper §3.1)
├── results/                     # paper-table JSONs (v12 + baselines)
└── scripts/
    ├── AGENTS.md                # v12 architecture & data flow
    ├── agent_v12.py             # canonical AD agent
    ├── agent_v12_mmad.py        # MMAD-MCQA variant
    ├── agent_v12_mmad_mcq.py    # MMAD-MCQA + single-letter coercion
    ├── agent_v12_logitdirect.py # logit-Direct deployment variant
    ├── agent_v9.py, agent_v11.py  # refutation/controller pieces v12 inherits
    ├── agent_prompt_*.py        # turn-1/refutation/mode prompts
    ├── agent_tools_v8.py        # 13-tool catalog (heatmap, retrieval, …)
    ├── infer.py                 # backend clients + image utils
    ├── baseline_*.py            # AnomalyDINO / VisualAD / AD-Copilot / IAD-R1
    ├── classical_baselines.py   # DINOv2 patch & global k-NN
    ├── expert_*.py              # SubspaceAD / AnomalyVFM wrappers
    ├── evaluate.py              # macro AUROC + paired-bootstrap CI
    ├── mmad_eval_v12_mmad*.py   # MMAD-MCQA evaluators
    └── run_*.sh, launch_*.sh    # repro shells (REPO_ROOT auto-resolved)
experts/                         # wrappers; user clones upstreams; see README
paper/                           # NeurIPS source + figures
```

## Citation

If you use AnomalyClaw or the CrossDomainVAD-12 benchmark in academic work,
please cite the paper (BibTeX in `CITATION.cff`).

## License

CC BY-NC 4.0 — non-commercial use only. See `LICENSE`. Third-party datasets
and expert baselines retain their original licenses.
