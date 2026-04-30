"""
Aggregate per-domain AUROC for the new baselines (AnomalyDINO,
VisualAD, AD-Copilot) and emit a LaTeX-ready row block for Table 1.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score


DOMAINS = ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "D11", "D12"]


def per_domain_auroc(result_dir):
    out = {}
    for d in DOMAINS:
        f = Path(result_dir) / f"{d}.json"
        if not f.exists() or f.stat().st_size < 1000:
            out[d] = None
            continue
        r = json.load(open(f))
        ok = [x for x in r if x.get("error") is None and x.get("anomaly_score") is not None]
        if len(ok) < 5:
            out[d] = None
            continue
        y = [x["label"] for x in ok]
        s = [x["anomaly_score"] for x in ok]
        if len(set(y)) < 2:
            out[d] = None
            continue
        out[d] = round(float(roc_auc_score(y, s)), 4)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/hdd1/jiangxi/AD-Agent/benchmark/results/baselines")
    args = ap.parse_args()

    rows = {}
    for name in ["anomalydino", "visualad", "ad_copilot", "ad_copilot_4shot",
                 "iad_r1", "qwen25vl_base_4shot", "qwen25vl_base_1shot"]:
        d = Path(args.root) / name
        if d.exists():
            rows[name] = per_domain_auroc(d)
        else:
            rows[name] = {x: None for x in DOMAINS}

    print("=== Per-domain AUROC (test split, manifests_v2) ===")
    print(f"{'method':12s}|" + "|".join(f"{d:>6}" for d in DOMAINS) + "| Macro")
    for name, per in rows.items():
        cells = []
        vals = []
        for d in DOMAINS:
            v = per.get(d)
            if v is None:
                cells.append("  N/A ")
            else:
                cells.append(f"{v:.4f}"[:6])
                vals.append(v)
        macro = round(float(np.mean(vals)), 4) if vals else None
        print(f"{name:12s}|" + "|".join(f"{c:>6}" for c in cells) + f"| {macro}")

    print("\n=== LaTeX rows (paste into 4_experiments.tex) ===")
    pretty = {
        "anomalydino": "AnomalyDINO~\\citep{damm2025anomalydino}",
        "visualad":    "VisualAD~\\citep{hou2026visualad}",
        "ad_copilot":  "AD-Copilot~\\citep{jiang2026adcopilot}",
        "ad_copilot_4shot": "AD-Copilot~\\citep{jiang2026adcopilot} (4-shot)",
        "iad_r1": "IAD-R1~\\citep{li2025iadr1}",
        "qwen25vl_base_4shot": "Qwen2.5-VL-7B (base, 4-shot)",
        "qwen25vl_base_1shot": "Qwen2.5-VL-7B (base, 1-shot)",
    }
    for name in ["anomalydino", "visualad", "ad_copilot", "ad_copilot_4shot",
                 "iad_r1", "qwen25vl_base_4shot", "qwen25vl_base_1shot"]:
        per = rows[name]
        macro_vals = [per[d] for d in DOMAINS if per[d] is not None]
        macro = round(float(np.mean(macro_vals)), 3) if macro_vals else None
        cells = []
        for d in DOMAINS:
            v = per[d]
            cells.append(f"{v:.3f}" if v is not None else "\\tbd")
        line = f"\\hspace{{1mm}}{pretty[name]:42s}& " + " & ".join(cells)
        line += f" & {macro:.3f} \\\\" if macro is not None else " & \\tbd \\\\"
        print(line)


if __name__ == "__main__":
    main()
