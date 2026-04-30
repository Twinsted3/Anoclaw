"""Generate fig_per_domain.pdf — SeedVL per-domain comparison (4 methods).

Labels use the paper's D01..D11 convention (surveillance/D8 is excluded).
Data is computed paired from the agent file (v0 comes from agent's Phase 1)
to guarantee item-level consistency with the bootstrap CIs.
"""
import json
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from sklearn.metrics import roc_auc_score

plt.rcParams.update({"font.family": "serif", "font.size": 8.5, "pdf.fonttype": 42})

RESULTS = "/hdd1/jiangxi/AD-Agent/benchmark/results"

DOMAIN_MAP = {
    "D1":  ("D01", "Industrial"),
    "D2":  ("D02", "Retail"),
    "D4":  ("D03", "Infrastr."),
    "D5":  ("D04", "Dermo."),
    "D5b": ("D05", "Brain MRI"),
    "D5c": ("D06", "Liver CT"),
    "D5d": ("D07", "Endoscopy"),
    "D6":  ("D08", "ChangeDet."),
    "D7":  ("D09", "Road"),
    "D9":  ("D10", "Logical"),
    "D10": ("D11", "VisA"),
}


def load_agent_paired():
    d = json.load(open(f"{RESULTS}/seedvl_agent_v1_test.json"))
    subs = {x["item_id"]: float(x["anomaly_score"])
            for x in json.load(open(f"{RESULTS}/subspacead_test.json"))
            if x.get("anomaly_score") is not None}
    dv = {x["item_id"]: float(x["anomaly_score"])
          for x in json.load(open(f"{RESULTS}/classical_dinov2_patch_test_all.json"))
          if x.get("anomaly_score") is not None}
    per = defaultdict(lambda: {"y": [], "v0": [], "agent": [], "subs": [], "dv": []})
    for it in d:
        dc = it.get("domain_code")
        if dc not in DOMAIN_MAP:
            continue
        key = DOMAIN_MAP[dc][0]  # "D01" etc.
        y = int(it["label_gt"])
        per[key]["y"].append(y)
        per[key]["v0"].append(float((it.get("raw_output") or {}).get("v0_score",
                                                                      it["anomaly_score"])))
        per[key]["agent"].append(float(it["anomaly_score"]))
        per[key]["subs"].append(subs.get(it["item_id"], np.nan))
        per[key]["dv"].append(dv.get(it["item_id"], np.nan))
    return per


def per_domain_aurocs():
    per = load_agent_paired()
    rows = []
    for d_code, (d_label, _) in sorted(DOMAIN_MAP.items(),
                                         key=lambda x: x[1][0]):
        if d_label not in per:
            continue
        v = per[d_label]
        y = np.array(v["y"])
        if len(set(y)) < 2:
            continue
        v0 = np.array(v["v0"])
        ag = np.array(v["agent"])
        ss = np.nan_to_num(np.array(v["subs"]), nan=np.nanmedian(v["subs"]))
        dv = np.nan_to_num(np.array(v["dv"]), nan=np.nanmedian(v["dv"]))
        rows.append((d_label,
                     roc_auc_score(y, dv), roc_auc_score(y, ss),
                     roc_auc_score(y, v0), roc_auc_score(y, ag)))
    return rows


def main():
    rows = per_domain_aurocs()
    labels = [r[0] for r in rows]
    dinov2 = [r[1] for r in rows]
    subs = [r[2] for r in rows]
    v0 = [r[3] for r in rows]
    agent = [r[4] for r in rows]

    fig, ax = plt.subplots(figsize=(11.5, 3.2))
    x = np.arange(len(labels))
    w = 0.2
    ax.bar(x - 1.5 * w, dinov2, w, label="DINOv2-PatchNN", color="#718096",
           edgecolor="black", linewidth=0.3)
    ax.bar(x - 0.5 * w, subs,   w, label="SubspaceAD",      color="#4a90c2",
           edgecolor="black", linewidth=0.3)
    ax.bar(x + 0.5 * w, v0,     w, label="v0 Direct",        color="#b7791f",
           edgecolor="black", linewidth=0.3)
    ax.bar(x + 1.5 * w, agent,  w, label="AnomalyClaw",      color="#2c7a7b",
           edgecolor="black", linewidth=0.3)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel("AUROC", fontsize=9)
    ax.set_ylim(0.3, 1.02)
    ax.set_title("Per-domain AUROC on CrossDomainVAD-11 test split (SeedVL)",
                 fontsize=10)
    ax.legend(loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.28),
              frameon=True, fontsize=8.5)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    ax.axhline(0.5, color="#c53030", linewidth=0.5, linestyle="--", alpha=0.5)

    plt.tight_layout()
    out = "/hdd1/jiangxi/AD-Agent/paper/figures/fig_per_domain.pdf"
    plt.savefig(out, bbox_inches="tight")
    print(f"saved {out}")


if __name__ == "__main__":
    main()
