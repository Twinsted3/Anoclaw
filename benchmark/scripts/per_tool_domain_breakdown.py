"""Per-tool per-domain sample analysis.

For every tool, break down wins and losses by domain. For each (tool, domain)
pair, list specific items and characterize the SAMPLE TYPE (is it a FP
correction for a normal-with-unusual-look, an FN correction for a subtle
anomaly, ...). Output is detailed enough that the agent prompt can cite
per-domain usage rules.

Output: refine-logs/PER_TOOL_DOMAIN_dev.md — long, browsable file.
"""
from __future__ import annotations
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np


def classify_flip(label, direct, tool, thresh=0.1):
    d_right = (label == 1 and direct >= 0.5) or (label == 0 and direct < 0.5)
    t_right = (label == 1 and tool >= 0.5) or (label == 0 and tool < 0.5)
    d_err, t_err = abs(direct - label), abs(tool - label)
    if d_right and not t_right:
        return "flip_to_wrong"
    if not d_right and t_right:
        return "flip_to_correct"
    if t_err < d_err - thresh:
        return "improved"
    if t_err > d_err + thresh:
        return "worsened"
    return "neutral"


def sample_type(label, direct, tool):
    """Categorize the item for characterization of the correction type."""
    if label == 0 and direct >= 0.7 and tool < 0.5:
        return "FP_corrected"      # direct wrongly said anom on a normal
    if label == 1 and direct <= 0.3 and tool >= 0.5:
        return "FN_corrected"      # direct wrongly said normal on an anom
    if label == 1 and direct >= 0.7 and tool < 0.5:
        return "TP_lost_to_FN"     # direct was right, tool broke it
    if label == 0 and direct <= 0.3 and tool >= 0.5:
        return "TN_lost_to_FP"     # direct was right, tool broke it
    return "other"


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--direct",
                    default="benchmark/results/v6_direct_qwen3_dev.json")
    ap.add_argument("--audit_dir",
                    default="benchmark/results/tool_audit")
    ap.add_argument("--out_md",
                    default="refine-logs/PER_TOOL_DOMAIN_dev.md")
    args = ap.parse_args()

    direct = json.load(open(args.direct))
    direct_by_id = {x["item_id"]: x for x in direct}
    rank_map = _load_rank()

    audit_files = sorted(Path(args.audit_dir).glob("*.json"))

    lines: list[str] = [
        "# Per-Tool × Per-Domain Sample Analysis — dev n=480",
        "",
        "For each tool, the WIN items (tool flipped to correct or improved "
        "the score) and LOSS items (tool broke correct or worsened) are "
        "listed by domain, with the specific item IDs and rationale snippets.",
        "",
        "Sample types:",
        "- `FP_corrected`: Direct said anomaly on a normal; tool brought down",
        "- `FN_corrected`: Direct missed an anomaly; tool brought up",
        "- `TP_lost_to_FN`: Direct correctly flagged anomaly; tool wrongly dismissed",
        "- `TN_lost_to_FP`: Direct correctly said normal; tool wrongly flagged",
        "",
    ]

    for f in audit_files:
        tool = f.stem
        rows = json.load(open(f))

        by_domain: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
        n_total = 0
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
            sample_t = sample_type(label, direct_score, tool_score)
            rank = rank_map.get(r["item_id"], 0.5)
            domain = r.get("domain_code", "UNK")
            by_domain[domain][flip].append({
                "item_id": r["item_id"],
                "label": int(label),
                "direct": direct_score,
                "tool": tool_score,
                "rank": rank,
                "sample_t": sample_t,
                "used_tool": bool(r.get("used_tool")),
                "rationale": (r.get("rationale") or "")[:220],
            })
            n_total += 1

        total_wins = sum(len(v.get("flip_to_correct", [])) + len(v.get("improved", []))
                         for v in by_domain.values())
        total_losses = sum(len(v.get("flip_to_wrong", [])) + len(v.get("worsened", []))
                           for v in by_domain.values())
        net_flips = (sum(len(v.get("flip_to_correct", [])) for v in by_domain.values())
                     - sum(len(v.get("flip_to_wrong", [])) for v in by_domain.values()))
        lines += [
            f"## {tool}  ({total_wins} wins, {total_losses} losses, net flips {net_flips:+d} on n={n_total})",
            "",
        ]

        for dom in sorted(by_domain.keys()):
            cats = by_domain[dom]
            wins = cats.get("flip_to_correct", []) + cats.get("improved", [])
            losses = cats.get("flip_to_wrong", []) + cats.get("worsened", [])
            if not wins and not losses:
                continue
            # Count sample types
            from collections import Counter
            win_types = Counter(w["sample_t"] for w in wins)
            loss_types = Counter(l["sample_t"] for l in losses)

            lines += [
                f"### {dom}  (wins {len(wins)}, losses {len(losses)})",
                "",
                f"Win sample-types: {dict(win_types)}",
                f"Loss sample-types: {dict(loss_types)}",
                "",
            ]

            if wins:
                lines.append("**WINS** (item · direct→tool · rank · type · rationale):")
                lines.append("")
                # Sort by most valuable wins first (flip_to_correct > improved)
                wins.sort(key=lambda x: (x["sample_t"] != "FP_corrected"
                                         and x["sample_t"] != "FN_corrected",
                                         -abs(x["direct"] - x["tool"])))
                for w in wins[:8]:
                    lines.append(
                        f"- `{w['item_id']}` L={w['label']} "
                        f"direct={w['direct']:.2f}→tool={w['tool']:.2f} "
                        f"rank={w['rank']:.2f} **{w['sample_t']}** "
                        f"used_tool={w['used_tool']}"
                    )
                    lines.append(f"  > {w['rationale']}")
                if len(wins) > 8:
                    lines.append(f"  ... and {len(wins)-8} more wins.")
                lines.append("")

            if losses:
                lines.append("**LOSSES**:")
                lines.append("")
                losses.sort(key=lambda x: (x["sample_t"] != "TP_lost_to_FN"
                                           and x["sample_t"] != "TN_lost_to_FP",
                                           -abs(x["direct"] - x["tool"])))
                for l in losses[:8]:
                    lines.append(
                        f"- `{l['item_id']}` L={l['label']} "
                        f"direct={l['direct']:.2f}→tool={l['tool']:.2f} "
                        f"rank={l['rank']:.2f} **{l['sample_t']}** "
                        f"used_tool={l['used_tool']}"
                    )
                    lines.append(f"  > {l['rationale']}")
                if len(losses) > 8:
                    lines.append(f"  ... and {len(losses)-8} more losses.")
                lines.append("")

            # Simple rule proposal
            rule_direction = None
            if len(wins) >= 3 and len(wins) > 2 * len(losses):
                # strong net-positive domain
                if any(w["sample_t"] == "FP_corrected" for w in wins):
                    ranks = [w["rank"] for w in wins if w["sample_t"] == "FP_corrected"]
                    if ranks:
                        lines.append(f"→ RULE candidate: on {dom}, tool tends to "
                                     f"correctly down-weight FPs when subspacead "
                                     f"rank ∈ [{min(ranks):.2f}, {max(ranks):.2f}].")
                        lines.append("")

        lines.append("---")
        lines.append("")

    Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_md, "w") as f:
        f.write("\n".join(lines))
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
