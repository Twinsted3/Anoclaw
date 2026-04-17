"""Tool-usage and effect analysis on an agent result file.

Outputs per-tool:
  - call count + coverage (% items that called it at least once)
  - AUROC of items that DID use the tool vs DIDN'T (on same items-pool subset)
  - avg turns when this tool was used
  - per-domain distribution

Compares agent score vs Direct-on-same-items for each tool subset, i.e.,
"when tool X was called, does agent beat Direct on those items?"

Usage:
  python benchmark/scripts/analyze_tool_effects.py \
    --agent benchmark/results/v6_5_agent_qwen3_test.json \
    --direct benchmark/results/v6_direct_qwen3_test.json \
    --out refine-logs/tool_effects_qwen3_v6_5.md
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score


def _load(p):
    d = json.load(open(p))
    if isinstance(d, dict):
        d = list(d.values())
    return {x["item_id"]: x for x in d if "item_id" in x}


def _macro(items):
    by = defaultdict(lambda: ([], []))
    for x in items:
        y, s, d = x.get("label_gt"), x.get("anomaly_score"), x.get("domain_code")
        if y is None or s is None or d is None:
            continue
        by[d][0].append(float(s)); by[d][1].append(int(y))
    aurocs = []
    for d, (s, y) in by.items():
        if len(set(y)) >= 2:
            aurocs.append(roc_auc_score(y, s))
    return float(np.mean(aurocs)) if aurocs else 0.0, len(aurocs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True)
    ap.add_argument("--direct", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    a_by = _load(args.agent)
    d_by = _load(args.direct)

    # Tool-wise stats
    all_tools = Counter()
    all_calls = Counter()
    tool_to_items = defaultdict(list)  # tool_name -> list of agent items that used it
    turns_hist = Counter()
    per_domain_tool = defaultdict(lambda: Counter())
    n_no_tool = 0
    for iid, x in a_by.items():
        tools = x.get("tools_used") or []
        turns_hist[x.get("n_turns", 0)] += 1
        if not tools:
            n_no_tool += 1
        for t in tools:
            all_calls[t] += 1
        for t in set(tools):
            all_tools[t] += 1
            tool_to_items[t].append(iid)
            per_domain_tool[x.get("domain_code")][t] += 1

    total_items = len(a_by)

    # Overall macros
    a_items = list(a_by.values())
    d_items = [d_by[i] for i in a_by if i in d_by]
    a_macro, nd_a = _macro(a_items)
    d_macro, nd_d = _macro(d_items)

    # Build report
    lines = []
    lines.append(f"# Tool Usage and Effect Analysis\n")
    lines.append(f"- **Agent results**: `{args.agent}` (n={total_items})\n")
    lines.append(f"- **Direct baseline**: `{args.direct}` (n={len(d_by)})\n")
    lines.append(f"- **Agent macro AUROC**: {a_macro:.4f}  "
                 f"(across {nd_a} domains)\n")
    lines.append(f"- **Direct macro AUROC**: {d_macro:.4f}\n")
    lines.append(f"- **Items with 0 tool calls**: {n_no_tool}/{total_items} "
                 f"({100*n_no_tool/total_items:.1f}%)\n\n")

    # Turns histogram
    lines.append("## Turn-count distribution\n\n")
    lines.append("| turns | count | pct |\n|---|---|---|\n")
    for t in sorted(turns_hist):
        n = turns_hist[t]
        lines.append(f"| {t} | {n} | {100*n/total_items:.1f}% |\n")
    lines.append("\n")

    # Per-tool effect
    lines.append("## Per-tool usage and effect\n\n")
    lines.append("Macro AUROC on items WHERE the tool was called, comparing "
                 "agent vs Direct on those same items. Δ = agent - direct "
                 "(positive = tool helped).\n\n")
    lines.append("| tool | #items | cov% | call_count | agent AUROC | direct AUROC | Δ |\n")
    lines.append("|------|--------|------|-----------|-------------|--------------|---|\n")
    for t, n in sorted(all_tools.items(), key=lambda x: -x[1]):
        sub_ids = tool_to_items[t]
        sub_agent = [a_by[i] for i in sub_ids]
        sub_direct = [d_by[i] for i in sub_ids if i in d_by]
        if not sub_direct:
            continue
        am, _ = _macro(sub_agent)
        dm, _ = _macro(sub_direct)
        delta = am - dm
        lines.append(f"| {t} | {n} | {100*n/total_items:.1f}% | "
                     f"{all_calls[t]} | {am:.4f} | {dm:.4f} | "
                     f"{delta:+.4f} |\n")
    lines.append("\n")

    # Subset that used NO tool: agent vs direct
    no_tool_ids = [iid for iid, x in a_by.items() if not (x.get("tools_used") or [])]
    sub_agent = [a_by[i] for i in no_tool_ids]
    sub_direct = [d_by[i] for i in no_tool_ids if i in d_by]
    if sub_direct:
        am, _ = _macro(sub_agent); dm, _ = _macro(sub_direct)
        lines.append(f"### Subset: NO tool called (n={len(no_tool_ids)})\n\n")
        lines.append(f"- agent AUROC: {am:.4f}\n")
        lines.append(f"- direct AUROC: {dm:.4f}\n")
        lines.append(f"- Δ = {am-dm:+.4f}\n\n")

    # Per-domain tool usage
    lines.append("## Per-domain tool usage (count of items using tool)\n\n")
    domains = sorted({x.get("domain_code") for x in a_by.values() if x.get("domain_code")})
    tools = sorted(all_tools)
    lines.append("| domain |" + "|".join(f" {t[5:]} " for t in tools) + "| no_tool |\n")
    lines.append("|" + "--|" * (len(tools) + 2) + "\n")
    for d in domains:
        d_n = sum(1 for x in a_by.values() if x.get("domain_code") == d)
        row = [f"{d} (n={d_n})"]
        for t in tools:
            row.append(str(per_domain_tool[d].get(t, 0)))
        n_notool = sum(1 for x in a_by.values()
                       if x.get("domain_code") == d and not (x.get("tools_used") or []))
        row.append(f"{n_notool}")
        lines.append("| " + " | ".join(row) + " |\n")
    lines.append("\n")

    # Save
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        f.writelines(lines)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
