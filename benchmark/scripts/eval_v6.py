"""v6 evaluation: macro AUROC + per-domain + bootstrap 95% CI + paired permutation.

Usage:
  python benchmark/scripts/eval_v6.py \
    --results benchmark/results/v6_agent_qwen3_test.json \
    --compare_to benchmark/results/v6_fusion_qwen3_test.json \
    --out_json refine-logs/v6_eval_qwen3.json
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score


def _load(path: str) -> list:
    data = json.load(open(path))
    if isinstance(data, dict):
        data = list(data.values())
    return data


def macro_auroc(items: list) -> dict:
    by = defaultdict(lambda: ([], []))
    for x in items:
        y = x.get("label_gt")
        s = x.get("anomaly_score")
        d = x.get("domain_code")
        if y is None or s is None or d is None:
            continue
        by[d][0].append(float(s))
        by[d][1].append(int(y))
    per_domain = {}
    for d, (s, y) in by.items():
        if len(set(y)) >= 2:
            per_domain[d] = float(roc_auc_score(y, s))
    macro = float(np.mean(list(per_domain.values()))) if per_domain else 0.0
    return {"macro": macro, "per_domain": per_domain,
            "n_domains": len(per_domain),
            "n_items": sum(len(s) for s, _ in by.values())}


def bootstrap_ci_per_domain(items: list, n_boot: int = 1000,
                            seed: int = 42, alpha: float = 0.05) -> dict:
    rng = np.random.RandomState(seed)
    by = defaultdict(lambda: ([], []))
    for x in items:
        y, s, d = x.get("label_gt"), x.get("anomaly_score"), x.get("domain_code")
        if y is None or s is None or d is None:
            continue
        by[d][0].append(float(s))
        by[d][1].append(int(y))
    ci = {}
    for d, (s, y) in by.items():
        s, y = np.array(s), np.array(y)
        if len(set(y)) < 2:
            continue
        boots = []
        for _ in range(n_boot):
            idx = rng.randint(0, len(y), len(y))
            yb, sb = y[idx], s[idx]
            if len(set(yb)) < 2:
                continue
            boots.append(roc_auc_score(yb, sb))
        if boots:
            lo = float(np.percentile(boots, 100 * alpha / 2))
            hi = float(np.percentile(boots, 100 * (1 - alpha / 2)))
            ci[d] = [lo, hi]
    return ci


def bootstrap_macro_ci(items: list, n_boot: int = 1000,
                       seed: int = 42, alpha: float = 0.05) -> list:
    """Bootstrap macro AUROC: resample items within each domain, compute macro."""
    rng = np.random.RandomState(seed)
    by = defaultdict(lambda: ([], []))
    for x in items:
        y, s, d = x.get("label_gt"), x.get("anomaly_score"), x.get("domain_code")
        if y is None or s is None or d is None:
            continue
        by[d][0].append(float(s))
        by[d][1].append(int(y))
    macros = []
    for _ in range(n_boot):
        aucs = []
        for d, (s, y) in by.items():
            if len(set(y)) < 2:
                continue
            s, y = np.array(s), np.array(y)
            idx = rng.randint(0, len(y), len(y))
            yb, sb = y[idx], s[idx]
            if len(set(yb)) >= 2:
                aucs.append(roc_auc_score(yb, sb))
        if aucs:
            macros.append(float(np.mean(aucs)))
    if not macros:
        return [0.0, 0.0]
    return [float(np.percentile(macros, 100 * alpha / 2)),
            float(np.percentile(macros, 100 * (1 - alpha / 2)))]


def paired_permutation_test(a_items: list, b_items: list,
                            n_perm: int = 10000, seed: int = 42) -> dict:
    rng = np.random.RandomState(seed)
    a_by = {x["item_id"]: x for x in a_items}
    b_by = {x["item_id"]: x for x in b_items}
    common = sorted(set(a_by) & set(b_by))
    per_dom = defaultdict(lambda: {"a": [], "b": [], "y": []})
    for iid in common:
        a, b = a_by[iid], b_by[iid]
        y = a.get("label_gt")
        d = a.get("domain_code")
        if y is None or d is None:
            continue
        per_dom[d]["a"].append(float(a["anomaly_score"]))
        per_dom[d]["b"].append(float(b["anomaly_score"]))
        per_dom[d]["y"].append(int(y))

    def macro_of(which: str) -> float:
        aucs = []
        for d, dd in per_dom.items():
            y = np.array(dd["y"])
            s = np.array(dd[which])
            if len(set(y)) >= 2:
                aucs.append(roc_auc_score(y, s))
        return float(np.mean(aucs)) if aucs else 0.0

    observed = macro_of("a") - macro_of("b")

    null_deltas = []
    for _ in range(n_perm):
        perm_macros_a, perm_macros_b = [], []
        for d, dd in per_dom.items():
            a = np.array(dd["a"]); b = np.array(dd["b"]); y = np.array(dd["y"])
            swap = rng.rand(len(a)) < 0.5
            a2 = np.where(swap, b, a)
            b2 = np.where(swap, a, b)
            if len(set(y)) >= 2:
                perm_macros_a.append(roc_auc_score(y, a2))
                perm_macros_b.append(roc_auc_score(y, b2))
        if perm_macros_a:
            null_deltas.append(float(np.mean(perm_macros_a)
                                     - np.mean(perm_macros_b)))
    null = np.array(null_deltas)
    p = float((np.abs(null) >= abs(observed)).mean()) if len(null) else 1.0
    return {"delta": float(observed), "p_value": p,
            "n_items_common": len(common), "n_permutations": n_perm}


def tool_usage_stats(items: list) -> dict:
    """Aggregate tools_used + n_turns + confidence stats from an agent output."""
    from collections import Counter
    turns, tools, n_single = [], Counter(), 0
    for x in items:
        if x.get("n_turns") is None:
            continue
        turns.append(int(x["n_turns"]))
        for t in x.get("tools_used") or []:
            tools[t] += 1
        if x.get("n_turns", 0) == 1 and not x.get("tools_used"):
            n_single += 1
    return {
        "n": len(items),
        "avg_turns": float(np.mean(turns)) if turns else None,
        "median_turns": float(np.median(turns)) if turns else None,
        "pct_single_turn_no_tool": (n_single / len(items) * 100) if items else 0,
        "tool_call_counts": dict(tools),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--compare_to", default=None)
    ap.add_argument("--out_json", required=True)
    ap.add_argument("--n_boot", type=int, default=1000)
    ap.add_argument("--n_perm", type=int, default=10000)
    args = ap.parse_args()

    items_a = _load(args.results)
    report = {
        "system_a": args.results,
        "macro_auroc": macro_auroc(items_a),
        "macro_bootstrap_ci_95": bootstrap_macro_ci(items_a, n_boot=args.n_boot),
        "per_domain_ci_95": bootstrap_ci_per_domain(items_a, n_boot=args.n_boot),
        "tool_usage": tool_usage_stats(items_a),
    }
    if args.compare_to:
        items_b = _load(args.compare_to)
        report["system_b"] = args.compare_to
        report["macro_auroc_b"] = macro_auroc(items_b)
        report["paired_permutation_a_minus_b"] = paired_permutation_test(
            items_a, items_b, n_perm=args.n_perm)

    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_json, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
