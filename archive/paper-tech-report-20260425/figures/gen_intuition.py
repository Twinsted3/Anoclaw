"""Generate fig_intuition.pdf — three-panel story of AnomalyClaw contributions.

Panel A: Descriptors dominate (generic vs task-anchored) on GPT-5.4.
Panel B: Score fusion uniformly strengthens all three backbones at 1 VLM call.
Panel C: AnomalyClaw trades VLM calls for interpretability vs fusion.
"""
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

fig, axes = plt.subplots(1, 3, figsize=(11.5, 2.9),
                         gridspec_kw={"width_ratios": [1.0, 1.3, 1.3]})

# ---------- Panel A: descriptors across 3 backbones ----------
# Source: paper/figures/descriptor_cis.json (paired bootstrap, n=1298 each).
axA = axes[0]
backbonesA = ["GPT-5.4", "SeedVL", "Qwen3.5"]
genericA = [0.761, 0.748, 0.760]
taskA    = [0.825, 0.789, 0.792]
deltasA  = [t - g for g, t in zip(genericA, taskA)]
xA = np.arange(len(backbonesA))
wA = 0.35
axA.bar(xA - wA / 2, genericA, wA, label="Generic", color="#a9a9a9",
        edgecolor="black", linewidth=0.4)
axA.bar(xA + wA / 2, taskA, wA, label="Task-anchored", color="#2b6cb0",
        edgecolor="black", linewidth=0.4)
for i, (g, t) in enumerate(zip(genericA, taskA)):
    axA.text(i - wA / 2, g + 0.003, f"{g:.3f}", ha="center", fontsize=7)
    axA.text(i + wA / 2, t + 0.003, f"{t:.3f}", ha="center", fontsize=7,
             fontweight="bold")
    axA.text(i, max(g, t) + 0.020, f"+{(t - g) * 100:.1f} pp", ha="center",
             color="#c53030", fontsize=8, fontweight="bold")
axA.set_xticks(xA)
axA.set_xticklabels(backbonesA, fontsize=8.5)
axA.set_ylim(0.70, 0.88)
axA.set_ylabel("Macro AUROC")
axA.set_title("(a) Descriptors dominate (all 3 backbones)")
axA.legend(loc="lower right", frameon=True, fontsize=8)
axA.grid(axis="y", linestyle=":", alpha=0.5)

# ---------- Panel B: fusion across backbones ----------
axB = axes[1]
backbones = ["GPT-5.4", "SeedVL", "Qwen3.5"]
# Source: paper/figures/bootstrap_cis.json (paired bootstrap, n=1298)
# v0 from agent file's Phase-1 embedded scores; fusion = 0.8*v0+0.2*sigmoid(exp - global_median).
v0 = [0.822, 0.795, 0.792]
fusion = [0.835, 0.813, 0.851]
x = np.arange(len(backbones))
w = 0.35
axB.bar(x - w / 2, v0, w, label="v0 Direct (1.0 call)",
        color="#718096", edgecolor="black", linewidth=0.5)
axB.bar(x + w / 2, fusion, w, label="v0 + SubspaceAD fusion (1.0)",
        color="#2c7a7b", edgecolor="black", linewidth=0.5)
for i, (a, b) in enumerate(zip(v0, fusion)):
    axB.text(i - w / 2, a + 0.003, f"{a:.3f}", ha="center", fontsize=7)
    axB.text(i + w / 2, b + 0.003, f"{b:.3f}", ha="center", fontsize=7,
             fontweight="bold")
for i, (a, b) in enumerate(zip(v0, fusion)):
    top = max(a, b)
    axB.text(i, top + 0.015, f"+{(b - a) * 100:.1f} pp", ha="center",
             color="#c53030", fontsize=8, fontweight="bold")
axB.set_xticks(x)
axB.set_xticklabels(backbones)
axB.set_ylim(0.74, 0.90)
axB.set_ylabel("Macro AUROC")
axB.set_title("(b) Score fusion: zero-cost baseline\n"
              "($s = 0.8\\,s_{0} + 0.2\\,\\sigma(s_\\mathrm{SubspaceAD})$)")
axB.legend(loc="lower right", frameon=True, framealpha=0.9)
axB.grid(axis="y", linestyle=":", alpha=0.5)

# ---------- Panel C: agent vs fusion ----------
axC = axes[2]
fusion2 = [0.835, 0.813, 0.851]
agent = [0.826, 0.818, 0.811]
axC.bar(x - w / 2, fusion2, w, label="Score fusion (1.0 call)",
        color="#2c7a7b", edgecolor="black", linewidth=0.5)
axC.bar(x + w / 2, agent, w, label="AnomalyClaw ($\\sim$1.3 calls)",
        color="#b7791f", edgecolor="black", linewidth=0.5)
for i, (a, b) in enumerate(zip(fusion2, agent)):
    axC.text(i - w / 2, a + 0.003, f"{a:.3f}", ha="center", fontsize=7)
    axC.text(i + w / 2, b + 0.003, f"{b:.3f}", ha="center", fontsize=7)
axC.set_xticks(x)
axC.set_xticklabels(backbones)
axC.set_ylim(0.74, 0.89)
axC.set_ylabel("Macro AUROC")
axC.set_title("(c) Agent trades accuracy for\nauditable decision traces")
axC.legend(loc="lower right", frameon=True, framealpha=0.9)
axC.grid(axis="y", linestyle=":", alpha=0.5)

plt.tight_layout()
out = "/hdd1/jiangxi/AD-Agent/paper/figures/fig_intuition.pdf"
plt.savefig(out, bbox_inches="tight")
print(f"saved {out}")
