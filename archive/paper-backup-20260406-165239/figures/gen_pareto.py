#!/usr/bin/env python3
"""Generate Pareto cost-accuracy scatter plot for AnomaClaw paper."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np

# ── Style ──────────────────────────────────────────────────────────────────────
matplotlib.rcParams.update({
    'font.size': 10,
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'Times', 'DejaVu Serif'],
    'axes.labelsize': 10,
    'axes.titlesize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 8.5,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    'axes.grid': False,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'text.usetex': False,
    'mathtext.fontset': 'stix',
})

# ── Data ───────────────────────────────────────────────────────────────────────
methods = [
    ("DINOv2-Global",       0,   0.653, False),
    ("DINOv2-PatchNN",      0,   0.661, False),
    ("PatchCore Expert",    0,   0.831, True),   # Pareto
    ("Expert-as-Router",    49,  0.844, True),   # Pareto
    ("Ret+VLM",             114, 0.866, False),
    ("Multi-Round Agent",   137, 0.873, False),
    ("Expert-Informed VLM", 132, 0.877, False),
    ("AnomaClaw (Ours)",    132, 0.882, True),   # Pareto
]

# ── Colors ─────────────────────────────────────────────────────────────────────
C_OURS = '#C0392B'       # deep red for AnomaClaw
C_PARETO = '#2980B9'     # blue for other Pareto points
C_BASELINE = '#7F8C8D'   # grey for non-Pareto
C_DOMINATED = '#E67E22'  # orange for dominated agent baseline

# ── Plot ───────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(1, 1, figsize=(5.5, 3.8))

# Draw Pareto frontier first (behind points)
pareto_x = [0, 49, 132]
pareto_y = [0.831, 0.844, 0.882]
ax.plot(pareto_x, pareto_y, color=C_PARETO, linewidth=1.2, linestyle='--',
        alpha=0.5, zorder=1)
# Shade Pareto-dominated region lightly
ax.fill_between(pareto_x, pareto_y, [0.6]*3, alpha=0.04, color=C_PARETO, zorder=0)

# Plot each point
for name, tokens, auroc, is_pareto in methods:
    if name == "AnomaClaw (Ours)":
        color = C_OURS
        marker = '*'
        ms = 16
        zorder = 10
    elif name == "Multi-Round Agent":
        color = C_DOMINATED
        marker = 's'
        ms = 7
        zorder = 5
    elif is_pareto:
        color = C_PARETO
        marker = 'D'
        ms = 7
        zorder = 5
    else:
        color = C_BASELINE
        marker = 'o'
        ms = 6
        zorder = 3

    ax.scatter(tokens, auroc, color=color, marker=marker, s=ms**2,
               zorder=zorder, edgecolors='white', linewidths=0.5)

# ── Labels ─────────────────────────────────────────────────────────────────────
label_offsets = {
    "DINOv2-Global":       (6, -12),
    "DINOv2-PatchNN":      (6, 5),
    "PatchCore Expert":    (6, -12),
    "Expert-as-Router":    (5, 8),
    "Ret+VLM":             (-8, -16),
    "Multi-Round Agent":   (5, -16),
    "Expert-Informed VLM": (-95, 5),
    "AnomaClaw (Ours)":    (-5, 8),
}

for name, tokens, auroc, is_pareto in methods:
    dx, dy = label_offsets.get(name, (5, 5))
    weight = 'bold' if name == "AnomaClaw (Ours)" else 'normal'
    fontsize = 8.5 if name == "AnomaClaw (Ours)" else 7.5
    color = C_OURS if name == "AnomaClaw (Ours)" else '#2C3E50'

    ax.annotate(
        name, (tokens, auroc),
        xytext=(dx, dy), textcoords='offset points',
        fontsize=fontsize, fontweight=weight, color=color,
        path_effects=[pe.withStroke(linewidth=2.5, foreground='white')],
    )

# ── Axes ───────────────────────────────────────────────────────────────────────
ax.set_xlabel('VLM Tokens per 100 Images (thousands)')
ax.set_ylabel('Macro AUROC')
ax.set_xlim(-8, 155)
ax.set_ylim(0.62, 0.91)
ax.set_xticks([0, 25, 50, 75, 100, 125, 150])

# Light grid
ax.yaxis.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)
ax.set_axisbelow(True)

# Legend with Pareto frontier entry
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='*', color='w', markerfacecolor=C_OURS, markersize=12, label='AnomaClaw (Ours)'),
    Line2D([0], [0], marker='D', color='w', markerfacecolor=C_PARETO, markersize=7, label='Pareto-optimal'),
    Line2D([0], [0], linestyle='--', color=C_PARETO, alpha=0.5, label='Pareto frontier'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor=C_DOMINATED, markersize=7, label='Dominated agent'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor=C_BASELINE, markersize=6, label='Other baselines'),
]
ax.legend(handles=legend_elements, loc='lower right', frameon=True, fancybox=False,
          edgecolor='#CCCCCC', fontsize=7, ncol=1)

fig.savefig('paper/figures/pareto.pdf', format='pdf')
fig.savefig('paper/figures/pareto.png', format='png')
print('Saved: paper/figures/pareto.pdf + .png')
