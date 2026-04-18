"""Per-item flip analysis: find the cases where a tool FLIPPED Direct's
prediction from wrong to right (or significantly improved it). Characterize
these cases so an agent prompt can be told when to call the tool.

Output per tool:
  - n_wins  (items where tool score was clearly closer to truth than Direct)
  - n_losses (items where tool score was clearly farther from truth)
  - n_flips_to_correct (FP→correct + FN→correct)
  - n_flips_to_wrong  (correct→FP + correct→FN)
  - Characterization of WIN items:
      * domain distribution
      * subspacead_rank distribution (observable AFTER expert_score call)
      * direct score distribution (external; NOT observable to agent but
        useful diagnostic)
      * agent_rationale keyword extraction (top words in wins vs losses)

A tool is WORTH KEEPING if:
  - n_flips_to_correct > n_flips_to_wrong (Net positive flips)
  - AND there is an identifiable visual/semantic pattern in WIN items
    that doesn't appear in LOSS items (extractable trigger)

Usage:
  python benchmark/scripts/analyze_tool_flips.py \
    --direct benchmark/results/v6_direct_qwen3_dev.json \
    --out_md refine-logs/FLIP_ANALYSIS_dev.md
"""
from __future__ import annotations
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


AUDIT_DIR = Path("benchmark/results/tool_audit")
STOPWORDS = set(
    "the a an and or but if of in on at to for with by is are was were "
    "be been being have has had this that these those it its as so "
    "which what who how when where why do does did not no yes can could "
    "would should may might must shall will from than then some such "
    "however more most less least much many very only also just quite "
    "rather still yet thus hence therefore while whereas whose whom they "
    "them their theirs we us our ours you your yours i me my mine he she "
    "him her his hers into onto over under above below between among "
    "both either neither any all each every other others another "
    "there here near beside because however since although though "
    "image images reference references query normal anomaly anomalous "
    "shows show appears appear seen observed consistent indicate indicates "
    "indicating suggesting suggest suggests suggests "
    "score rank expert tool similar value based information strong weak "
    "potential unclear conclusion conclude overall "
    "present presenting likely clearly definite definitely possible "
    "region regions area areas feature features pattern patterns "
    "pixel pixels mean max min threshold small large big high low "
    "light dark color colors texture textures background foreground "
    "however suggests 0 1 2 3 4 5 6 7 8 9".split()
)


def tokenize(text: str) -> list[str]:
    if not text:
        return []
    text = re.sub(r"[^a-zA-Z\s]", " ", text.lower())
    tokens = [t for t in text.split() if len(t) > 2 and t not in STOPWORDS]
    return tokens


def classify_item(label: float, direct_score: float, tool_score: float,
                  threshold: float = 0.1, decision_thresh: float = 0.5) -> str:
    """Return one of:
       'flip_to_correct': direct wrong, tool right (crossed 0.5)
       'flip_to_wrong'  : direct right, tool wrong
       'improved'       : same side but tool closer to truth by threshold
       'worsened'       : same side but tool farther by threshold
       'neutral'        : no significant change
    """
    direct_right = (label == 1 and direct_score >= decision_thresh) or \
                   (label == 0 and direct_score < decision_thresh)
    tool_right = (label == 1 and tool_score >= decision_thresh) or \
                 (label == 0 and tool_score < decision_thresh)
    direct_err = abs(direct_score - label)
    tool_err = abs(tool_score - label)
    if direct_right and not tool_right:
        return "flip_to_wrong"
    if not direct_right and tool_right:
        return "flip_to_correct"
    if tool_err < direct_err - threshold:
        return "improved"
    if tool_err > direct_err + threshold:
        return "worsened"
    return "neutral"


def _load_expert_rank_map():
    try:
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
    except Exception:
        return {}


