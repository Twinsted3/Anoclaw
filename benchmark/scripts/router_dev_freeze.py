"""Dev-frozen per-domain router (codex's suggested experiment #5).

Protocol:
  1. Compute per-domain macro AUROC of Direct vs. each agent variant on DEV.
  2. For each domain, choose the system with the HIGHER dev AUROC.
  3. Apply the chosen system to TEST items in that domain.
  4. Report test macro AUROC — one number, no further iteration.

This is a PURE agent composition (each item's score comes from exactly
one system, no averaging). The routing is learned from dev only.

Usage:
  python benchmark/scripts/router_dev_freeze.py \
    --dev_direct benchmark/results/v6_direct_qwen3_dev.json \
    --dev_agents benchmark/results/v6_5_agent_qwen3_dev.json ... \
    --test_direct benchmark/results/v6_direct_qwen3_test.json \
    --test_agents benchmark/results/v6_5_agent_qwen3_test.json ... \
    --out benchmark/results/router_dev_frozen_qwen3_test.json \
    --min_margin 0.0  # positive margin required for agent to be picked
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from sklearn.metrics import roc_auc_score


def _load(p):
    d = json.load(open(p))
    if isinstance(d, dict):
        d = list(d.values())
    return {x["item_id"]: x for x in d if "item_id" in x}


def _per_dom_auroc(items):
    by = defaultdict(lambda: ([], []))
    for x in items.values():
        y, s, d = x.get("label_gt"), x.get("anomaly_score"), x.get("domain_code")
        if y is None or s is None or d is None:
            continue
        by[d][0].append(float(s)); by[d][1].append(int(y))
    out = {}
    for d, (s, y) in by.items():
        if len(set(y)) >= 2:
            out[d] = float(roc_auc_score(y, s))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev_direct", required=True)
    ap.add_argument("--dev_agents", nargs="+", required=True,
                    help="one or more agent result JSONs on dev split")
    ap.add_argument("--test_direct", required=True)
    ap.add_argument("--test_agents", nargs="+", required=True,
                    help="matching agent result JSONs on test split "
                         "(same count as --dev_agents, in same order)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--min_margin", type=float, default=0.0,
                    help="minimum dev-AUROC advantage agent must have over "
                         "direct to be selected for that domain")
    args = ap.parse_args()

    if len(args.dev_agents) != len(args.test_agents):
        raise ValueError("--dev_agents and --test_agents must have same count")

    dev_direct = _load(args.dev_direct)
    dev_agents = [_load(p) for p in args.dev_agents]
    test_direct = _load(args.test_direct)
    test_agents = [_load(p) for p in args.test_agents]

    per_dom_direct = _per_dom_auroc(dev_direct)
    per_dom_agents = [_per_dom_auroc(a) for a in dev_agents]

    # For each domain, pick the best system (direct or agent_i)
    all_doms = sorted({d for d in per_dom_direct}
                      | {d for p in per_dom_agents for d in p})
    choice = {}
    for d in all_doms:
        scores = [("direct", per_dom_direct.get(d, 0.0))]
        for i, p in enumerate(per_dom_agents):
            name = Path(args.dev_agents[i]).stem
            scores.append((name, p.get(d, 0.0)))
        scores.sort(key=lambda x: -x[1])
        best_name, best_auc = scores[0]
        direct_auc = per_dom_direct.get(d, 0.0)
        # Require agent to beat direct by at least min_margin
        if best_name != "direct" and (best_auc - direct_auc) < args.min_margin:
            best_name = "direct"
        choice[d] = {"system": best_name, "dev_auc": best_auc,
                     "direct_dev_auc": direct_auc,
                     "candidates": scores}

    # Apply to test
    system_idx = {Path(p).stem: i for i, p in enumerate(args.dev_agents)}
    out_items = []
    for iid, item in test_direct.items():
        dom = item.get("domain_code")
        if dom is None:
            continue
        ch = choice.get(dom, {"system": "direct"})
        sys_name = ch["system"]
        if sys_name == "direct":
            src = item
        else:
            idx = system_idx[sys_name]
            src = test_agents[idx].get(iid)
            if src is None or src.get("error") is not None \
               or src.get("anomaly_score") is None:
                src = item  # fallback
                sys_name = "direct_fallback"
        out_items.append({
            **{k: item.get(k) for k in ("item_id", "domain_code", "label_gt")},
            "anomaly_score": src.get("anomaly_score"),
            "routed_to": sys_name,
        })

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out_items, f)

    # Report
    print(f"Wrote {len(out_items)} items → {args.out}\n")
    print("Per-domain choice (dev-frozen):")
    for d in all_doms:
        ch = choice[d]
        cand_str = "  ".join(f"{n}={auc:.3f}" for n, auc in ch["candidates"])
        print(f"  {d}: {ch['system']:30s}  ({cand_str})")
    print()

    # Macro AUROC on test
    from eval_v6 import macro_auroc
    m = macro_auroc(out_items)
    print(f"TEST MACRO AUROC: {m['macro']:.4f}  (n={m['n_items']}, "
          f"domains={m['n_domains']})")
    print()
    # Compare to direct on test
    m_d = macro_auroc(list(test_direct.values()))
    print(f"Direct baseline macro:  {m_d['macro']:.4f}")
    print(f"Dev-frozen router macro: {m['macro']:.4f}  "
          f"(Δ={m['macro']-m_d['macro']:+.4f})")


if __name__ == "__main__":
    main()
