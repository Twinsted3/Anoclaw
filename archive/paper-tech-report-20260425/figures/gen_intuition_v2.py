"""Generate fig_intuition.pdf (v2) — three-panel story for AnomalyClaw v2.

Panel A: Per-domain best strategy varies — no single strategy wins uniformly.
         Heatmap of (domain, strategy) AUROC with best cell marked per row.
Panel B: Router captures the complementarity gap — macro AUROC for
         direct / fusion / calibration-router / oracle on 3 backbones.
Panel C: Router assignment agreement with oracle — per-domain alignment
         across backbones.
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "legend.fontsize": 8,
    "pdf.fonttype": 42,
})

REFINE = Path("/hdd1/jiangxi/AD-Agent/refine-logs")
MATRIX = json.load(open(REFINE / "PER_DOMAIN_STRATEGY_MATRIX.json"))
ROUTER = json.load(open(REFINE / "ROUTER_RESULTS.json"))

fig = plt.figure(figsize=(12.2, 3.4))
gs = fig.add_gridspec(1, 3, width_ratios=[1.3, 1.0, 1.1])
axA, axB, axC = fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), fig.add_subplot(gs[2])


# ---------- Panel A: per-domain best strategy heatmap (SeedVL) ----------
bk = "seedvl"
strategies = ["direct", "fusion_v0_subspace", "debate", "interpret"]
strat_labels = ["Direct", "Fusion", "Debate", "Interpret"]
matrix = MATRIX["matrix"]
domains = MATRIX["domains"]
doms = [d for d in domains if d not in {"D3"}]  # D3 excluded from test in paper
heat = np.full((len(doms), len(strategies)), np.nan)
for i, d in enumerate(doms):
    for j, s in enumerate(strategies):
        key = f"{bk}|{s}"
        v = matrix.get(key, {}).get(d, {}).get("auroc")
        if v is not None:
            heat[i, j] = v

cmap = plt.cm.RdYlGn
cmap.set_bad(color="#eeeeee")
im = axA.imshow(heat, aspect="auto", cmap=cmap, vmin=0.5, vmax=1.0)
axA.set_xticks(range(len(strategies)))
axA.set_xticklabels(strat_labels, fontsize=8)
axA.set_yticks(range(len(doms)))
axA.set_yticklabels(doms, fontsize=7)
for i in range(len(doms)):
    row = heat[i]
    if np.all(np.isnan(row)):
        continue
    best_j = int(np.nanargmax(row))
    for j in range(len(strategies)):
        val = heat[i, j]
        if np.isnan(val):
            continue
        txt = f"{val:.2f}".lstrip("0")
        col = "black" if 0.6 <= val <= 0.9 else "white"
        axA.text(j, i, txt, ha="center", va="center",
                 fontsize=6.5, color=col,
                 fontweight="bold" if j == best_j else "normal")
    # box around best
    rect = mpatches.Rectangle((best_j - 0.48, i - 0.48), 0.96, 0.96,
                              fill=False, edgecolor="#1a365d", linewidth=1.3)
    axA.add_patch(rect)
axA.set_title("(a) Best strategy varies per domain (SeedVL test)")
fig.colorbar(im, ax=axA, shrink=0.85, pad=0.01).set_label("AUROC", fontsize=8)


# ---------- Panel B: router captures gap ----------
backbones = ["GPT-5.4", "SeedVL", "Qwen3.5"]
keys = ["gpt54", "seedvl", "qwen35"]
direct_v = [ROUTER[k]["baselines"]["direct"]["macro"] for k in keys]
fusion_v = [ROUTER[k]["baselines"]["fusion"]["macro"] for k in keys]
desc_v = [ROUTER[k]["descriptor_macro"] for k in keys]
calib_v = [ROUTER[k]["calibration_macro"] for k in keys]
oracle_v = [ROUTER[k]["oracle_macro"] for k in keys]

x = np.arange(len(backbones))
w = 0.17
colors = ["#718096", "#2c7a7b", "#b7791f", "#2b6cb0", "#2f855a"]
series = [
    ("Direct", direct_v),
    ("Fusion", fusion_v),
    ("Descriptor router", desc_v),
    ("Calib. router", calib_v),
    ("Oracle", oracle_v),
]
for idx, (lbl, vals) in enumerate(series):
    axB.bar(x + (idx - 2) * w, vals, w, label=lbl, color=colors[idx],
            edgecolor="black", linewidth=0.4)
axB.set_xticks(x)
axB.set_xticklabels(backbones)
axB.set_ylim(0.62, 0.88)
axB.set_ylabel("Macro AUROC")
axB.set_title("(b) Router closes single-strategy gap")
axB.legend(loc="lower right", ncol=1, fontsize=7, framealpha=0.9)
axB.grid(axis="y", linestyle=":", alpha=0.5)


# ---------- Panel C: router assignment per backbone ----------
# Bar-stacked chart showing, per backbone, fraction of domains assigned to each strategy
# by the calibration router, compared to oracle
assignments = {
    "Oracle GPT-5.4": ROUTER["gpt54"]["oracle_assignment"],
    "Calib GPT-5.4": ROUTER["gpt54"]["calibration_assignment"],
    "Oracle SeedVL": ROUTER["seedvl"]["oracle_assignment"],
    "Calib SeedVL": ROUTER["seedvl"]["calibration_assignment"],
    "Oracle Qwen3.5": ROUTER["qwen35"]["oracle_assignment"],
    "Calib Qwen3.5": ROUTER["qwen35"]["calibration_assignment"],
}
strat_order = ["direct", "fusion", "debate", "interpret", "subspacead"]
strat_colors = {"direct": "#718096", "fusion": "#2c7a7b",
                "debate": "#b7791f", "interpret": "#2b6cb0",
                "subspacead": "#553c9a"}
labels = list(assignments.keys())
bottom = np.zeros(len(labels))
for s in strat_order:
    counts = np.array([sum(1 for v in a.values() if v == s) for a in assignments.values()],
                      dtype=float)
    counts = counts / max(len(next(iter(assignments.values()))), 1) * 100.0
    axC.barh(labels, counts, left=bottom, color=strat_colors[s],
             edgecolor="white", linewidth=0.5, label=s.replace("_", " "))
    bottom += counts
axC.set_xlim(0, 100)
axC.set_xlabel("% domains assigned")
axC.set_title("(c) Strategy mix: calib vs oracle")
axC.invert_yaxis()
axC.legend(loc="lower right", fontsize=7, framealpha=0.9)
axC.grid(axis="x", linestyle=":", alpha=0.4)

plt.tight_layout()
out = "/hdd1/jiangxi/AD-Agent/paper/figures/fig_intuition.pdf"
plt.savefig(out, bbox_inches="tight")
print(f"saved {out}")
