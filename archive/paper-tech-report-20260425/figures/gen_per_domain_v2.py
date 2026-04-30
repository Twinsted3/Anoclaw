"""fig_per_domain.pdf (v2) — per-domain AUROC across strategies + router choice
overlay. One panel per backbone."""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({"font.family": "serif", "font.size": 9, "pdf.fonttype": 42})

REFINE = Path("/hdd1/jiangxi/AD-Agent/refine-logs")
MATRIX = json.load(open(REFINE / "PER_DOMAIN_STRATEGY_MATRIX.json"))
ROUTER = json.load(open(REFINE / "ROUTER_RESULTS.json"))

fig, axes = plt.subplots(3, 1, figsize=(11.5, 6.5), sharex=False)

bk_pretty = {"gpt54": "GPT-5.4", "seedvl": "SeedVL", "qwen35": "Qwen3.5-VL"}

strategies = ["direct", "fusion_v0_subspace", "debate", "interpret"]
strat_labels = ["Direct", "Fusion", "Debate", "Interpret"]
strat_colors = ["#718096", "#2c7a7b", "#b7791f", "#2b6cb0"]
domains_order = ["D1", "D2", "D3", "D4", "D5", "D5b", "D5c", "D5d",
                 "D6", "D7", "D8", "D9", "D10", "D11", "D12"]

for row, bk in enumerate(["gpt54", "seedvl", "qwen35"]):
    ax = axes[row]
    doms_avail = [d for d in domains_order
                  if any(d in MATRIX["matrix"].get(f"{bk}|{s}", {}) for s in strategies)]
    x = np.arange(len(doms_avail))
    w = 0.18
    for j, strat in enumerate(strategies):
        vals = []
        for d in doms_avail:
            v = MATRIX["matrix"].get(f"{bk}|{strat}", {}).get(d, {}).get("auroc")
            vals.append(v if v is not None else 0)
        ax.bar(x + (j - 1.5) * w, vals, w, label=strat_labels[j],
               color=strat_colors[j], edgecolor="black", linewidth=0.3)

    # Calibration router chosen strategy highlight
    calib = ROUTER[bk]["calibration_assignment"]
    for i, d in enumerate(doms_avail):
        chosen = calib.get(d)
        if chosen in ("fusion", "fusion_v0_subspace"):
            label = "fusion"
            j = strategies.index("fusion_v0_subspace")
        elif chosen == "subspacead":
            # expert-only fallback — mark separately
            j = None
        elif chosen in ("direct", "debate", "interpret"):
            j = strategies.index(chosen)
        else:
            j = None
        if j is not None:
            val = MATRIX["matrix"].get(f"{bk}|{strategies[j]}", {}).get(d, {}).get("auroc", 0)
            ax.plot(x[i] + (j - 1.5) * w, val + 0.02, marker="v",
                    color="red", markersize=5)

    ax.set_xticks(x)
    ax.set_xticklabels(doms_avail, fontsize=8)
    ax.set_ylim(0.4, 1.02)
    ax.set_ylabel("AUROC")
    ax.set_title(f"{bk_pretty[bk]} — red $\\blacktriangledown$ = calib. router choice")
    if row == 0:
        ax.legend(loc="lower left", ncol=4, fontsize=7, framealpha=0.9)
    ax.grid(axis="y", linestyle=":", alpha=0.4)

plt.tight_layout()
out = "/hdd1/jiangxi/AD-Agent/paper/figures/fig_per_domain.pdf"
plt.savefig(out, bbox_inches="tight")
print(f"saved {out}")
