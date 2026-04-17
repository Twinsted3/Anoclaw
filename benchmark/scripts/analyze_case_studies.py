"""Single-case analysis: pick K wins and K losses of agent vs direct,
show the agent's thought chain.

Usage:
  python benchmark/scripts/analyze_case_studies.py \
    --agent benchmark/results/v6_5_agent_qwen3_test.json \
    --direct benchmark/results/v6_direct_qwen3_test.json \
    --k 5 \
    --out refine-logs/case_studies_v6_5_qwen3.md
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True)
    ap.add_argument("--direct", required=True)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    a = {x["item_id"]: x for x in json.load(open(args.agent))}
    d = {x["item_id"]: x for x in json.load(open(args.direct))}
    common = sorted(set(a) & set(d))

    # Compute per-item prediction correctness at threshold 0.5
    records = []
    for iid in common:
        ax = a[iid]; dx = d[iid]
        if ax.get("label_gt") is None: continue
        y = int(ax["label_gt"])
        a_correct = (ax["anomaly_score"] > 0.5) == (y == 1)
        d_correct = (dx["anomaly_score"] > 0.5) == (y == 1)
        # Gain = agent_score wins over direct when label=1 (positive), or
        # loses when label=0 (negative). Use signed score advantage.
        if y == 1:
            advantage = ax["anomaly_score"] - dx["anomaly_score"]
        else:
            advantage = dx["anomaly_score"] - ax["anomaly_score"]
        records.append({"item_id": iid, "y": y, "a_correct": a_correct,
                        "d_correct": d_correct, "advantage": advantage,
                        "ax": ax, "dx": dx})

    wins = sorted([r for r in records if r["a_correct"] and not r["d_correct"]],
                   key=lambda r: -r["advantage"])[:args.k]
    losses = sorted([r for r in records if not r["a_correct"] and r["d_correct"]],
                    key=lambda r: -r["advantage"])[:args.k]

    lines = []
    lines.append(f"# Case studies: agent wins vs direct (top {args.k})\n\n")
    for r in wins:
        _fmt_case(lines, r, "WIN")
    lines.append(f"\n# Case studies: agent losses (top {args.k})\n\n")
    for r in losses:
        _fmt_case(lines, r, "LOSS")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        f.writelines(lines)
    print(f"Wrote {args.out}")


def _fmt_case(lines, r, tag):
    ax, dx = r["ax"], r["dx"]
    lines.append(f"## {tag}: {r['item_id']} (domain={ax.get('domain_code')},"
                 f" gt={r['y']})\n\n")
    lines.append(f"- **Direct**: score={dx.get('anomaly_score'):.3f} "
                 f"rationale={dx.get('raw_output', {}).get('evidence', '?')[:200]!r}\n")
    lines.append(f"- **Agent**: score={ax.get('anomaly_score'):.3f} "
                 f"rationale={(ax.get('rationale') or '')[:200]!r}\n")
    lines.append(f"  turns={ax.get('n_turns')} "
                 f"tools={ax.get('tools_used')} confidence={ax.get('confidence')}\n")
    lines.append(f"  advantage_score: {r['advantage']:+.3f}\n\n")


if __name__ == "__main__":
    main()
