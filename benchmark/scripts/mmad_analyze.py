"""Analyze mmad_eval_v9 results: per-type accuracy, AD AUROC,
per-class threshold calibration.

Usage:
  python benchmark/scripts/mmad_analyze.py \
    --dev benchmark/results/mmad_v9_dev989.json \
    --test benchmark/results/mmad_v9_full.json \
    --out benchmark/results/mmad_v9_report.json
"""
from __future__ import annotations
import argparse
import json
from collections import defaultdict


def compute_per_type(results, field="agent_answer"):
    buckets = defaultdict(lambda: {"c": 0, "n": 0})
    for r in results:
        qt = r.get("question_type")
        gt = r.get("correct_answer")
        pred = r.get(field)
        if not gt or not pred:
            continue
        buckets[qt]["n"] += 1
        if pred == gt:
            buckets[qt]["c"] += 1
    return {qt: {"acc": v["c"] / v["n"], "n": v["n"]}
            for qt, v in buckets.items() if v["n"]}


def compute_auroc(ad_items, score_field="agent_score"):
    try:
        from sklearn.metrics import roc_auc_score
    except Exception:
        return None
    y = [int(r.get("label_gt", 0)) for r in ad_items]
    s = [float(r.get(score_field, 0.5) or 0.5) for r in ad_items]
    if len(set(y)) < 2:
        return None
    return float(roc_auc_score(y, s))


def yes_no_letters(options):
    yes_letter = no_letter = None
    for k, v in (options or {}).items():
        t = str(v).lower()
        if any(x in t for x in ("yes", "defect", "there is", "anomal")):
            yes_letter = k
        elif any(x in t for x in ("no ", "no,", "no defect", "not ", "normal")):
            no_letter = k
    return yes_letter or "A", no_letter or "B"


def fit_per_class_threshold(dev_results, score_field="ensemble_score"):
    """For AD subset, find per-class τ maximising MCQ accuracy on dev."""
    by_class = defaultdict(list)
    for r in dev_results:
        if r.get("question_type") != "Anomaly Detection":
            continue
        by_class[r.get("class_name")].append(r)

    thresholds = {}
    for cls, items in by_class.items():
        best_t, best_acc = 0.5, 0.0
        for t in [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45,
                  0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]:
            correct = 0
            total = 0
            for r in items:
                s = r.get(score_field)
                if s is None:
                    continue
                yes_l, no_l = yes_no_letters(r.get("options") or {})
                pred = yes_l if float(s) > t else no_l
                if pred == r.get("correct_answer"):
                    correct += 1
                total += 1
            if total == 0:
                continue
            acc = correct / total
            if acc > best_acc:
                best_acc = acc
                best_t = t
        thresholds[cls] = {"tau": best_t, "dev_acc": best_acc,
                           "n_dev": len(items)}
    # Global fallback
    all_items = [r for rs in by_class.values() for r in rs]
    global_best_t, global_best_acc = 0.5, 0.0
    for t in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        correct = total = 0
        for r in all_items:
            s = r.get(score_field)
            if s is None:
                continue
            yes_l, no_l = yes_no_letters(r.get("options") or {})
            pred = yes_l if float(s) > t else no_l
            if pred == r.get("correct_answer"):
                correct += 1
            total += 1
        acc = correct / total if total else 0
        if acc > global_best_acc:
            global_best_acc = acc
            global_best_t = t
    thresholds["_global"] = {"tau": global_best_t, "dev_acc": global_best_acc,
                             "n_dev": sum(len(r) for r in by_class.values())}
    return thresholds