def analyze_tool(tool_file: Path, direct_by_id: dict, rank_map: dict):
    rows = json.load(open(tool_file))
    tool = tool_file.stem
    wins, losses, neutrals = [], [], []
    for r in rows:
        label = r.get("label_gt")
        if label is None or r.get("error"):
            continue
        d = direct_by_id.get(r["item_id"])
        if not d:
            continue
        tool_score = r.get("anomaly_score", 0.5)
        direct_score = d.get("anomaly_score", 0.5)
        cls = classify_item(label, direct_score, tool_score)
        item = {
            "item_id": r["item_id"],
            "domain": r.get("domain_code"),
            "label": int(label),
            "direct_score": direct_score,
            "tool_score": tool_score,
            "used_tool": bool(r.get("used_tool")),
            "class": cls,
            "rationale": (r.get("rationale") or ""),
            "rank": rank_map.get(r["item_id"], 0.5),
        }
        if cls in ("flip_to_correct", "improved"):
            wins.append(item)
        elif cls in ("flip_to_wrong", "worsened"):
            losses.append(item)
        else:
            neutrals.append(item)

    return {
        "tool": tool,
        "n_total": len(rows),
        "n_wins": len(wins),
        "n_losses": len(losses),
        "n_neutral": len(neutrals),
        "flips_to_correct": sum(1 for w in wins if w["class"] == "flip_to_correct"),
        "flips_to_wrong": sum(1 for l in losses if l["class"] == "flip_to_wrong"),
        "wins": wins,
        "losses": losses,
    }


def summarize_distribution(items: list[dict], rank_map: dict) -> dict:
    """Characterize a set of items: domain dist, label dist, rank dist,
    direct-confidence dist, and top keywords from rationales."""
    doms = Counter(i["domain"] for i in items)
    labels = Counter(i["label"] for i in items)
    ranks_at_hi = sum(1 for i in items if i["rank"] >= 0.7)
    ranks_at_lo = sum(1 for i in items if i["rank"] <= 0.3)
    ranks_mid = len(items) - ranks_at_hi - ranks_at_lo
    direct_mid = sum(1 for i in items if abs(i["direct_score"] - 0.5) < 0.15)
    direct_conf = sum(1 for i in items if abs(i["direct_score"] - 0.5) >= 0.3)
    tool_used = sum(1 for i in items if i["used_tool"])
    kw = Counter()
    for i in items:
        for t in tokenize(i["rationale"]):
            kw[t] += 1
    return {
        "n": len(items),
        "domains": doms.most_common(),
        "labels": labels.most_common(),
        "rank_hi": ranks_at_hi,
        "rank_lo": ranks_at_lo,
        "rank_mid": ranks_mid,
        "direct_mid": direct_mid,
        "direct_conf": direct_conf,
        "tool_used": tool_used,
        "top_keywords": kw.most_common(20),
    }


