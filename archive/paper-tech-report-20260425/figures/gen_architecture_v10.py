"""Generate the main AnomalyClaw v10 architecture figure.

The figure emphasizes the headline system described in the method:
an always-on Direct VLM branch runs in parallel with a structured v9
refutation agent, and their independent scores are averaged.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUT_DIR = Path(__file__).resolve().parent

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 8.5,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.unicode_minus": False,
    }
)

fig, ax = plt.subplots(figsize=(13.4, 6.2))
ax.set_xlim(0, 13.4)
ax.set_ylim(0, 6.2)
ax.axis("off")
fig.patch.set_facecolor("white")


COL = {
    "input": ("#DCFCE7", "#16A34A"),
    "direct": ("#DBEAFE", "#2563EB"),
    "agent": ("#EDE9FE", "#7C3AED"),
    "tool": ("#F5F3FF", "#8B5CF6"),
    "expert": ("#ECFDF5", "#059669"),
    "fusion": ("#FFEDD5", "#EA580C"),
    "neutral": ("#F8FAFC", "#475569"),
    "loop": ("#FEF3C7", "#D97706"),
}


def rounded_box(
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    subtitle: str = "",
    *,
    theme: str = "neutral",
    title_size: float = 9.0,
    body_size: float = 7.4,
    lw: float = 1.4,
    z: int = 2,
):
    fc, ec = COL[theme]
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.045,rounding_size=0.13",
        facecolor=fc,
        edgecolor=ec,
        linewidth=lw,
        zorder=z,
    )
    patch.set_path_effects(
        [
            pe.SimplePatchShadow(offset=(1.4, -1.4), alpha=0.10, rho=0.98),
            pe.Normal(),
        ]
    )
    ax.add_patch(patch)
    compact = h < 0.78
    title_y = y + h * 0.68 if compact else y + h - 0.18
    body_y = y + h * 0.28 if compact else y + 0.17
    title_va = "center" if compact else "top"
    body_va = "center" if compact else "bottom"
    ax.text(
        x + w / 2,
        title_y,
        title,
        ha="center",
        va=title_va,
        fontsize=title_size,
        fontweight="bold",
        color="#0F172A",
        zorder=z + 1,
    )
    if subtitle:
        ax.text(
            x + w / 2,
            body_y,
            subtitle,
            ha="center",
            va=body_va,
            fontsize=body_size,
            color="#334155",
            linespacing=1.18,
            zorder=z + 1,
        )
    return patch


def group_box(x: float, y: float, w: float, h: float, label: str, color: str):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.06,rounding_size=0.18",
        facecolor=color,
        edgecolor="#CBD5E1",
        linewidth=1.1,
        linestyle="-",
        zorder=0,
    )
    ax.add_patch(patch)
    ax.text(
        x + 0.18,
        y + h - 0.16,
        label,
        ha="left",
        va="top",
        fontsize=8.0,
        fontweight="bold",
        color="#475569",
        bbox=dict(boxstyle="round,pad=0.10", fc=color, ec="none", alpha=0.95),
        zorder=1,
    )


def arrow(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    label: str = "",
    rad: float = 0.0,
    color: str = "#1F2937",
    lw: float = 1.8,
    dashed: bool = False,
    label_offset: tuple[float, float] = (0.0, 0.0),
    z: int = 5,
):
    patch = FancyArrowPatch(
        (x1, y1),
        (x2, y2),
        arrowstyle="-|>",
        mutation_scale=13,
        linewidth=lw,
        color=color,
        linestyle="--" if dashed else "-",
        connectionstyle=f"arc3,rad={rad}",
        shrinkA=2,
        shrinkB=2,
        zorder=z,
    )
    ax.add_patch(patch)
    if label:
        xm = (x1 + x2) / 2 + label_offset[0]
        ym = (y1 + y2) / 2 + label_offset[1]
        ax.text(
            xm,
            ym,
            label,
            ha="center",
            va="center",
            fontsize=7.2,
            color=color,
            bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.88),
            zorder=z + 1,
        )


def pill(x: float, y: float, text: str, *, fc: str, ec: str):
    patch = FancyBboxPatch(
        (x, y),
        1.74,
        0.32,
        boxstyle="round,pad=0.03,rounding_size=0.16",
        facecolor=fc,
        edgecolor=ec,
        linewidth=0.9,
        zorder=6,
    )
    ax.add_patch(patch)
    ax.text(x + 0.87, y + 0.16, text, ha="center", va="center", fontsize=6.8, color=ec, zorder=7)


# Title
ax.text(
    6.7,
    5.93,
    "AnomalyClaw v10: Always-on Direct VLM + Structured Refutation Agent",
    ha="center",
    va="center",
    fontsize=13.2,
    fontweight="bold",
    color="#0F172A",
)
ax.text(
    6.7,
    5.66,
    "Training-free cross-domain visual anomaly detection with frozen VLMs, cached experts, and auditable tool traces",
    ha="center",
    va="center",
    fontsize=8.8,
    color="#475569",
)


# Inputs
group_box(0.22, 1.56, 1.72, 3.70, "Input bundle", "#F8FAFC")
rounded_box(0.45, 4.18, 1.25, 0.66, "Query", r"image $x$", theme="input", title_size=8.2, body_size=6.8)
rounded_box(0.45, 3.36, 1.25, 0.66, "References", r"normal set $\mathcal{R}$", theme="input", title_size=8.2, body_size=6.8)
rounded_box(0.45, 2.54, 1.25, 0.66, "Task", "prompt / domain", theme="input", title_size=8.2, body_size=6.8)
rounded_box(0.45, 1.72, 1.25, 0.66, "Backbone", "same VLM", theme="input", title_size=8.2, body_size=6.8)


# Frozen assets / evidence bank
group_box(2.25, 0.31, 6.10, 1.24, "Frozen evidence bank available to v9", "#FAFAFA")
rounded_box(
    2.48,
    0.56,
    2.58,
    0.68,
    "13 tool primitives",
    "visual | reference | structural\nsemantic lookup",
    theme="tool",
    title_size=8.0,
    body_size=6.3,
)
rounded_box(
    5.32,
    0.56,
    2.78,
    0.68,
    "Cached expert probes",
    "SubspaceAD | AnomalyVFM\npatch-kNN heatmaps",
    theme="expert",
    title_size=8.0,
    body_size=6.3,
)


# Direct branch
group_box(2.25, 4.04, 3.45, 1.06, "Independent direct branch", "#F8FBFF")
rounded_box(
    2.58,
    4.13,
    2.78,
    0.72,
    "Direct VLM scorer",
    "descriptor-free prompt\n1 parallel VLM call",
    theme="direct",
    title_size=8.8,
    body_size=6.8,
)
rounded_box(
    6.02,
    4.13,
    1.08,
    0.72,
    r"$s_{\mathrm{Direct}}$",
    "robust rank\nestimate",
    theme="direct",
    title_size=9.0,
    body_size=6.3,
)


# v9 branch
group_box(2.25, 1.72, 7.82, 2.14, "v9 refutation agent branch: bounded K=5 structured deliberation", "#FBFAFF")
rounded_box(
    2.52,
    2.50,
    1.72,
    0.84,
    "1. Suspect list",
    "initial score\ncandidate features\nrefutation target",
    theme="agent",
    title_size=8.0,
    body_size=6.2,
)
rounded_box(
    4.72,
    2.50,
    1.78,
    0.84,
    "2. Refutation tool",
    "test whether target\nappears in references",
    theme="loop",
    title_size=8.0,
    body_size=6.2,
)
rounded_box(
    6.98,
    2.50,
    1.72,
    0.84,
    "3. Verdict",
    "found in ref /\nnot found / inconcl.",
    theme="agent",
    title_size=8.0,
    body_size=6.2,
)
rounded_box(
    8.92,
    2.50,
    0.88,
    0.84,
    r"$s_{v9}$",
    "fine-grained\nagent score",
    theme="agent",
    title_size=9.0,
    body_size=6.0,
)
rounded_box(
    4.18,
    1.88,
    3.92,
    0.56,
    "Explicit anti-confirmation contract",
    "tools retire candidates; remaining features update the score",
    theme="neutral",
    title_size=7.4,
    body_size=5.9,
    lw=1.0,
)
pill(8.33, 1.96, "auditable trace", fc="#F8FAFC", ec="#64748B")
pill(8.33, 1.58, "1-5 VLM calls", fc="#FFF7ED", ec="#EA580C")


# Fusion and output
rounded_box(
    10.78,
    3.13,
    1.30,
    1.05,
    "Fixed ensemble",
    r"$s = 0.5s_{\mathrm{Direct}}$" "\n" r"$+\,0.5s_{v9}$",
    theme="fusion",
    title_size=8.4,
    body_size=7.5,
)
rounded_box(
    12.32,
    3.15,
    0.86,
    1.00,
    "Output",
    "anomaly score\n+ trace",
    theme="fusion",
    title_size=8.4,
    body_size=6.8,
)


# Arrows from inputs
arrow(1.72, 4.51, 2.58, 4.49, label=r"$x,\mathcal{R}$", label_offset=(0.0, 0.18))
arrow(1.72, 3.69, 2.52, 2.98, label=r"$x,\mathcal{R}$", label_offset=(-0.05, 0.10))
arrow(1.72, 2.87, 2.52, 2.80, label="task context", label_offset=(0.0, -0.20))
arrow(1.72, 2.05, 2.52, 2.64, label="same backbone", label_offset=(-0.03, -0.18))

# Direct branch arrows
arrow(5.36, 4.49, 6.02, 4.49, label="score")
arrow(7.10, 4.49, 10.78, 3.83, label="parallel branch", rad=-0.10, label_offset=(0.25, 0.15))

# v9 internal arrows
arrow(4.24, 2.92, 4.72, 2.92, label="target")
arrow(6.50, 2.92, 6.98, 2.92, label="evidence")
arrow(8.70, 2.92, 8.92, 2.92, label="update", label_offset=(0.0, 0.18))
arrow(7.80, 2.48, 5.25, 2.45, label="next feature if any", rad=0.20, color="#92400E", lw=1.5)

# Evidence bank to refutation tool
arrow(3.74, 1.24, 5.12, 2.50, label="tool outputs", dashed=True, color="#6D28D9", lw=1.4, label_offset=(-0.16, 0.03))
arrow(6.70, 1.24, 5.86, 2.50, label="expert maps", dashed=True, color="#047857", lw=1.4, label_offset=(0.18, 0.03))

# v9 to fusion, fusion to output
arrow(9.80, 2.92, 10.78, 3.42, label="agent branch")
arrow(12.08, 3.66, 12.32, 3.66)

# Bottom design notes
note_y = 0.12
for x, text, fc, ec in [
    (8.68, "No training", "#F0FDFA", "#0F766E"),
    (10.05, "No per-backbone tuning", "#EFF6FF", "#2563EB"),
    (11.66, "Parallel wall-time", "#FFF7ED", "#EA580C"),
]:
    w = 1.17 if text == "No training" else 1.72 if text == "Parallel wall-time" else 1.72
    patch = FancyBboxPatch(
        (x, note_y),
        w,
        0.36,
        boxstyle="round,pad=0.03,rounding_size=0.18",
        facecolor=fc,
        edgecolor=ec,
        linewidth=0.9,
        zorder=4,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, note_y + 0.18, text, ha="center", va="center", fontsize=7.0, color=ec, zorder=5)


for suffix in ("pdf", "png", "svg"):
    out = OUT_DIR / f"fig_architecture.{suffix}"
    fig.savefig(out, bbox_inches="tight", pad_inches=0.04, dpi=300)
    print(f"saved {out}")