def apply_thresholds(test_results, thresholds, score_field="ensemble_score"):
    """Map score → MCQ letter using per-class threshold."""
    out = []
    for r in test_results:
        r2 = dict(r)
        if r.get("question_type") != "Anomaly Detection":
            out.append(r2)
            continue
        s = r.get(score_field)
        if s is None:
            out.append(r2)
            continue
        cls = r.get("class_name")
        tau = thresholds.get(cls, thresholds["_global"])["tau"]
        yes_l, no_l = yes_no_letters(r.get("options") or {})
        r2[f"{score_field}_tuned_answer"] = yes_l if float(s) > tau else no_l
        out.append(r2)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", required=True)
    ap.add_argument("--test", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    dev = json.load(open(args.dev))
    print(f"=== DEV ({args.dev}) — {len(dev)} items ===")
    for field in ("direct_answer", "agent_answer", "ensemble_answer"):
        per = compute_per_type(dev, field)
        print(f"\n[{field}]")
        for qt, v in sorted(per.items()):
            print(f"  {qt:25s}  acc={100*v['acc']:5.2f}%  n={v['n']}")

    # AD AUROC on dev
    ad_dev = [r for r in dev if r.get("question_type") == "Anomaly Detection"]
    print(f"\n[AD AUROC on dev, n={len(ad_dev)}]")
    for f in ("direct_score", "agent_score", "ensemble_score"):
        auc = compute_auroc(ad_dev, f)
        if auc is not None:
            print(f"  {f:16s} AUROC={auc:.4f}")

    # Fit thresholds on dev
    print("\n[Per-class threshold calibration (ensemble_score)]")
    thresholds = fit_per_class_threshold(dev, "ensemble_score")
    print(f"  global τ={thresholds['_global']['tau']:.2f} "
          f"acc={100*thresholds['_global']['dev_acc']:.2f}% "
          f"(n={thresholds['_global']['n_dev']})")

    report = {"dev_per_type_agent": compute_per_type(dev, "agent_answer"),
              "dev_per_type_direct": compute_per_type(dev, "direct_answer"),
              "dev_per_type_ensemble": compute_per_type(dev, "ensemble_answer"),
              "dev_ad_auroc_direct": compute_auroc(ad_dev, "direct_score"),
              "dev_ad_auroc_agent": compute_auroc(ad_dev, "agent_score"),
              "dev_ad_auroc_ensemble": compute_auroc(ad_dev, "ensemble_score"),
              "thresholds": thresholds}

    if args.test:
        test = json.load(open(args.test))
        print(f"\n=== TEST ({args.test}) — {len(test)} items ===")
        for field in ("direct_answer", "agent_answer", "ensemble_answer"):
            per = compute_per_type(test, field)
            print(f"\n[{field}]")
            for qt, v in sorted(per.items()):
                print(f"  {qt:25s}  acc={100*v['acc']:5.2f}%  n={v['n']}")
        tuned = apply_thresholds(test, thresholds, "ensemble_score")
        per = compute_per_type(tuned, "ensemble_score_tuned_answer")
        print(f"\n[ensemble_score_tuned_answer (AD only)]")
        for qt, v in sorted(per.items()):
            print(f"  {qt:25s}  acc={100*v['acc']:5.2f}%  n={v['n']}")
        ad_test = [r for r in test
                   if r.get("question_type") == "Anomaly Detection"]
        print(f"\n[AD AUROC on test, n={len(ad_test)}]")
        for f in ("direct_score", "agent_score", "ensemble_score"):
            auc = compute_auroc(ad_test, f)
            if auc is not None:
                print(f"  {f:16s} AUROC={auc:.4f}")
        report["test_per_type_agent"] = compute_per_type(test, "agent_answer")
        report["test_per_type_direct"] = compute_per_type(test,
                                                          "direct_answer")
        report["test_per_type_ensemble"] = compute_per_type(
            test, "ensemble_answer")
        report["test_per_type_ensemble_tuned"] = compute_per_type(
            tuned, "ensemble_score_tuned_answer")
        report["test_ad_auroc_direct"] = compute_auroc(ad_test, "direct_score")
        report["test_ad_auroc_agent"] = compute_auroc(ad_test, "agent_score")
        report["test_ad_auroc_ensemble"] = compute_auroc(ad_test,
                                                         "ensemble_score")

    if args.out:
        with open(args.out, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
