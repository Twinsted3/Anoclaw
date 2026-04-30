"""Verbalized Self-Evolution v2 — anchor + RAG.

Design decisions (see §5 redesign notes):
  (1) Task anchor from `manifests_v2/domain_config.json` is injected into
      the agent's SYSTEM prompt. This fixes the missing task-anchor
      problem in v1 (L1 rulebook only described normal/anomaly, never said
      what the benchmark counts as anomalous in this domain).
  (2) Rules are flattened into a per-(domain, class) store, retrieved
      with metadata filtering + priority ranking (L2-corrective first,
      then L1 by natural order), capped at top-K. This replaces the
      full-rulebook JSON dump which had ~250 tokens per query and caused
      checklist-style bias.
  (3) Retrieved rules are rendered as a brief markdown list injected in
      the user message (after ref images, before task preamble). Total
      payload ≤ ~80 tokens.

This module is orthogonal to v1 (`verbalized_learning.py`) — it consumes
the same L1/L2 artifacts but applies them differently.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import agent_v9 as v9_mod  # noqa: E402
from infer import get_client, get_model_name  # noqa: E402


MULTI_CLASS_DOMAINS = {"D1", "D2", "D3", "D4", "D5", "D6"}

DOMAIN_CONFIG_PATH = "/hdd1/jiangxi/AD-Agent/benchmark/manifests_v2/domain_config.json"


# ---------------------------------------------------------------------------
# Task anchor
# ---------------------------------------------------------------------------

def load_domain_config(path=DOMAIN_CONFIG_PATH):
    return json.load(open(path))


def compose_anchor(domain_cfg, domain_code):
    """One-sentence task anchor injected into system prompt.

    Matches §4 Table 12 descriptor style (+3.2pp Qwen3.5 evidence that
    a short task anchor helps the VLM define what "anomalous" means).
    """
    d = domain_cfg.get(domain_code, {})
    name = d.get("name", domain_code)
    at = d.get("anomaly_type", "anomaly")
    desc = d.get("description", "")
    return (f"Domain task anchor: detect {at} anomalies "
            f"in {name}. {desc}").strip()


# ---------------------------------------------------------------------------
# Rule store — flatten L1 + L2 with source tags
# ---------------------------------------------------------------------------

def _l1_unit_rules(unit):
    """Return rule texts from an L1 unit in natural order."""
    rb = unit.get("rulebook", {}) or {}
    out = []
    # Use `rules` primarily; fall back to anomaly_modes if rules empty.
    for r in rb.get("rules", [])[:8]:
        if isinstance(r, str) and r.strip():
            out.append(r.strip())
    for r in rb.get("hypothesized_anomaly_modes", [])[:6]:
        if isinstance(r, str) and r.strip():
            out.append(f"anomaly mode: {r.strip()}")
    return out


def _l2_unit_rules(unit, drop_normal_tolerance=True):
    """Return L2 corrective rule texts tagged with rule_type.

    By default we DROP `normal_tolerance` rules because our K=10 oracle
    selection (lowest-confidence dev items) is biased toward FP cases
    the agent flagged as anomaly but GT was normal. The reflector then
    over-generates ``do not classify X as anomalous'' rules that
    generalise too aggressively and suppress true positives at test
    time (diagnosed 2026-04-21 on D8 derma / D9 brain / D10 liver).
    """
    out = []
    for r in unit.get("rules", []):
        if not isinstance(r, dict):
            continue
        txt = (r.get("text", "") or "").strip()
        if not txt:
            continue
        rtype = r.get("rule_type", "rule")
        if drop_normal_tolerance and rtype == "normal_tolerance":
            continue
        out.append(f"(corrective:{rtype}) {txt}")
    return out


def build_rule_store(l1_dir, l2_dir):
    """Build a dict keyed by (domain, class) → list[{text, source, priority}].

    Lower priority number = injected first.
        0 = L2 corrective (oracle-grounded, strongest signal)
        1 = L1 if-then rule (top of rulebook)
        2 = L1 hypothesized anomaly mode (background)
    """
    store = {}
    for f in sorted(Path(l1_dir).glob("D*_l1.json")):
        data = json.load(open(f))
        for u in data.get("units", []):
            key = tuple(u["unit"])
            rules = _l1_unit_rules(u)
            for i, t in enumerate(rules):
                prio = 1 if not t.startswith("anomaly mode:") else 2
                store.setdefault(key, []).append(
                    {"text": t, "source": "L1", "priority": prio,
                     "order": i})
    for f in sorted(Path(l2_dir).glob("D*_l2.json")):
        data = json.load(open(f))
        for u in data.get("units", []):
            key = tuple(u["unit"])
            rules = _l2_unit_rules(u)
            for i, t in enumerate(rules):
                store.setdefault(key, []).append(
                    {"text": t, "source": "L2", "priority": 0,
                     "order": i})
    return store


def retrieve_rules(store, domain_code, category, k=3, sources=None):
    """Return top-K rules for (domain, category) by priority+order.

    Args:
      sources: if given, a set like {"L1"}, {"L2"}, or {"L1","L2"}. Filters
        before ranking. Enables running the L1-only vs L2-only vs stacked
        variants from the same store.
    """
    if domain_code in MULTI_CLASS_DOMAINS:
        key = (domain_code, category)
    else:
        key = (domain_code,)
    pool = store.get(key, [])
    if sources is not None:
        pool = [r for r in pool if r["source"] in sources]
    pool_sorted = sorted(pool, key=lambda r: (r["priority"], r["order"]))
    return pool_sorted[:k]


def compose_user_rules_block(rules):
    """Render retrieved rules as a brief markdown list for user-msg injection."""
    if not rules:
        return ""
    lines = ["Relevant domain rules (advisory — not exhaustive):"]
    for i, r in enumerate(rules, 1):
        tag = "" if r["source"] == "L1" else f" [{r['source']}]"
        lines.append(f"{i}. {r['text']}{tag}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# eval-test-v2 runner
# ---------------------------------------------------------------------------

def run_v2_eval(manifest_path, out_path, variant, l1_dir, l2_dir,
                domain_config, *, backend="qwen3", max_turns=3,
                workers=6, top_k=3, use_anchor=True):
    """Run v9 agent on test split with v2 injection for one domain."""
    manifest = json.load(open(manifest_path))
    test_items = [it for it in manifest if it.get("split") == "test"]
    store = build_rule_store(l1_dir, l2_dir)
    client = get_client(backend)
    model = get_model_name(backend)

    sources_map = {
        "anchor":   set(),                 # anchor-only, no rules retrieved
        "l1":       {"L1"},
        "l2":       {"L2"},
        "l1l2":     {"L1", "L2"},
    }
    if variant not in sources_map:
        raise ValueError(f"Unknown variant {variant}. "
                         f"Use anchor | l1 | l2 | l1l2.")
    sources = sources_map[variant]

    results = []

    def _run_one(it):
        d = it.get("domain_code"); c = it.get("category")
        anchor_str = compose_anchor(domain_config, d) if use_anchor else None
        if variant == "anchor":
            rules_block = None
        else:
            rules = retrieve_rules(store, d, c, k=top_k, sources=sources)
            rules_block = compose_user_rules_block(rules)
        return v9_mod.run_v9_item(
            client, model, it, split="test",
            max_turns=max_turns,
            rulebook=rules_block,       # injected into user msg by v9 agent
            # system_prefix passed via a new kwarg we add in agent_v9 below
        ), anchor_str, rules_block

    # We patch SYSTEM_PROMPT globally per-item via a wrapper rather than
    # modifying agent_v9. Simplest: temporarily replace the module-level
    # constant inside a lock. But multi-threaded calls need thread-safe
    # anchor propagation — instead, pass anchor via a thread-local.
    #
    # To keep the diff minimal: we prepend anchor to the `rulebook` arg
    # (system prompts already carry the instructions; the model reads the
    # anchor at the top of the user message, which is also effective per
    # §4 Table 12 — descriptor-as-user-context is the same pattern used
    # by v6_direct).
    def _compose_full_rulebook(anchor, rules_block):
        parts = []
        if anchor:
            parts.append(f"TASK CONTEXT\n{anchor}")
        if rules_block:
            parts.append(rules_block)
        return "\n\n".join(parts) if parts else None

    def _run_one_v2(it):
        d = it.get("domain_code"); c = it.get("category")
        anchor_str = compose_anchor(domain_config, d) if use_anchor else None
        if variant == "anchor":
            rules = []
        else:
            rules = retrieve_rules(store, d, c, k=top_k, sources=sources)
        rules_block = compose_user_rules_block(rules) if rules else ""
        full = _compose_full_rulebook(anchor_str, rules_block)
        r = v9_mod.run_v9_item(
            client, model, it, split="test",
            max_turns=max_turns,
            rulebook=full,
        )
        return r, anchor_str, rules_block

    with ThreadPoolExecutor(max_workers=workers) as ex:
        fut = {ex.submit(_run_one_v2, it): it for it in test_items}
        for f in as_completed(fut):
            it = fut[f]
            try:
                r, anc, rb = f.result()
                results.append({
                    "item_id": r.item_id,
                    "score": r.score,
                    "mode": r.mode,
                    "rationale": r.rationale,
                    "label": it.get("label"),
                    "domain_code": it.get("domain_code"),
                    "category": it.get("category"),
                    "anchor_injected": bool(anc),
                    "n_rules_injected": len(rb.splitlines()) - 1 if rb else 0,
                })
            except Exception as e:
                print(f"[v2-eval] {it['item_id']} failed: {e}",
                      file=sys.stderr)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(results, indent=2,
                                          ensure_ascii=False))
    print(f"[v2-eval] wrote {out_path} ({len(results)} items)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--variant", required=True,
                    choices=["anchor", "l1", "l2", "l1l2"])
    ap.add_argument("--l1_dir",
                    default="/hdd1/jiangxi/AD-Agent/benchmark/results/verbalized/l1")
    ap.add_argument("--l2_dir",
                    default="/hdd1/jiangxi/AD-Agent/benchmark/results/verbalized/l2")
    ap.add_argument("--domain_config", default=DOMAIN_CONFIG_PATH)
    ap.add_argument("--backend", default="qwen3")
    ap.add_argument("--max_turns", type=int, default=3)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--top_k", type=int, default=3)
    ap.add_argument("--no_anchor", action="store_true",
                    help="Disable anchor injection (diagnostic only).")
    args = ap.parse_args()

    dc = load_domain_config(args.domain_config)
    run_v2_eval(args.manifest, args.out, args.variant,
                args.l1_dir, args.l2_dir, dc,
                backend=args.backend, max_turns=args.max_turns,
                workers=args.workers, top_k=args.top_k,
                use_anchor=not args.no_anchor)


if __name__ == "__main__":
    main()
