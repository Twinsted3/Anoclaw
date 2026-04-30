"""Generate fig_per_domain.pdf (v10) — per-domain AUROC for Direct / V9 / Ensemble
across three VLM backbones on CrossDomainVAD-12 test.

Reads `paper/figures/v2_main_results.json` (produced 2026-04-22 from the
v10 runs under `benchmark/results/v2/`).
Writes `paper/figures/fig_per_domain.pdf` (overwrites the v1 version).
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "legend.fontsize": 8,
    "pdf.fonttype": 42,
})

HERE = Path(__file__).parent
DATA = json.load(open(HERE / "v2_main_results.json"))

BACKBONE_ORDER = ["gpt", "seedvl", "qwen3"]
BACKBONE_LABEL = {"gpt": "GPT-5.4", "seedvl": "SeedVL", "qwen3": "Qwen3.5-VL-27B"}
DOMAINS = [f"D{i}" for i in range(1, 13)]
DOMAIN_LABEL = {
    "D1": "D1 MVTec-AD",
    "D2": "D2 GoodsAD",
    "D3": "D3 VisA",
    "D4": "D4 SDNET",
    "D5": "D5 MVTec-LOCO",
    "D6": "D6 Real3D-AD",
    "D7": "D7 LEVIR",
    "D8": "D8 Derma",
    "D9": "D9 BraTS",
    "D10": "D10 Liver CT",
    "D11": "D11 Kvasir",
    "D12": "D12 Road",
}

COLOR_DIRECT = "#4C72B0"
COLOR_V9 = "#DD8452"
COLOR_ENS = "#55A868"

fig, axes = plt.subplots(3, 1, figsize=(10.5, 8.0), sharex=True)

for ax, backbone in zip(axes, BACKBONE_ORDER):
    bb = DATA[backbone]
    per = bb["per_domain"]
    direct = [per[d]["direct"] for d in DOMAINS]
    v9 = [per[d]["v9"] for d in DOMAINS]
    ens = [per[d]["ensemble"] for d in DOMAINS]
    x = np.arange(len(DOMAINS))
    width = 0.27
    ax.bar(x - width, direct, width, label="Direct",
           color=COLOR_DIRECT, edgecolor="black", linewidth=0.4)
    ax.bar(x, v9, width, label="Agent (v9)",
           color=COLOR_V9, edgecolor="black", linewidth=0.4)
    ax.bar(x + width, ens, width, label="Ensemble (v10)",
           color=COLOR_ENS, edgecolor="black", linewidth=0.4)

    # Reference line at random
    ax.axhline(0.5, color="grey", linewidth=0.6, linestyle=":", alpha=0.6)

    # Macro numbers in title
    m = bb["macro"]
    boot = bb["bootstrap_1000_stratified_paired"]["Ens vs Direct"]
    sig = "$\\star$" if boot["ci95_lo_pp"] > 0 else ""
    ax.set_title(
        f"{BACKBONE_LABEL[backbone]} — "
        f"Direct {m['direct']:.3f} / v9 {m['v9']:.3f} / Ens {m['ensemble']:.3f}   "
        f"($\\Delta$Ens$-$Direct $=$ ${boot['delta_pp']:+.2f}$ pp, "
        f"95\\%CI $[{boot['ci95_lo_pp']:+.2f}, {boot['ci95_hi_pp']:+.2f}]${sig})",
        loc="left",
    )
    ax.set_ylim(0.35, 1.02)
    ax.set_ylabel("AUROC")
    ax.grid(axis="y", linewidth=0.3, alpha=0.5)
    if backbone == BACKBONE_ORDER[0]:
        ax.legend(loc="lower left", ncol=3, frameon=False)

axes[-1].set_xticks(np.arange(len(DOMAINS)))
axes[-1].set_xticklabels([DOMAIN_LABEL[d] for d in DOMAINS],
                         rotation=30, ha="right")

plt.tight_layout()
out = HERE / "fig_per_domain.pdf"
plt.savefig(out, bbox_inches="tight")
print(f"Wrote {out}")
