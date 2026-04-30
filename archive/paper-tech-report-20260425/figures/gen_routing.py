"""Generate fig_routing.pdf — routing distribution per domain on SeedVL test.

Bars show the fraction of items routed to {A agree, B trust_expert, D interpret}
out of each domain's item count. Labels follow D01..D11 convention.
"""
import json
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict, Counter

plt.rcParams.update({"font.family": "serif", "font.size": 8.5, "pdf.fonttype": 42})

RESULTS = "/hdd1/jiangxi/AD-Agent/benchmark/results"

DOMAIN_MAP = {
    "D1":  "D01", "D2":  "D02", "D4":  "D03", "D5":  "D04",
    "D5b": "D05", "D5c": "D06", "D5d": "D07", "D6":  "D08",
    "D7":  "D09", "D9":  "D10", "D10": "D11",
}


def classify_route(it):
    """Infer the route taken based on the agent's raw_output structure.

    Agent records {agree, interpret, expert_norm, v0, ...} per item.
      - raw_output.agree = True         -> Route A
      - raw_output.interpret is present -> Route D
      - else (expert fusion path)       -> Route B
    """
    ro = it.get("raw_output") or {}
    if ro.get("route") in ("agree", "agree_weak_expert"):
        return "A"
    if ro.get("interpret") is not None or ro.get("route") == "interpret":
        return "D"
    if ro.get("route") == "trust_expert":
        return "B"
    if ro.get("agree") is True:
        return "A"
    if ro.get("interpret") is not None:
        return "D"
    return "A"  # default fallback


def main():
    d = json.load(open(f"{RESULTS}/seedvl_agent_v1_test.json"))
    per = defaultdict(Counter)
    for it in d:
        dc = it.get("domain_code")
        if dc not in DOMAIN_MAP:
            continue
        per[DOMAIN_MAP[dc]][classify_route(it)] += 1

    labels = sorted(per.keys())
    totals = [sum(per[k].values()) for k in labels]
    frac_a = [per[k].get("A", 0) / totals[i] for i, k in enumerate(labels)]
    frac_b = [per[k].get("B", 0) / totals[i] for i, k in enumerate(labels)]
    frac_d = [per[k].get("D", 0) / totals[i] for i, k in enumerate(labels)]

    fig, ax = plt.subplots(figsize=(11.5, 2.8))
    x = np.arange(len(labels))
    ax.bar(x, frac_a, label="Route A (agree, 0 extra calls)", color="#2f855a",
           edgecolor="black", linewidth=0.3)
    ax.bar(x, frac_b, bottom=frac_a, label="Route B (trust expert, 0 extra calls)",
           color="#3182ce", edgecolor="black", linewidth=0.3)
    bottom_bd = [a + b for a, b in zip(frac_a, frac_b)]
    ax.bar(x, frac_d, bottom=bottom_bd,
           label="Route D (interpret, +1 call)",
           color="#805ad5", edgecolor="black", linewidth=0.3)

    # annotate total
    for i, (a, b, d_) in enumerate(zip(frac_a, frac_b, frac_d)):
        if b >= 0.015:
            ax.text(i, a + b / 2, f"{b*100:.0f}%", ha="center", va="center",
                    fontsize=7.0, color="white")
        if d_ >= 0.02:
            ax.text(i, a + b + d_ / 2, f"{d_*100:.0f}%", ha="center",
                    va="center", fontsize=7.0, color="white")

    overall = {r: sum(per[k].get(r, 0) for k in labels) for r in ("A", "B", "D")}
    total = sum(overall.values())
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel("Fraction of items", fontsize=9)
    ax.set_ylim(0, 1.05)
    calls_per_img = 1 + overall["D"] / total
    ax.set_title(
        f"AnomalyClaw routing on SeedVL test (overall: "
        f"A {overall['A']/total*100:.0f}% / B {overall['B']/total*100:.0f}% / "
        f"D {overall['D']/total*100:.0f}%; {calls_per_img:.2f} VLM calls/img)",
        fontsize=9.5)
    ax.legend(loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.28),
              frameon=True, fontsize=8.2)

    plt.tight_layout()
    out = "/hdd1/jiangxi/AD-Agent/paper/figures/fig_routing.pdf"
    plt.savefig(out, bbox_inches="tight")
    print(f"saved {out}")
    print(f"overall routing: {dict(overall)}  total={total}")


if __name__ == "__main__":
    main()
