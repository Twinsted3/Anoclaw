"""compose_ensemble.py — produce the ensemble score from cached results.

Usage:
  python benchmark/scripts/compose_ensemble.py \
    --direct benchmark/results/v6_direct_qwen3_test.json \
    --agent  benchmark/results/v6_5_agent_qwen3_test.json \
    --output benchmark/results/v6_ensemble_qwen3_test.json \
    --alpha 0.5

Output is a standard result JSON whose `anomaly_score` is:
    alpha * direct + (1 - alpha) * agent
indexed by item_id. Items missing from one side fall back to the other.

This is the "integrated" ensemble from the user's perspective: a single
command that takes the two independent system outputs and composes the
best-performing combination.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load(path: str) -> dict:
    data = json.load(open(path))
    if isinstance(data, dict):
        data = list(data.values())
    return {x["item_id"]: x for x in data if "item_id" in x}


def _valid_score(x):
    """A score counts only if the record has no error AND has a score."""
    if not x:
        return None
    if x.get("error"):
        return None
    s = x.get("anomaly_score")
    return float(s) if s is not None else None


def compose(direct_path: str, agent_path: str, alpha: float = 0.5) -> list:
    d_by = _load(direct_path)
    a_by = _load(agent_path)
    out = []
    for iid in sorted(set(d_by) | set(a_by)):
        dx, ax = d_by.get(iid), a_by.get(iid)
        d_score = _valid_score(dx)
        a_score = _valid_score(ax)
        if d_score is not None and a_score is not None:
            score = alpha * d_score + (1 - alpha) * a_score
            source = "ensemble"
        elif d_score is not None:
            score = d_score
            source = ("direct_only_agent_errored"
                      if ax and ax.get("error") else "direct_only")
        elif a_score is not None:
            score = a_score
            source = ("agent_only_direct_errored"
                      if dx and dx.get("error") else "agent_only")
        else:
            continue
        base = ax if ax else dx
        out.append({
            **{k: base.get(k) for k in ("item_id", "domain_code", "label_gt")},
            "anomaly_score": score,
            "direct_score": d_score,
            "agent_score": a_score,
            "alpha": alpha,
            "source": source,
            "n_turns": base.get("n_turns"),
            "tools_used": base.get("tools_used"),
            "rationale": base.get("rationale"),
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--direct", required=True)
    ap.add_argument("--agent", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--alpha", type=float, default=0.5,
                    help="weight on direct (0..1); default 0.5")
    args = ap.parse_args()

    out = compose(args.direct, args.agent, args.alpha)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(out, f)
    print(f"Wrote {len(out)} ensemble results → {args.output}")
    # Quick macro
    try:
        import sys as _s
        _s.path.insert(0, str(Path(__file__).parent))
        from eval_v6 import macro_auroc
        m = macro_auroc(out)
        print(f"Macro AUROC = {m['macro']:.4f}  (n={m['n_items']}, "
              f"domains={m['n_domains']})")
    except Exception as e:
        print(f"(macro eval skipped: {e})")


if __name__ == "__main__":
    main()
