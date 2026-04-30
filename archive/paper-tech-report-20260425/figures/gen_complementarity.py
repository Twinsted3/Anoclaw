"""Generate fig_complementarity.pdf — VLM x Expert correctness matrix per domain (GPT-5.4 test).

For each domain, split the 120 (or 98) test items into 4 cells:
    (v0 correct, expert correct)   both correct
    (v0 wrong,   expert correct)   expert-only correct  ← the agent's rescue opportunity
    (v0 correct, expert wrong)     v0-only correct
    (v0 wrong,   expert wrong)     both wrong

Binary correctness is computed using per-item 0.5 threshold on the anomaly
score (for v0) and comparison against the global expert median (for SubspaceAD).
"""
import json
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

plt.rcParams.update({"font.family": "serif", "font.size": 8.5, "pdf.fonttype": 42})

RESULTS = "/hdd1/jiangxi/AD-Agent/benchmark/results"

DOMAIN_MAP = {
    "D1":  "D01 Industrial",  "D2":  "D02 Retail",
    "D4":  "D03 Infrastr.",   "D5":  "D04 Dermo.",
    "D5b": "D05 Brain MRI",   "D5c": "D06 Liver CT",
    "D5d": "D07 Endoscopy",   "D6":  "D08 Change",
    "D7":  "D09 Road",        "D9":  "D10 Logical",
    "D10": "D11 VisA",
}


def main():
    agent = json.load(open(f"{RESULTS}/gpt54_agent_v1_test.json"))
    subs = {x["item_id"]: float(x["anomaly_score"])
            for x in json.load(open(f"{RESULTS}/subspacead_test.json"))
            if x.get("anomaly_score") is not None}
    global_median = float(np.median(list(subs.values())))

    per = defaultdict(lambda: [0, 0, 0, 0])  # BB, BW_expert, WB_vlm, WW
    for it in agent:
        dc = it.get("domain_code")
        if dc not in DOMAIN_MAP:
            continue
        iid = it["item_id"]
        if iid not in subs:
            continue
        y = int(it["label_gt"])
        v0_score = float((it.get("raw_output") or {}).get("v0_score",
                                                           it["anomaly_score"]))
        v0_pred = int(v0_score >= 0.5)
        exp_pred = int(subs[iid] > global_median)
        v0_correct = (v0_pred == y)
        exp_correct = (exp_pred == y)
        if v0_correct and exp_correct:
            per[dc][0] += 1
        elif (not v0_correct) and exp_correct:
            per[dc][1] += 1  # expert-only correct (rescue opportunity)
        elif v0_correct and (not exp_correct):
            per[dc][2] += 1  # vlm-only correct (risk)
        else:
            per[dc][3] += 1

    # Order by paper D01..D11
    ordered = [(DOMAIN_MAP[dc], per[dc]) for dc in DOMAIN_MAP
               if dc in per]
    labels = [n for n, _ in ordered]
    counts = np.array([c for _, c in ordered]).T  # 4 x N

    fig, ax = plt.subplots(figsize=(11.5, 2.8))
    # Show percentages inside each cell (row = category, col = domain)
    totals = counts.sum(axis=0)
    pct = 100.0 * counts / totals

    cmap_rows = ["#2f855a", "#3182ce", "#d69e2e", "#c53030"]
    row_names = [
        "Both correct",
        "Expert-only correct (rescue)",
        "VLM-only correct (risk)",
        "Both wrong",
    ]

    # Show as stacked horizontal bars? Use a heatmap-style layout:
    im = ax.imshow(pct, aspect="auto", cmap="YlGnBu", vmin=0, vmax=60)
    ax.set_xticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, rotation=28, ha="right", fontsize=8.3)
    ax.set_yticks(np.arange(4))
    ax.set_yticklabels(row_names, fontsize=8.5)
    # Annotate counts
    for i in range(4):
        for j in range(len(labels)):
            c = counts[i, j]
            p = pct[i, j]
            color = "white" if p > 35 else "black"
            ax.text(j, i, f"{c}\n{p:.0f}%", ha="center", va="center",
                    fontsize=7.2, color=color)
    ax.set_title(
        "VLM $\\times$ Expert correctness matrix per domain (GPT-5.4 test). "
        "Top-right cells are agent rescue opportunity.",
        fontsize=9.5)
    cb = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cb.set_label("%", fontsize=8)

    plt.tight_layout()
    out = "/hdd1/jiangxi/AD-Agent/paper/figures/fig_complementarity.pdf"
    plt.savefig(out, bbox_inches="tight")
    print(f"saved {out}")


if __name__ == "__main__":
    main()
