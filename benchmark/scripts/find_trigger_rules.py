"""Cross-tool rule discovery: for each tool audit, partition items by
(subspacead_rank quantile, direct_confidence quantile) and compute
per-cell net_flips. A cell with many positive net-flips across tools is
an exploitable niche.

Observable fields for the agent:
  - subspacead rank (after calling tool_expert_score(subspacead))
  - its own self-confidence on turn 1 (proxy for direct)

We compute:
  (a) For each tool: 3x3 grid of net_flips vs Direct
  (b) Across tools: which cells consistently show POSITIVE net_flips
  (c) Item-level candidates: items where multiple tools agree on correct flip
"""
from __future__ import annotations
import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


def classify_flip(label, direct_score, tool_score, thresh=0.1):
    direct_right = (label == 1 and direct_score >= 0.5) or \
                   (label == 0 and direct_score < 0.5)
    tool_right = (label == 1 and tool_score >= 0.5) or \
                 (label == 0 and tool_score < 0.5)
    d_err, t_err = abs(direct_score - label), abs(tool_score - label)
    if direct_right and not tool_right:
        return -2  # flip to wrong
    if not direct_right and tool_right:
        return +2  # flip to correct
    if t_err < d_err - thresh:
        return +1  # improved
    if t_err > d_err + thresh:
        return -1  # worsened
    return 0


def _load_rank():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from agent_tools_v7 import _load_expert_scores
    recs, scores = _load_expert_scores("subspacead", "dev")
    if len(scores) == 0:
        return {}
    return {iid: float(np.searchsorted(scores, float(rec["anomaly_score"]))
                       / len(scores))
            for iid, rec in recs.items()
            if rec.get("anomaly_score") is not None}


def rank_bucket(r):
    if r <= 0.4:
        return "lo"
    if r < 0.8:
        return "md"
    return "hi"


