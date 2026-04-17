"""Expert × Strategy ablation matrix.

For each domain, compute AUROC of:
  - Direct VLM alone
  - Direct + fusion w=0.2 with each expert (subspacead, anomalyvfm,
    patchknn, dinov2_global)
  - Each expert alone
  - Direct + fusion w=0.5 (equal weight)
  - Direct + max(direct, expert)  (conservative OR)
  - Direct + min(direct, expert)  (conservative AND)

This lets us see: which expert helps which domain, what's the optimal
fusion weight, and how much headroom a "perfect per-domain expert choice"
would give.

Usage:
  python benchmark/scripts/expert_strategy_matrix.py \
    --direct benchmark/results/v6_direct_qwen3_test.json \
    --out refine-logs/expert_strategy_qwen3.md
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score


def _load(p):
    d = json.load(open(p))
    if isinstance(d, dict):
        d = list(d.values())
    return {x["item_id"]: x for x in d if "item_id" in x}


def _sigmoid(se, median):
    return 1.0 / (1.0 + np.exp(-2.0 * (se - median) / max(median, 1e-6)))


def _auroc_by_domain(items):
    by = defaultdict(lambda: ([], []))
    for x in items:
        y, s, d = x.get("label_gt"), x.get("anomaly_score"), x.get("domain_code")
        if y is None or s is None or d is None:
            continue
        by[d][0].append(float(s)); by[d][1].append(int(y))
    per = {}
    for d, (s, y) in by.items():
        if len(set(y)) >= 2:
            per[d] = roc_auc_score(y, s)
    macro = float(np.mean(list(per.values()))) if per else 0.0
    return per, macro


def _build_fused(direct_by, expert_by, median_calib, alpha, mode="linear"):
    out = []
    for iid, dx in direct_by.items():
        dv = dx.get("anomaly_score")
        if dv is None: continue
        ex = expert_by.get(iid)
        if ex and ex.get("anomaly_score") is not None:
            sig = _sigmoid(float(ex["anomaly_score"]), median_calib)
            if mode == "linear":
                s = (1 - alpha) * float(dv) + alpha * sig
            elif mode == "max":
                s = max(float(dv), sig)
            elif mode == "min":
                s = min(float(dv), sig)
            else:
                raise ValueError(mode)
        else:
            s = float(dv)
        out.append({"item_id": iid, "domain_code": dx.get("domain_code"),
                    "label_gt": dx.get("label_gt"), "anomaly_score": s})
    return out


def _expert_only(expert_test_path, manifest_path):
    raw = json.load(open(expert_test_path))
    if isinstance(raw, list):
        recs = {x["item_id"]: x for x in raw if "item_id" in x}
    else:
        recs = raw
    m = json.load(open(manifest_path))
    m_by = {x["item_id"]: x for x in m if x.get("split") == "test"}
    out = []
    for iid, rec in recs.items():
        if iid not in m_by: continue
        s = rec.get("anomaly_score")
        if s is None: continue
        out.append({"item_id": iid, "domain_code": m_by[iid].get("domain_code"),
                    "label_gt": m_by[iid].get("label"),
                    "anomaly_score": float(s)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--direct", required=True)
    ap.add_argument("--manifest", default="benchmark/manifests/full_manifest.json")
    ap.add_argument("--results_dir", default="benchmark/results")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    direct_by = _load(args.direct)

    # Load expert caches
    experts = {}
    EX_FILES = {
        "subspacead":    ("subspacead_calibration.json", "subspacead_test.json"),
        "anomalyvfm":    ("anomalyvfm_calibration.json", "anomalyvfm_test.json"),
        "patchknn":      ("classical_dinov2_patch_test_all.json", "classical_dinov2_patch_test_all.json"),
        "dinov2_global": ("classical_dinov2_global_test_all.json", "classical_dinov2_global_test_all.json"),
    }
    for name, (calib_f, test_f) in EX_FILES.items():
        test_path = Path(args.results_dir) / test_f
        calib_path = Path(args.results_dir) / calib_f
        if not test_path.exists():
            continue
        calib = json.load(open(calib_path))
        if isinstance(calib, list):
            calib_scores = [float(x["anomaly_score"]) for x in calib
                            if x.get("anomaly_score") is not None]
        else:
            calib_scores = [float(v["anomaly_score"]) for v in calib.values()
                            if v.get("anomaly_score") is not None]
        median = float(np.median(calib_scores)) if calib_scores else 1.0
        # Load test expert by item_id
        test_raw = json.load(open(test_path))
        if isinstance(test_raw, list):
            test_by = {x["item_id"]: x for x in test_raw if "item_id" in x}
        else:
            test_by = test_raw
        experts[name] = (test_by, median)

    # Direct alone
    per, macro = _auroc_by_domain(list(direct_by.values()))
    rows = {"Direct VLM": {"macro": macro, "per": per}}

    # Expert-only
    for name, (test_by, _med) in experts.items():
        recs = [{"item_id": iid, "domain_code": direct_by.get(iid, {}).get("domain_code"),
                 "label_gt": direct_by.get(iid, {}).get("label_gt"),
                 "anomaly_score": v.get("anomaly_score")}
                for iid, v in test_by.items()
                if v.get("anomaly_score") is not None]
        per, macro = _auroc_by_domain(recs)
        rows[f"{name} alone"] = {"macro": macro, "per": per}

    # Direct + fusion with each expert at multiple weights
    for name, (test_by, med) in experts.items():
        for alpha in [0.1, 0.2, 0.3, 0.5, 0.8]:
            fused = _build_fused(direct_by, test_by, med, alpha, "linear")
            per, macro = _auroc_by_domain(fused)
            rows[f"Direct + {name} α={alpha}"] = {"macro": macro, "per": per}
        # max/min variants at alpha=0.5 (not applicable; mode overrides)
        for mode in ("max", "min"):
            fused = _build_fused(direct_by, test_by, med, 0.5, mode)
            per, macro = _auroc_by_domain(fused)
            rows[f"Direct ⊕{mode}⊕ {name}"] = {"macro": macro, "per": per}

    # Oracle: per-domain best row
    all_domains = sorted({d for r in rows.values() for d in r["per"]})
    oracle_per = {}
    oracle_row_by_dom = {}
    for d in all_domains:
        best_name = max(rows, key=lambda n: rows[n]["per"].get(d, 0))
        oracle_per[d] = rows[best_name]["per"].get(d, 0)
        oracle_row_by_dom[d] = best_name
    oracle_macro = float(np.mean(list(oracle_per.values())))

    # Render
    lines = []
    lines.append(f"# Expert × Strategy Matrix\n")
    lines.append(f"- Direct: `{args.direct}`\n")
    lines.append(f"- Output: `{args.out}`\n\n")

    # Main table
    lines.append(f"## Macro AUROC by system\n\n")
    lines.append("| System | Macro |\n|--------|------|\n")
    for n in sorted(rows, key=lambda x: -rows[x]["macro"]):
        lines.append(f"| {n} | {rows[n]['macro']:.4f} |\n")
    lines.append(f"| **ORACLE (per-domain best row)** | **{oracle_macro:.4f}** |\n\n")

    # Per-domain best fusion
    lines.append(f"## Oracle per-domain choice (upper bound)\n\n")
    lines.append("| Domain | Best system | AUROC |\n|--------|-------------|-------|\n")
    for d in all_domains:
        lines.append(f"| {d} | {oracle_row_by_dom[d]} | {oracle_per[d]:.4f} |\n")
    lines.append("\n")

    # Per-domain matrix (selected columns)
    selected = ["Direct VLM"] + [f"Direct + {n} α=0.2"
                                 for n in experts if f"Direct + {n} α=0.2" in rows]
    lines.append(f"## Per-domain AUROC matrix (selected)\n\n")
    header = "| domain |" + "|".join(f" {s[:14]} " for s in selected) + "|\n"
    lines.append(header)
    lines.append("|" + "--|" * (len(selected) + 1) + "\n")
    for d in all_domains:
        row = [d]
        for s in selected:
            row.append(f"{rows[s]['per'].get(d, 0):.3f}")
        lines.append("| " + " | ".join(row) + " |\n")
    lines.append("\n")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        f.writelines(lines)
    print(f"Wrote {args.out}")
    print(f"\nHighlights:")
    print(f"  Direct VLM:       {rows['Direct VLM']['macro']:.4f}")
    for n in sorted(rows, key=lambda x: -rows[x]["macro"])[:5]:
        print(f"  {n}: {rows[n]['macro']:.4f}")
    print(f"  ORACLE upper bound: {oracle_macro:.4f}")


if __name__ == "__main__":
    main()
