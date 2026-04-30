"""Generate fig_architecture.pdf — AnomalyClaw three-phase pipeline with three active routes.

Canonical routing (matches benchmark/scripts/infer.py run_agent_v2):
  Route A (Agree)       : y0==ye OR c0>=0.90 OR y0=anomalous OR rho<=0.8  -> commit s0    (+0 calls)
  Route B (Trust Expert): y0=normal & rho>1.5 & kappa>1.20                -> 0.3 s0 + 0.7 sigma(s_exp)   (+0 calls)
  Route D (Interpret)   : y0=normal & 0.8<rho<=1.5  (or rho>1.5 & kappa<=1.20) -> 2nd VLM call        (+1 call)

Route C (Enumerate) is a prototype only — shown in appendix, NOT in the main-table agent.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "pdf.fonttype": 42,
})

fig, ax = plt.subplots(figsize=(11.5, 4.3))
ax.set_xlim(0, 11.5)
ax.set_ylim(0, 4.8)
ax.axis("off")


def box(x, y, w, h, fc, ec="black", lw=0.8, round_r=0.08):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle=f"round,pad=0.02,rounding_size={round_r}",
                                facecolor=fc, edgecolor=ec, linewidth=lw))


def arrow(x1, y1, x2, y2, color="black", lw=1.1, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                                  arrowstyle="-|>", mutation_scale=11,
                                  color=color, linewidth=lw, linestyle=ls))


# ---------- Inputs ----------
box(0.0, 3.30, 1.3, 0.70, "#e6fffa")
ax.text(0.65, 3.65, "Query $x$", ha="center", va="center", fontsize=9)
box(0.0, 2.45, 1.3, 0.70, "#e6fffa")
ax.text(0.65, 2.80, "References $\\mathcal{R}$", ha="center", va="center", fontsize=9)
box(0.0, 1.60, 1.3, 0.70, "#fff5f0")
ax.text(0.65, 1.95, "Descriptor $d$", ha="center", va="center", fontsize=9)

# ---------- Phase 1: Perceive ----------
box(1.9, 2.90, 2.3, 1.10, "#bee3f8")
ax.text(3.05, 3.75, "Phase 1: Perceive", ha="center", va="center",
        fontsize=9, fontweight="bold")
ax.text(3.05, 3.43, "$\\mathrm{VLM}(x,\\mathcal{R},d)$",
        ha="center", va="center", fontsize=9)
ax.text(3.05, 3.12, "$\\rightarrow\\;(s_0, c_0, \\hat{y}_0)$",
        ha="center", va="center", fontsize=9)
ax.text(3.05, 2.72, "1 VLM call", ha="center", va="center",
        fontsize=7.5, style="italic", color="#2b6cb0")

# ---------- Phase 2: Expert ----------
box(1.9, 1.20, 2.3, 1.10, "#c6f6d5")
ax.text(3.05, 2.05, "Phase 2: Expert", ha="center", va="center",
        fontsize=9, fontweight="bold")
ax.text(3.05, 1.73, "SubspaceAD (DINOv2+PCA)",
        ha="center", va="center", fontsize=8.3)
ax.text(3.05, 1.42, "$\\rightarrow s_\\mathrm{exp},\\,\\mathrm{patches},\\,\\rho,\\,\\kappa$",
        ha="center", va="center", fontsize=8.6)
ax.text(3.05, 1.00, "0 VLM calls (cached)", ha="center", va="center",
        fontsize=7.5, style="italic", color="#2f855a")

# Inputs -> Phase 1 / Phase 2
arrow(1.3, 3.65, 1.9, 3.60)
arrow(1.3, 2.80, 1.9, 3.30)
arrow(1.3, 1.95, 1.9, 3.00)
arrow(1.3, 2.80, 1.9, 1.80)

# ---------- Phase 3: Router ----------
box(4.85, 2.00, 1.95, 1.40, "#fefcbf")
ax.text(5.825, 3.05, "Phase 3:", ha="center", va="center",
        fontsize=9.3, fontweight="bold")
ax.text(5.825, 2.75, "Adaptive", ha="center", va="center",
        fontsize=9.3, fontweight="bold")
ax.text(5.825, 2.45, "Router", ha="center", va="center",
        fontsize=9.3, fontweight="bold")
ax.text(5.825, 1.75, "test $(\\hat{y}_0, c_0, \\rho, \\kappa)$", ha="center", va="center",
        fontsize=7.6, style="italic", color="#744210")

# Phase 1/2 -> Router
arrow(4.2, 3.45, 4.85, 3.10)
ax.text(4.52, 3.40, "$(s_0, c_0, \\hat{y}_0)$", fontsize=7.3, color="#2b6cb0")
arrow(4.2, 1.80, 4.85, 2.30)
ax.text(4.30, 1.85, "$(s_\\mathrm{exp}, \\rho, \\kappa)$", fontsize=7.3, color="#2f855a")

# ---------- Three routes ----------
route_x = 7.45
route_w = 3.9
route_h = 0.95
route_ys = [3.30, 2.15, 1.00]
route_colors = ["#c6f6d5", "#bee3f8", "#e9d8fd"]
route_data = [
    ("Route A (Agree)",
     "$\\hat{y}_0{=}\\hat{y}_e$ or $c_0{\\geq}0.90$ or $\\hat{y}_0{=}$anomalous or $\\rho{\\leq}0.8$",
     "$\\rightarrow$ commit $s_0$   (+0 calls)"),
    ("Route B (Trust Expert)",
     "$\\hat{y}_0{=}$normal and $\\rho{>}1.5$ and $\\kappa{>}1.20$",
     "$\\rightarrow 0.3\\,s_0 + 0.7\\,\\sigma(s_\\mathrm{exp})$   (+0 calls)"),
    ("Route D (Interpret)",
     "$\\hat{y}_0{=}$normal and $0.8{<}\\rho$ (else Route B)",
     "$\\rightarrow$ VLM re-examines top-5 patches   (+1 call)"),
]
for y, c, (head, cond, body) in zip(route_ys, route_colors, route_data):
    box(route_x, y, route_w, route_h, c)
    ax.text(route_x + 0.12, y + route_h - 0.20, head, ha="left", va="center",
            fontsize=8.6, fontweight="bold")
    ax.text(route_x + 0.12, y + route_h - 0.50, cond, ha="left", va="center",
            fontsize=7.8)
    ax.text(route_x + 0.12, y + 0.20, body, ha="left", va="center",
            fontsize=7.8)

# Router -> each route
for y in route_ys:
    arrow(6.8, 2.70, route_x, y + route_h / 2, lw=0.8)

# ---------- Final score ----------
box(5.05, 0.15, 2.0, 0.55, "#edf2f7")
ax.text(6.05, 0.42, "Final score $s$", ha="center", va="center",
        fontsize=9.5, fontweight="bold")
for y in route_ys:
    arrow(route_x, y + route_h / 2, 7.05, 0.70, lw=0.5, color="#718096")

# Title
ax.text(5.75, 4.55,
        "AnomalyClaw: Perceive $\\rightarrow$ Expert $\\rightarrow$ Adaptive Router",
        ha="center", fontsize=11, fontweight="bold")

plt.tight_layout()
out = "/hdd1/jiangxi/AD-Agent/paper/figures/fig_architecture.pdf"
plt.savefig(out, bbox_inches="tight")
print(f"saved {out}")
