"""Verbalized Controller Learning v4 — disagreement-based meta-rules + RAG.

Pipeline (per domain):
  Stage A  run-passive-dev
      Run agent_v11 with learning_enabled=False on dev (== v10). Collects
      per-item (v9_score, v9_rationale, direct_score, direct_rationale, gt).

  Stage B  build-meta
      Partition dev items into four buckets:
        agree_correct, agree_wrong, disagree_a_wins, disagree_b_wins
      (by GT label and each branch's sign relative to 0.5). Balanced subset
      (up to K/2 a_wins + K/2 b_wins) fed to a VLM reflector that SEES the
      image + refs + both rationales + GT and writes 1–3 routing rules per
      side. agree_* buckets are not used (per user directive: no fallback
      rules for both-miss cases).

  Stage C  build-stack
      Merge per-domain meta-rules with existing v3_l1 invariants and v3_l2
      corrective (FN / FP) rules into a single flat rule store. Each rule
      has (type, category_or_null, text, source_items, confidence).

  Stage D  retrieve_rules_v4 (used at inference by agent_v11)
      RAG retrieval by (domain, category): filters rules whose category
      matches the item's category (or is domain-wide / null), ranks by
      priority (meta > invariant > corrective), returns top-K formatted.

The v3 L1/L2 artifacts under benchmark/results/verbalized/v3_l1 and
benchmark/results/verbalized/v3_l2 are reused verbatim as the "domain"
layer; they do not need regeneration.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from infer import (  # noqa: E402
    call_llm, extract_json, get_client, get_model_name,
    img_msg, load_and_encode, text_msg,
)
from verbalized_v3 import compose_anchor, load_domain_config  # noqa: E402

DOMAIN_CODES = [f"D{i}" for i in range(1, 13)]

DEFAULT_DEV_DIR = "benchmark/results/verbalized/v11_passive_dev"
DEFAULT_META_DIR = "benchmark/results/verbalized/v4_meta"
DEFAULT_STACK_DIR = "benchmark/results/verbalized/v4_rulebook"
DEFAULT_L1_DIR = "benchmark/results/verbalized/v3_l1"
DEFAULT_L2_DIR = "benchmark/results/verbalized/v3_l2"
DEFAULT_MANIFESTS = "benchmark/manifests_v2"


# ---------------------------------------------------------------------------
# Disagreement partition
# ---------------------------------------------------------------------------

def _binarize(score, threshold=0.5):
    if score is None:
        return None
    return 1 if score >= threshold else 0


def partition_dev(dev_results, manifest_items):
    """Group dev results by (agree, disagree_a_wins, disagree_b_wins).

    `dev_results` is the JSON list written by agent_v11 (learning_enabled=False).
    Each record has v9_score, direct_score, label_gt, rationale, item_id.
    `manifest_items` is a dict {item_id: manifest_row} for looking up refs etc.

    Returns dict of lists, each list element carries everything the reflector
    needs: (item_id, category, query_path, ref_paths, v9_score, v9_rationale,
    direct_score, direct_rationale, gt).
    """
    buckets = {
        "agree_correct": [],
        "agree_wrong": [],
        "disagree_a_wins": [],  # Agent correct, Direct wrong
        "disagree_b_wins": [],  # Direct correct, Agent wrong
        "skipped": [],
    }
    for r in dev_results:
        if r.get("error") and r.get("v9_score") is None:
            buckets["skipped"].append(r.get("item_id"))
            continue
        if r.get("mode") != "anomaly_detection":
            buckets["skipped"].append(r.get("item_id"))
            continue

        v9s = r.get("v9_score")
        d_s = r.get("direct_score")
        gt = r.get("label_gt")
        if v9s is None or d_s is None or gt is None:
            buckets["skipped"].append(r.get("item_id"))
            continue

        v9p = _binarize(v9s)
        dp = _binarize(d_s)
        gt_bin = int(gt)

        mrow = manifest_items.get(r["item_id"]) or {}
        # Direct rationale string from raw_output if available; passive v11
        # currently reports blend so we reconstruct from direct_score alone.
        direct_rationale = r.get("direct_rationale") or ""
        enriched = {
            "item_id": r["item_id"],
            "category": mrow.get("category"),
            "query_path": mrow.get("query_path"),
            "ref_paths": (mrow.get("ref_paths") or [])[:2],
            "v9_score": float(v9s),
            "v9_rationale": (r.get("rationale") or "")[:600],
            "direct_score": float(d_s),
            "direct_rationale": direct_rationale[:600],
            "gt": gt_bin,
        }

        v9_correct = (v9p == gt_bin)
        d_correct = (dp == gt_bin)

        if v9p == dp:
            buckets["agree_correct" if v9_correct else "agree_wrong"].append(enriched)
        else:
            if v9_correct:
                buckets["disagree_a_wins"].append(enriched)
            else:
                buckets["disagree_b_wins"].append(enriched)
    return buckets


def balanced_sample(a_wins, b_wins, k=10):
    """Deterministically sample K/2 a_wins + K/2 b_wins.

    Sorted by item_id for reproducibility; if one side is short, take all of
    it and let the other side fill up to k-len(short).
    """
    half = k // 2
    a_sorted = sorted(a_wins, key=lambda x: x["item_id"])
    b_sorted = sorted(b_wins, key=lambda x: x["item_id"])
    if len(a_sorted) >= half and len(b_sorted) >= half:
        return a_sorted[:half], b_sorted[:half]
    if len(a_sorted) < half:
        a_take = a_sorted
        b_take = b_sorted[:k - len(a_take)]
    else:
        b_take = b_sorted
        a_take = a_sorted[:k - len(b_take)]
    return a_take, b_take


# ---------------------------------------------------------------------------
# Stage B: meta-rule reflector (VLM, images in-context)
# ---------------------------------------------------------------------------

META_SYSTEM = (
    "You are auditing a two-branch visual anomaly detection ensemble.\n"
    "Branch A (Agent) does multi-turn reasoning with tool use; Branch B "
    "(Direct) does a single-pass judgment with no tools.\n"
    "You are shown cases where A and B disagreed. In each case one branch "
    "was correct (by GT) and the other was wrong. Your job: discover "
    "OBSERVABLE PATTERNS — things visible in the image or mentioned in a "
    "rationale — that predict which branch should be trusted.\n"
    "Do NOT write 'always trust X'. Do NOT cite item IDs. Each rule must "
    "be actionable at inference time from what the controller sees: image, "
    "refs, both branches' scores and rationales."
)

META_USER_TEMPLATE = (
    "Domain: {anchor}\n"
    "Number of A-wins cases (trust Agent): {n_a}\n"
    "Number of B-wins cases (trust Direct): {n_b}\n\n"
    "Below, each case shows NORMAL REFERENCES, then QUERY image, then the "
    "two branches' outputs, then the GT label.\n\n"
    "Write 1–3 routing rules PER SIDE. Return JSON only:\n"
    "{{\n"
    "  \"a_wins_rules\": [\"If <observable pattern>, trust A (Agent).\"],\n"
    "  \"b_wins_rules\": [\"If <observable pattern>, trust B (Direct).\"]\n"
    "}}"
)


def _case_block(case, idx, side_label):
    """Build the multimodal content block for a single case.

    Only the QUERY image is shown per case. Reference images are omitted
    because the vLLM backend caps image count at 12 per prompt, and
    K=10 cases * (1 query + 2 refs) = 30 images blows the limit. Ref
    information is recoverable from the two branches' rationales, which
    already describe ref content in text.
    """
    parts = []
    parts.append(text_msg(
        f"--- {side_label} case {idx} (item {case['item_id']}) ---\n"
        f"QUERY IMAGE:"
    ))
    if case.get("query_path") and os.path.exists(case["query_path"]):
        parts.append(img_msg(load_and_encode(case["query_path"])))
    parts.append(text_msg(
        f"Branch A (Agent) score={case['v9_score']:.3f}\n"
        f"  Rationale: {case['v9_rationale']}\n"
        f"Branch B (Direct) score={case['direct_score']:.3f}\n"
        f"  Rationale: {case['direct_rationale']}\n"
        f"GT: {'anomaly' if case['gt'] == 1 else 'normal'}\n"
    ))
    return parts


def build_meta_rules(client, model, domain_code, a_wins, b_wins,
                     anchor, max_tokens=600):
    """Call VLM reflector to produce meta-rules for one domain.

    Returns dict: {"a_wins_rules": [...], "b_wins_rules": [...],
                   "a_evidence": [item_ids], "b_evidence": [item_ids],
                   "raw": str, "error": str|None}
    """
    if not a_wins and not b_wins:
        return {"a_wins_rules": [], "b_wins_rules": [],
                "a_evidence": [], "b_evidence": [],
                "raw": "", "error": "no_disagreement_cases"}

    user_parts = [text_msg(META_USER_TEMPLATE.format(
        anchor=anchor, n_a=len(a_wins), n_b=len(b_wins)))]
    for i, c in enumerate(a_wins, 1):
        user_parts.extend(_case_block(c, i, "A-wins"))
    for i, c in enumerate(b_wins, 1):
        user_parts.extend(_case_block(c, i, "B-wins"))

    messages = [
        {"role": "system", "content": META_SYSTEM},
        {"role": "user", "content": user_parts},
    ]

    try:
        text, inp, out = call_llm(client, model, messages, max_tokens=max_tokens)
    except Exception as e:
        return {"a_wins_rules": [], "b_wins_rules": [],
                "a_evidence": [c["item_id"] for c in a_wins],
                "b_evidence": [c["item_id"] for c in b_wins],
                "raw": "", "error": f"{type(e).__name__}: {e}"}

    parsed = extract_json(text) or {}
    return {
        "a_wins_rules": parsed.get("a_wins_rules") or [],
        "b_wins_rules": parsed.get("b_wins_rules") or [],
        "a_evidence": [c["item_id"] for c in a_wins],
        "b_evidence": [c["item_id"] for c in b_wins],
        "raw": text,
        "tokens": {"input": inp, "output": out},
        "error": None if parsed else "parse_failed",
    }


# ---------------------------------------------------------------------------
# Stage C: combine v3 domain rules + meta-rules into flat store
# ---------------------------------------------------------------------------

def _load_v3_l1_rules(domain_code, l1_dir):
    """Return list of (category, invariant_text) from v3 L1 artifact."""
    p = Path(l1_dir) / f"{domain_code}_l1.json"
    if not p.exists():
        return []
    data = json.load(open(p))
    out = []
    for unit in data.get("units", []):
        u = unit.get("unit") or []
        # unit is [domain] or [domain, category]
        category = u[1] if len(u) >= 2 else None
        rb = unit.get("rulebook") or {}
        for inv in rb.get("invariants", []):
            txt = inv.get("statement") or ""
            if txt:
                out.append({
                    "type": "invariant",
                    "subtype": inv.get("type"),
                    "category": category,
                    "text": txt,
                    "source_items": [],
                    "confidence": rb.get("confidence", "unknown"),
                })
    return out


def _load_v3_l2_rules(domain_code, l2_dir):
    """Return list of corrective rules from v3 L2 artifact."""
    p = Path(l2_dir) / f"{domain_code}_l2.json"
    if not p.exists():
        return []
    data = json.load(open(p))
    out = []
    for unit in data.get("units", []):
        u = unit.get("unit") or []
        category = u[1] if len(u) >= 2 else None
        for r in unit.get("rules", []):
            side = r.get("side") or ""
            rtype = "corrective_fn" if side == "FN" else \
                    "corrective_fp" if side == "FP" else "corrective"
            txt = r.get("text") or ""
            if txt:
                out.append({
                    "type": rtype,
                    "subtype": r.get("rule_type"),
                    "category": category,
                    "text": txt,
                    "source_items": r.get("covers_items") or [],
                    "confidence": unit.get("confidence", "unknown"),
                })
    return out


def build_stack_rulebook(domain_code, meta_data, l1_dir, l2_dir):
    """Merge meta-rules + v3 L1 invariants + v3 L2 corrective into a single
    flat list, tagged so RAG can filter/rank.
    """
    rules = []

    # Meta-rules (domain-wide; no category — they're routing rules)
    if meta_data:
        for txt in meta_data.get("a_wins_rules", []):
            rules.append({
                "type": "meta_a_win",
                "category": None,
                "text": txt,
                "source_items": meta_data.get("a_evidence", []),
                "confidence": "oracle",
            })
        for txt in meta_data.get("b_wins_rules", []):
            rules.append({
                "type": "meta_b_win",
                "category": None,
                "text": txt,
                "source_items": meta_data.get("b_evidence", []),
                "confidence": "oracle",
            })

    rules.extend(_load_v3_l1_rules(domain_code, l1_dir))
    rules.extend(_load_v3_l2_rules(domain_code, l2_dir))

    # Stable IDs
    for i, r in enumerate(rules):
        r["id"] = f"{domain_code}_{r['type']}_{i}"

    return {
        "domain_code": domain_code,
        "n_rules": len(rules),
        "rules": rules,
        "meta_origin": {
            "error": (meta_data or {}).get("error"),
            "n_a_wins": len((meta_data or {}).get("a_evidence") or []),
            "n_b_wins": len((meta_data or {}).get("b_evidence") or []),
        },
    }


# ---------------------------------------------------------------------------
# Stage D: RAG retrieval (controller-side)
# ---------------------------------------------------------------------------

RULE_PRIORITY = {
    "meta_a_win": 0,
    "meta_b_win": 0,
    "invariant": 1,
    "corrective_fn": 2,
    "corrective_fp": 2,
    "corrective": 2,
}


def retrieve_rules_v4(rulebook_path: str, domain_code: str,
                     category: str | None,
                     max_meta: int = 3, max_domain: int = 4) -> str:
    """Load a v4 rulebook and return a rendered text block for the controller.

    Filter: rule.category is None (domain-wide) OR matches `category`.
    Rank:   meta-rules first (up to max_meta a_win+b_win combined), then
            invariants + corrective (up to max_domain total).
    Empty string if the rulebook is missing or has nothing applicable.
    """
    p = Path(rulebook_path)
    if not p.exists():
        return ""
    try:
        rb = json.load(open(p))
    except Exception:
        return ""
    if rb.get("domain_code") and rb["domain_code"] != domain_code:
        return ""

    applicable = []
    for r in rb.get("rules", []):
        cat = r.get("category")
        if cat is None or cat == category:
            applicable.append(r)

    metas = [r for r in applicable if r["type"].startswith("meta_")]
    domains = [r for r in applicable if not r["type"].startswith("meta_")]
    # rank domain rules: invariants before correctives
    domains.sort(key=lambda r: RULE_PRIORITY.get(r["type"], 99))
    metas.sort(key=lambda r: (r["type"], r.get("id", "")))

    metas = metas[:max_meta]
    domains = domains[:max_domain]

    lines = []
    if metas:
        lines.append("# Routing rules (which branch to trust):")
        for r in metas:
            tag = "A" if r["type"] == "meta_a_win" else "B"
            lines.append(f"- [trust {tag}] {r['text']}")
    if domains:
        if lines:
            lines.append("")
        lines.append("# Domain knowledge:")
        for r in domains:
            tag = r["type"].replace("corrective_", "").upper() \
                  if r["type"].startswith("corrective") else r["type"]
            lines.append(f"- [{tag}] {r['text']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_manifest_items(domain_code, manifest_dir):
    """Return {item_id: row} for this domain, all splits."""
    # Manifest filenames follow D{n}_*_manifest.json
    matches = list(Path(manifest_dir).glob(f"{domain_code}_*_manifest.json"))
    if not matches:
        return {}
    data = json.load(open(matches[0]))
    return {x["item_id"]: x for x in data}


def cmd_build_meta(args):
    cfg = load_domain_config()
    client = get_client(args.backend)
    model = get_model_name(args.backend)
    Path(args.out_dir).mkdir(parents=True, exist_ok=True)

    dev_path_tpl = str(Path(args.dev_dir) / "{dc}.json")

    for dc in (args.domains or DOMAIN_CODES):
        out = Path(args.out_dir) / f"{dc}_meta.json"
        if out.exists() and not args.overwrite:
            print(f"[{dc}] skip (exists)")
            continue

        dev_file = dev_path_tpl.format(dc=dc)
        if not os.path.exists(dev_file):
            print(f"[{dc}] MISSING dev file {dev_file} — skip")
            continue
        dev_results = json.load(open(dev_file))
        manifest_items = _load_manifest_items(dc, args.manifest_dir)

        buckets = partition_dev(dev_results, manifest_items)
        a_all = buckets["disagree_a_wins"]
        b_all = buckets["disagree_b_wins"]
        a_take, b_take = balanced_sample(a_all, b_all, k=args.k)

        print(f"[{dc}] partition: agree_correct={len(buckets['agree_correct'])} "
              f"agree_wrong={len(buckets['agree_wrong'])} "
              f"A-wins={len(a_all)} B-wins={len(b_all)} "
              f"→ reflect on {len(a_take)}+{len(b_take)}")

        anchor = compose_anchor(cfg, dc)
        t0 = time.time()
        meta = build_meta_rules(client, model, dc, a_take, b_take, anchor,
                                max_tokens=args.max_tokens)
        meta["partition_stats"] = {
            "agree_correct": len(buckets["agree_correct"]),
            "agree_wrong": len(buckets["agree_wrong"]),
            "disagree_a_wins_total": len(a_all),
            "disagree_b_wins_total": len(b_all),
            "reflected_a": len(a_take),
            "reflected_b": len(b_take),
            "skipped": len(buckets["skipped"]),
        }
        meta["domain_code"] = dc
        meta["seconds"] = round(time.time() - t0, 1)
        json.dump(meta, open(out, "w"), indent=2)
        print(f"[{dc}] meta.a={len(meta['a_wins_rules'])} "
              f"meta.b={len(meta['b_wins_rules'])} "
              f"t={meta['seconds']}s err={meta.get('error')}")


def cmd_build_stack(args):
    Path(args.out_dir).mkdir(parents=True, exist_ok=True)
    for dc in (args.domains or DOMAIN_CODES):
        meta_path = Path(args.meta_dir) / f"{dc}_meta.json"
        meta_data = json.load(open(meta_path)) if meta_path.exists() else {}
        rb = build_stack_rulebook(dc, meta_data, args.l1_dir, args.l2_dir)
        out = Path(args.out_dir) / f"{dc}.json"
        json.dump(rb, open(out, "w"), indent=2)
        counts = defaultdict(int)
        for r in rb["rules"]:
            counts[r["type"]] += 1
        print(f"[{dc}] stacked {rb['n_rules']} rules: {dict(counts)}")


def cmd_preview(args):
    """Render what the controller will see for a given domain/category."""
    rb_path = Path(args.rulebook_dir) / f"{args.domain}.json"
    text = retrieve_rules_v4(str(rb_path), args.domain, args.category,
                             max_meta=args.max_meta, max_domain=args.max_domain)
    print(text or "(empty)")


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)

    p_meta = sp.add_parser("build-meta",
                           help="Stage B: VLM reflector over disagreement cases")
    p_meta.add_argument("--dev_dir", default=DEFAULT_DEV_DIR)
    p_meta.add_argument("--manifest_dir", default=DEFAULT_MANIFESTS)
    p_meta.add_argument("--out_dir", default=DEFAULT_META_DIR)
    p_meta.add_argument("--backend", choices=["gpt", "seedvl", "qwen3"],
                        default="qwen3")
    p_meta.add_argument("--domains", nargs="+", default=None)
    p_meta.add_argument("--k", type=int, default=10,
                        help="max cases fed to reflector (K/2 each side)")
    p_meta.add_argument("--max_tokens", type=int, default=600)
    p_meta.add_argument("--overwrite", action="store_true")
    p_meta.set_defaults(func=cmd_build_meta)

    p_stack = sp.add_parser("build-stack",
                            help="Stage C: merge v3 L1/L2 + meta into rulebook")
    p_stack.add_argument("--meta_dir", default=DEFAULT_META_DIR)
    p_stack.add_argument("--l1_dir", default=DEFAULT_L1_DIR)
    p_stack.add_argument("--l2_dir", default=DEFAULT_L2_DIR)
    p_stack.add_argument("--out_dir", default=DEFAULT_STACK_DIR)
    p_stack.add_argument("--domains", nargs="+", default=None)
    p_stack.set_defaults(func=cmd_build_stack)

    p_prev = sp.add_parser("preview", help="Render retrieved rules for controller")
    p_prev.add_argument("--rulebook_dir", default=DEFAULT_STACK_DIR)
    p_prev.add_argument("--domain", required=True)
    p_prev.add_argument("--category", default=None)
    p_prev.add_argument("--max_meta", type=int, default=3)
    p_prev.add_argument("--max_domain", type=int, default=4)
    p_prev.set_defaults(func=cmd_preview)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