def keyword_diff(win_kw: list, loss_kw: list, min_count: int = 3) -> list:
    """Return words much more common in wins than losses (proxy for trigger)."""
    w = dict(win_kw)
    l = dict(loss_kw)
    diffs = []
    for word, w_count in w.items():
        if w_count < min_count:
            continue
        l_count = l.get(word, 0)
        # log-odds-ish: rank by w_count - l_count, tie-break by ratio
        score = (w_count - l_count) / max(1, w_count + l_count)
        if score > 0.3:  # clearly more common in wins
            diffs.append((word, w_count, l_count, score))
    diffs.sort(key=lambda x: -x[3])
    return diffs[:15]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--direct", default="benchmark/results/v6_direct_qwen3_dev.json")
    ap.add_argument("--audit_dir", default="benchmark/results/tool_audit")
    ap.add_argument("--out_md", default="refine-logs/FLIP_ANALYSIS_dev.md")
    args = ap.parse_args()

    direct = json.load(open(args.direct))
    direct_by_id = {x["item_id"]: x for x in direct}
    rank_map = _load_expert_rank_map()

    audit_files = sorted(Path(args.audit_dir).glob("*.json"))
    results = []
    for f in audit_files:
        try:
            r = analyze_tool(f, direct_by_id, rank_map)
            results.append(r)
        except Exception as e:
            print(f"[warn] {f}: {e}")

    lines: list[str] = [
        f"# Per-Item Flip Analysis — dev n={len(direct)}",
        "",
        "## Headline: do any tools have exploitable per-item gains?",
        "",
        "| tool | flips→correct | flips→wrong | net_flips | n_wins (flips+improved) | n_losses | win/loss |",
        "|---|---|---|---|---|---|---|",
    ]
    results.sort(key=lambda x: -(x["flips_to_correct"] - x["flips_to_wrong"]))
    for r in results:
        net = r["flips_to_correct"] - r["flips_to_wrong"]
        ratio = r["n_wins"] / max(1, r["n_losses"])
        lines.append(
            f"| {r['tool']} | {r['flips_to_correct']} | "
            f"{r['flips_to_wrong']} | {net:+d} | "
            f"{r['n_wins']} | {r['n_losses']} | {ratio:.2f} |"
        )
    lines.append("")

    lines += [
        "## Per-tool trigger analysis",
        "",
        "For each tool, comparing WIN items vs LOSS items reveals whether a",
        "distinguishable pattern exists that could be injected as a trigger",
        "hint in the agent prompt.",
        "",
    ]

    for r in results:
        win_sum = summarize_distribution(r["wins"], rank_map)
        loss_sum = summarize_distribution(r["losses"], rank_map)
        diffs = keyword_diff(win_sum["top_keywords"], loss_sum["top_keywords"])
        net = r["flips_to_correct"] - r["flips_to_wrong"]

        lines += [
            f"### {r['tool']}  (net flips {net:+d}, wins {r['n_wins']}, losses {r['n_losses']})",
            "",
            f"**Win items** (n={win_sum['n']}): "
            f"domains={dict(win_sum['domains'][:6])}; "
            f"label_pos_rate={win_sum['labels']}; "
            f"rank(hi/mid/lo)={win_sum['rank_hi']}/{win_sum['rank_mid']}/{win_sum['rank_lo']}; "
            f"direct_mid(uncertain)={win_sum['direct_mid']}; "
            f"direct_conf(extreme)={win_sum['direct_conf']}; "
            f"tool_used={win_sum['tool_used']}/{win_sum['n']}",
            "",
            f"**Loss items** (n={loss_sum['n']}): "
            f"domains={dict(loss_sum['domains'][:6])}; "
            f"label_pos_rate={loss_sum['labels']}; "
            f"rank(hi/mid/lo)={loss_sum['rank_hi']}/{loss_sum['rank_mid']}/{loss_sum['rank_lo']}; "
            f"direct_mid(uncertain)={loss_sum['direct_mid']}; "
            f"direct_conf(extreme)={loss_sum['direct_conf']}; "
            f"tool_used={loss_sum['tool_used']}/{loss_sum['n']}",
            "",
        ]
        if diffs:
            lines.append("**Keywords distinctive in WIN rationales** (word: n_wins n_losses score):")
            lines.append("")
            for w, wc, lc, s in diffs:
                lines.append(f"- `{w}`: wins={wc} losses={lc} score={s:+.2f}")
            lines.append("")
        else:
            lines.append("**No distinctive keyword pattern in WIN vs LOSS rationales.**")
            lines.append("")

        # Top-5 sample wins for manual inspection
        if r["wins"]:
            lines.append("**Sample WIN items (tool flipped correctly):**")
            lines.append("")
            samples = [w for w in r["wins"] if w["class"] == "flip_to_correct"][:5]
            for s in samples:
                lines.append(f"- `{s['item_id']}` [{s['domain']}] label={s['label']} "
                             f"direct={s['direct_score']:.2f}→tool={s['tool_score']:.2f}  "
                             f"rank={s['rank']:.2f}  used_tool={s['used_tool']}")
                lines.append(f"  > {s['rationale'][:200]}")
            lines.append("")
        if r["losses"]:
            lines.append("**Sample LOSS items (tool flipped wrong):**")
            lines.append("")
            samples = [l for l in r["losses"] if l["class"] == "flip_to_wrong"][:5]
            for s in samples:
                lines.append(f"- `{s['item_id']}` [{s['domain']}] label={s['label']} "
                             f"direct={s['direct_score']:.2f}→tool={s['tool_score']:.2f}  "
                             f"rank={s['rank']:.2f}  used_tool={s['used_tool']}")
                lines.append(f"  > {s['rationale'][:200]}")
            lines.append("")

    Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_md, "w") as f:
        f.write("\n".join(lines))
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
