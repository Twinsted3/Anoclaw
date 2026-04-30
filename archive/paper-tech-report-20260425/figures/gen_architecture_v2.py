"""fig_architecture.pdf (v2): Tool x Expert x Strategy framework diagram for
AnomalyClaw."""
import matplotlib.pyplot as plt
import matplotlib.patches as mp
import numpy as np

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "pdf.fonttype": 42,
})

fig, ax = plt.subplots(figsize=(12.0, 4.6))
ax.set_xlim(0, 120)
ax.set_ylim(0, 50)
ax.axis("off")


def box(x, y, w, h, label, sub="", color="#e2e8f0", edge="#2d3748", fs=9, bold=True):
    r = mp.FancyBboxPatch((x, y), w, h,
                          boxstyle="round,pad=0.3",
                          fc=color, ec=edge, linewidth=1.1)
    ax.add_patch(r)
    ax.text(x + w / 2, y + h - 1.3, label, ha="center", va="top",
            fontsize=fs, fontweight="bold" if bold else "normal")
    if sub:
        ax.text(x + w / 2, y + 1.0, sub, ha="center", va="bottom", fontsize=7.5,
                color="#2d3748")


def arrow(x1, y1, x2, y2, color="#4a5568"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=1.3))


# Inputs on left
box(1, 36, 14, 8, "Query + refs",
    sub="image x, refs R\ndomain descriptor d", color="#fefcbf")
box(1, 25, 14, 8, "Domain tag",
    sub="family in {industrial,\nmedical, logical, road,\nchange, retail, infra}",
    color="#fefcbf")

# Router in middle
box(20, 28, 22, 18, "Router", color="#fed7d7",
    sub="(a) Offline: descriptor\n-> default strategy\n"
        "(b) Online: expert concentr.\n$\\rho, \\kappa$ may override")

# Three axes
# Axis 1: Tools
ax.text(52, 46, "Tool library", fontsize=10, fontweight="bold", color="#2d3748")
tools = [
    ("domain_descriptor", "0 calls"),
    ("reference_retriever", "0 calls"),
    ("hotspot_cropper", "0 calls"),
    ("component_counter", "0 calls"),
    ("knowledge_lookup", "0 calls"),
]
for i, (n, c) in enumerate(tools):
    y = 43 - i * 3.6
    box(47, y, 20, 3.0, n, sub=c, color="#e6fffa", fs=7.5, bold=True)

# Axis 2: Experts
ax.text(74, 46, "Expert pool", fontsize=10, fontweight="bold", color="#2d3748")
experts = [
    ("SubspaceAD", "DINOv2 + PCA 99% EV"),
    ("PatchKNN", "DINOv2 patch distance"),
    ("Global", "DINOv2 CLS cosine"),
]
for i, (n, c) in enumerate(experts):
    y = 43 - i * 4.6
    box(69, y, 22, 4.0, n, sub=c, color="#e9d8fd", fs=8, bold=True)

# Axis 3: Strategies
ax.text(99, 46, "Strategies", fontsize=10, fontweight="bold", color="#2d3748")
strategies = [
    ("Direct", "1 VLM call"),
    ("Fusion", "1 VLM + expert"),
    ("Debate", "2 VLM calls"),
    ("Interpret", "~1.3 VLM calls"),
]
for i, (n, c) in enumerate(strategies):
    y = 43 - i * 3.6
    box(94, y, 22, 3.0, n, sub=c, color="#fed7aa", fs=8, bold=True)

# Output
box(48, 2, 56, 10, "Final anomaly score & trace", color="#c6f6d5",
    sub="s in [0,1]; decision trace includes\n"
        "{tools used, expert, strategy, key patches, VLM evidence}")

# Arrows from input -> router
arrow(15, 40, 20, 40)
arrow(15, 29, 20, 32)
# Arrows from router -> axes
arrow(42, 42, 47, 43)  # tools
arrow(42, 38, 69, 40)  # experts
arrow(42, 32, 94, 36)  # strategies
# Arrows to output
arrow(58, 18, 60, 12)
arrow(80, 18, 76, 12)
arrow(100, 18, 92, 12)

# Title / caption
ax.text(60, 48.5, "AnomalyClaw: Tool x Expert x Strategy agent",
        ha="center", fontsize=11, fontweight="bold")

out = "/hdd1/jiangxi/AD-Agent/paper/figures/fig_architecture.pdf"
plt.savefig(out, bbox_inches="tight")
print(f"saved {out}")
