"""
Evaluate inference results and compute benchmark metrics.

Usage:
  python benchmark/scripts/evaluate.py \
      --results benchmark/results/seedvl_v1_calibration.json \
      --output benchmark/results/seedvl_v1_calibration_metrics.json

Metrics:
  - Balanced Accuracy (BA)
  - AUROC
  - Macro-F1
  - per-domain breakdown
  - cost per 100 images
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    roc_auc_score,
    balanced_accuracy_score,
    f1_score,
    confusion_matrix,
)
from scipy import stats as scipy_stats


def bootstrap_ci(metric_fn, y_true, y_score_or_pred, n=1000, ci=0.95):
    """Bootstrap 95% CI for a metric function."""
    scores = []
    rng = np.random.default_rng(42)
    n_samples = len(y_true)
    for _ in range(n):
        idx = rng.integers(0, n_samples, n_samples)
        try:
            s = metric_fn(np.array(y_true)[idx], np.array(y_score_or_pred)[idx])
            scores.append(s)
        except Exception:
            pass
    if not scores:
        return None, None
    alpha = (1 - ci) / 2
    return float(np.quantile(scores, alpha)), float(np.quantile(scores, 1 - alpha))


def compute_metrics(items, threshold=0.5):
    y_true = [x["label_gt"] for x in items]
    y_score = [x["anomaly_score"] for x in items]
    y_pred = [x["label_pred"] for x in items]

    if len(set(y_true)) < 2:
        return {"note": "only one class present"}

    auroc = float(roc_auc_score(y_true, y_score))
    ba = float(balanced_accuracy_score(y_true, y_pred))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    f1_macro = float(f1_score(y_true, y_pred, average="macro", zero_division=0))

    cm = confusion_matrix(y_true, y_pred).tolist()
    n_items = len(items)
    total_tokens_in = sum((x.get("cost_tokens") or {}).get("input", 0) for x in items)
    total_tokens_out = sum((x.get("cost_tokens") or {}).get("output", 0) for x in items)
    total_latency = sum(x.get("latency_sec", 0) or 0 for x in items)
    n_errors = sum(1 for x in items if x.get("error"))

    # Bootstrap CIs
    auroc_lo, auroc_hi = bootstrap_ci(roc_auc_score, y_true, y_score)
    ba_lo, ba_hi = bootstrap_ci(balanced_accuracy_score, y_true, y_pred)

    return {
        "n_items": n_items,
        "n_errors": n_errors,
        "auroc": auroc,
        "auroc_ci": [auroc_lo, auroc_hi],
        "balanced_accuracy": ba,
        "ba_ci": [ba_lo, ba_hi],
        "f1_binary": f1,
        "f1_macro": f1_macro,
        "confusion_matrix": cm,
        "cost_tokens_in_per_100": round(total_tokens_in / n_items * 100, 0),
        "cost_tokens_out_per_100": round(total_tokens_out / n_items * 100, 0),
        "avg_latency_sec": round(total_latency / max(n_items, 1), 2),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()

    with open(args.results) as f:
        results = json.load(f)

    # Filter out items with errors
    valid = [x for x in results if x.get("error") is None
             and x.get("label_gt") is not None
             and x.get("anomaly_score") is not None]
    print(f"Valid items: {len(valid)}/{len(results)}")

    # Overall metrics
    overall = compute_metrics(valid, args.threshold)

    # Per-domain metrics
    by_domain = defaultdict(list)
    for x in valid:
        by_domain[x["domain_code"]].append(x)

    domain_metrics = {}
    for code, items in sorted(by_domain.items()):
        domain_metrics[code] = {
            "domain": items[0]["domain"],
            "n": len(items),
            **compute_metrics(items, args.threshold),
        }

    # Per-split metrics
    by_split = defaultdict(list)
    for x in valid:
        by_split[x.get("split", "unknown")].append(x)
    split_metrics = {s: compute_metrics(items, args.threshold)
                     for s, items in by_split.items()}

    # Macro-average across domains (equal weight)
    domain_aurocs = [v["auroc"] for v in domain_metrics.values() if "auroc" in v]
    domain_bas = [v["balanced_accuracy"] for v in domain_metrics.values()
                  if "balanced_accuracy" in v]

    output = {
        "overall": overall,
        "macro_avg_auroc": float(np.mean(domain_aurocs)) if domain_aurocs else None,
        "macro_avg_ba": float(np.mean(domain_bas)) if domain_bas else None,
        "per_domain": domain_metrics,
        "per_split": split_metrics,
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    # Print summary (robust to string/None values when all items errored out)
    def _fmt(v, d=4):
        if isinstance(v, (int, float)):
            return f"{v:.{d}f}"
        return str(v)

    print(f"\n=== Evaluation Summary ===")
    auroc_ci = overall.get('auroc_ci') or [None, None]
    print(f"  Overall AUROC:             {_fmt(overall.get('auroc', 'N/A'))} "
          f"[{_fmt(auroc_ci[0], 3)}, {_fmt(auroc_ci[1], 3)}]")
    print(f"  Overall Balanced Accuracy: {_fmt(overall.get('balanced_accuracy', 'N/A'))}")
    print(f"  Overall Macro-F1:          {_fmt(overall.get('f1_macro', 'N/A'))}")
    if output.get('macro_avg_auroc') is not None:
        print(f"  Macro-avg AUROC (domains): {_fmt(output['macro_avg_auroc'])}")
    print(f"\n  Per-Domain AUROC:")
    for code, m in domain_metrics.items():
        print(f"    {code} ({m['domain']:20s}): {_fmt(m.get('auroc', 'N/A'))}  "
              f"BA={_fmt(m.get('balanced_accuracy', 'N/A'))}  n={m['n']}")
    print(f"\n  Saved: {args.output}")


if __name__ == "__main__":
    main()