def direct_bucket(d):
    # Use raw Direct score, not margin — Direct is bimodal and virtually never
    # lands in uncertain zone, so margin-based buckets collapse to a single
    # "confident" column. Raw score + rank lets us see conflict cells
    # (rank and direct disagree).
    if d < 0.3:
        return "dir_normal"  # Direct thinks NORMAL
    if d < 0.7:
        return "dir_mid"
    return "dir_anom"  # Direct thinks ANOMALY


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--direct",
                    default="benchmark/results/v6_direct_qwen3_dev.json")
    ap.add_argument("--audit_dir",
                    default="benchmark/results/tool_audit")
    ap.add_argument("--out_md",
                    default="refine-logs/TRIGGER_RULES_dev.md")
    args = ap.parse_args()

    direct = json.load(open(args.direct))
    direct_by_id = {x["item_id"]: x for x in direct}
    rank_map = _load_rank()

    # per-tool: cell → list of flip values
    per_tool: dict = {}
    # cross-tool: item_id → list of (tool, flip_value) entries
    item_tools: dict = defaultdict(list)

    audit_files = sorted(Path(args.audit_dir).glob("*.json"))
    for f in audit_files:
        tool = f.stem
        rows = json.load(open(f))
        cell_flips = defaultdict(list)
        for r in rows:
            label = r.get("label_gt")
            if label is None or r.get("error"):
                continue
            d = direct_by_id.get(r["item_id"])
            if not d:
                continue
            tool_score = r.get("anomaly_score", 0.5)
            direct_score = d["anomaly_score"]
            flip = classify_flip(label, direct_score, tool_score)
            rank = rank_map.get(r["item_id"], 0.5)
            cell = (rank_bucket(rank), direct_bucket(direct_score))
            cell_flips[cell].append(flip)
            item_tools[r["item_id"]].append((tool, flip, label,
                                             direct_score, tool_score,
                                             rank, r.get("domain_code")))
        per_tool[tool] = cell_flips

    # --- Per-tool cell grids ---
    lines: list[str] = [
        f"# Trigger Rule Discovery — dev n={len(direct)}",
        "",
        "## Setup",
        "",
        "Each item is placed in a (rank × direct_confidence) cell:",
        "- rank: subspacead normalized rank (lo ≤0.4, md 0.4-0.8, hi ≥0.8)",
        "- direct_confidence: |direct_score - 0.5| (uncertain <0.15, moderate 0.15-0.30, confident ≥0.30)",
        "",
        "Flip values: +2=flip→correct, +1=improved, 0=neutral, -1=worsened, -2=flip→wrong.",
        "Cell **net_flips = sum of flip values**. Positive net = tool net-helps in that cell.",
        "",
        "## Per-tool cell grids (net_flips, n_items)",
        "",
    ]

    ranks = ["lo", "md", "hi"]
    confs = ["dir_normal", "dir_mid", "dir_anom"]
    for tool, cells in per_tool.items():
        lines.append(f"### {tool}")
        lines.append("")
        lines.append("| rank\\direct | uncertain | moderate | confident |")
        lines.append("|---|---|---|---|")
        for r in ranks:
            row = [f"rank={r}"]
            for c in confs:
                vals = cells.get((r, c), [])
                net = sum(vals)
                n = len(vals)
                if n == 0:
                    row.append("—")
                else:
                    row.append(f"{net:+d} (n={n})")
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")

    # --- Cross-tool cell agreement ---
    lines += [
        "## Cross-tool cell summary",
        "",
        "Averaged net_flips per cell across all tools. "
        "A consistently positive cell → robust trigger.",
        "",
        "| rank\\direct | uncertain | moderate | confident |",
        "|---|---|---|---|",
    ]
    for r in ranks:
        row = [f"rank={r}"]
        for c in confs:
            all_nets = [sum(per_tool[t].get((r, c), [])) for t in per_tool]
            all_ns = [len(per_tool[t].get((r, c), [])) for t in per_tool]
            if sum(all_ns) == 0:
                row.append("—")
            else:
                avg_net = np.mean(all_nets)
                avg_n = np.mean(all_ns)
                pos = sum(1 for x in all_nets if x > 0)
                row.append(f"avg_net={avg_net:+.1f} (n̄={avg_n:.0f}, {pos}/{len(all_nets)} tools +)")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    # --- Items where most tools help ---
    lines += [
        "## Items where ≥7 tools correctly flipped (robust exploitable items)",
        "",
        "These items are candidates that any tool (with disconfirm clause) "
        "reliably corrects — suggests the effect is PROMPT-driven, not "
        "tool-specific.",
        "",
    ]
    strong_items = []
    for iid, entries in item_tools.items():
        pos = sum(1 for (_, f, *_rest) in entries if f >= 1)
        neg = sum(1 for (_, f, *_rest) in entries if f <= -1)
        if pos >= 7:
            e0 = entries[0]
            strong_items.append({
                "item_id": iid,
                "label": e0[2],
                "direct": e0[3],
                "rank": e0[5],
                "domain": e0[6],
                "n_tools_pos": pos,
                "n_tools_neg": neg,
            })
    strong_items.sort(key=lambda x: -x["n_tools_pos"])
    lines.append(f"Found {len(strong_items)} such items.")
    lines.append("")
    if strong_items:
        lines.append("| item_id | domain | label | direct | rank | +tools | -tools |")
        lines.append("|---|---|---|---|---|---|---|")
        for s in strong_items[:40]:
            lines.append(f"| {s['item_id']} | {s['domain']} | {s['label']} "
                         f"| {s['direct']:.2f} | {s['rank']:.2f} "
                         f"| {s['n_tools_pos']} | {s['n_tools_neg']} |")
    lines.append("")

    # Cross-tool items where most tools HURT
    hurt_items = []
    for iid, entries in item_tools.items():
        neg = sum(1 for (_, f, *_rest) in entries if f <= -1)
        pos = sum(1 for (_, f, *_rest) in entries if f >= 1)
        if neg >= 7:
            e0 = entries[0]
            hurt_items.append({
                "item_id": iid,
                "label": e0[2],
                "direct": e0[3],
                "rank": e0[5],
                "domain": e0[6],
                "n_tools_neg": neg,
                "n_tools_pos": pos,
            })
    hurt_items.sort(key=lambda x: -x["n_tools_neg"])
    lines += [
        "## Items where ≥7 tools wrongly flipped (universal LOSS items)",
        "",
        f"Found {len(hurt_items)} such items.",
        "",
    ]
    if hurt_items:
        lines.append("| item_id | domain | label | direct | rank | -tools | +tools |")
        lines.append("|---|---|---|---|---|---|---|")
        for s in hurt_items[:40]:
            lines.append(f"| {s['item_id']} | {s['domain']} | {s['label']} "
                         f"| {s['direct']:.2f} | {s['rank']:.2f} "
                         f"| {s['n_tools_neg']} | {s['n_tools_pos']} |")
    lines.append("")

    # --- Actionable trigger proposal ---
    lines += [
        "## Proposed trigger rule (for agent prompt injection)",
        "",
        "If robust cells exist (avg_net>0 AND majority of tools +), synthesize "
        "an agent rule: 'When you observe rank∈X and your current score is in "
        "direct_conf∈Y, apply disconfirm-style reconsideration.'",
        "",
    ]

    Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_md, "w") as f:
        f.write("\n".join(lines))
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
