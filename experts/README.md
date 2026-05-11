# Expert baselines

AnomalyClaw's tool family includes calls into several published expert anomaly
detectors. The wrappers under `benchmark/scripts/expert_*.py` load expert
scores from JSON caches that are produced by running each upstream baseline on
the CrossDomainVAD-11 manifest.

The expert source code is **not** vendored in this repository because each
upstream project carries its own license. Reproducing the paper requires you
to fetch the original repos and run them once to produce the cache files. The
score caches themselves are released on Hugging Face (see `DATA.md`).

## Required directory layout

```
experts/
├── README.md            # this file
├── AnomalyDINO/         # clone https://github.com/dammsi/AnomalyDINO
├── AnomalyVFM/          # clone the AnomalyVFM release (see paper §4.3)
├── IAD-R1/              # clone https://github.com/Klin0kong/IAD-R1
├── SubspaceAD/          # clone the SubspaceAD release (see paper §4.3)
└── VisualAD/            # clone the VisualAD release (see paper §4.3)
```

The exact upstream URLs are listed in the paper's references section. After
cloning, follow each upstream's setup instructions to download weights into
the expected `checkpoints/` subdirectory.

## Quick path: download cached expert scores

If you only want to reproduce the AnomalyClaw agent's final results without
re-running every expert, download the pre-computed JSON caches from the
Hugging Face dataset companion (see `DATA.md`) and drop them into
`benchmark/results/`. The wrappers `expert_subspacead.py` and
`expert_anomalyvfm.py` only need those caches at agent inference time.
