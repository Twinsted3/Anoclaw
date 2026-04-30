"""Verbalized Self-Evolution v3 — invariant-L1 + cluster-L2 + RAG.

Framework redesign per §5 v3 plan:
  L1 (offline, ref-only):
      reflector lists ref-verifiable INVARIANTS, no hypothesised anomaly
      modes. Invariant types restricted to:
        count | symmetry | spatial_layout | color_palette | texture | structural
      Empty list allowed (weak-prior domains honestly say 'nothing
      stable to extract').
      Anomaly at test time = invariant violation. Fabricated anomaly
      modes (the v1/v2 failure mode) are removed.

  L2 (offline, oracle-based):
      balanced K/2 FN + K/2 FP selection on dev.
      reflector sees the WHOLE batch of oracle items (images + agent
      trajectories + GT labels) at once and writes 1-3 cluster rules
      per side (FN and FP). This produces 2-6 per-domain rules grounded
      in observed error patterns rather than 10 per-item rules with
      redundancy and normal_tolerance bias.

  RAG (online, per-query):
      metadata filter by (domain, class) [class optional for single-class
      domains]; within the filtered pool, guarantee at least 1 L1
      invariant in the top-K. Sources tagged [invariant] / [corrective-fn]
      / [corrective-fp] in the injected list so the agent knows
      provenance.

  Agent:
      v9 unchanged. Task anchor in system prompt. Retrieved rules in
      user message (brief markdown).
"""
from __future__ import annotations
import argparse
import json
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import agent_v9 as v9_mod  # noqa: E402
from infer import (  # noqa: E402
    call_llm, extract_json, get_client, get_model_name,
    img_msg, load_and_encode, text_msg,
)
from verbalized_learning import (  # noqa: E402
    MULTI_CLASS_DOMAINS, DOMAIN_FILES, group_units, collect_unit_refs,
    unit_label, split_dev_ids,
)


DOMAIN_CONFIG_PATH = "/hdd1/jiangxi/AD-Agent/benchmark/manifests_v2/domain_config.json"


# ---------------------------------------------------------------------------
# Task anchor (shared)
# ---------------------------------------------------------------------------

def load_domain_config(path=DOMAIN_CONFIG_PATH):
    return json.load(open(path))


def compose_anchor(domain_cfg, domain_code):
    d = domain_cfg.get(domain_code, {})
    name = d.get("name", domain_code)
    at = d.get("anomaly_type", "anomaly")
    desc = d.get("description", "")
    return f"Detect {at} anomalies in {name}. {desc}".strip()


# ---------------------------------------------------------------------------
# L1 v3: invariant extraction only
# ---------------------------------------------------------------------------

INVARIANT_TYPES = ["count", "symmetry", "spatial_layout",
                   "color_palette", "texture", "structural"]

L1_V3_SYSTEM = (
    "You are extracting VISUAL INVARIANTS from a small set of NORMAL "
    "reference images of a specific object class. An invariant is a "
    "concrete property that holds TRUE for EVERY reference image, "
    "such that a query image lacking that property is by definition "
    "anomalous. Your job is NOT to guess what anomalies look like — "
    "anomalies are by definition violations of the invariants you "
    "extract. Be strict: if you cannot verify a property in every ref, "
    "do NOT list it."
)

L1_V3_USER_TEMPLATE = """Class: {unit_name}
Domain task anchor: {task_anchor}
Number of reference images: {n_refs}

Extract INVARIANTS from the refs. Each invariant must be verifiable in \
EVERY ref image.

Allowed invariant types (use exactly one per entry):
  - count           (exact number of parts, segments, compartments, \
objects, etc.)
  - symmetry        (bilateral / radial / rotational symmetry)
  - spatial_layout  (where parts/compartments/objects must be placed)
  - color_palette   (allowed colour set or dominant colour constraint)
  - texture         (surface pattern regularity; e.g. fine grain, mesh)
  - structural      (object-level geometry, boundary continuity, etc.)

Output strict JSON, no prose outside:

{{
  "invariants": [
    {{
      "type": "count|symmetry|spatial_layout|color_palette|texture|structural",
      "statement": "concise visual predicate, <=20 words, the NORMAL state",
      "evidence": "short note on why refs support this (e.g. 'all 8 refs show exactly 3 fruits left')"
    }}
  ],
  "confidence": "high | medium | low"
}}

HARD rules:
  - If you cannot find ANY invariant that holds across all refs, \
return an empty "invariants" list. Do not invent anomaly modes.
  - Do NOT output any "anomaly" list, "rules" list, or predict what \
could go wrong. Those are downstream concerns.
  - Invariants must describe the NORMAL STATE. The anomaly signal at \
test time is "query image VIOLATES an invariant".
  - 0 to 6 invariants total. Quality over quantity.
  - confidence="high" if every invariant is strongly visible in refs; \
"low" if weak refs or novel domain.
"""


def build_l1_invariants(unit_key, ref_paths, client, model, *,
                        n_refs=8, max_retries=3, task_anchor=""):
    refs_used = ref_paths[:n_refs]
    parts = [img_msg(load_and_encode(rp)) for rp in refs_used]
    parts.append(text_msg(L1_V3_USER_TEMPLATE.format(
        unit_name=unit_label(unit_key), n_refs=len(refs_used),
        task_anchor=task_anchor or "(not provided)")))
    messages = [
        {"role": "system", "content": L1_V3_SYSTEM},
        {"role": "user", "content": parts},
    ]
    for _ in range(max_retries):
        try:
            resp_text, _, _ = call_llm(client, model, messages,
                                        temperature=0.0, max_tokens=900)
            parsed = extract_json(resp_text)
            if isinstance(parsed, dict) and "invariants" in parsed:
                # Normalize: filter to allowed types.
                clean = []
                for iv in parsed.get("invariants", []) or []:
                    if not isinstance(iv, dict):
                        continue
                    t = iv.get("type")
                    st = (iv.get("statement") or "").strip()
                    if t in INVARIANT_TYPES and st:
                        clean.append({
                            "type": t,
                            "statement": st,
                            "evidence": (iv.get("evidence") or "").strip(),
                        })
                parsed["invariants"] = clean
                parsed.setdefault("confidence", "low")
                return {
                    "unit": list(unit_key),
                    "n_refs_seen": len(refs_used),
                    "rulebook": parsed,
                }
        except Exception as e:
            print(f"[L1 v3 reflect] retry {unit_key}: {e}",
                  file=sys.stderr)
            time.sleep(1.0)
    return {"unit": list(unit_key), "n_refs_seen": len(refs_used),
            "rulebook": {"invariants": [], "confidence": "failed"}}


# ---------------------------------------------------------------------------
# L2 v3: cluster-based batch reflection
# ---------------------------------------------------------------------------

L2_V3_SYSTEM = (
    "You are a visual anomaly-detection expert reviewing a batch of "
    "DEV items the colleague agent misclassified. The ground-truth "
    "labels have been revealed to you. Your job is to find COMMON "
    "PATTERNS across items and propose a SMALL number (1-3 per side) "
    "of generalisable rules that would correct the agent's systematic "
    "errors on this class."
)

L2_V3_USER_TEMPLATE = """Class: {unit_name}
Domain task anchor: {task_anchor}

You will see K={k} dev items the agent got wrong or was uncertain about, \
split into FN (agent said NORMAL but GT is ANOMALY) and FP (agent said \
ANOMALY but GT is NORMAL). For each item you have: the query image, the \
agent's predicted score, and the agent's reasoning trace.

Your task:
  Write 1-3 CORRECTIVE RULES per side (FN side, FP side), where each \
rule captures a pattern observed across multiple items. If one side has \
fewer than 2 items, you may omit that side. If you see a pattern that \
applies to only ONE item, do NOT write a rule for it — it won't \
generalise.

Output strict JSON:

{{
  "fn_patterns": [
    {{
      "rule_type": "anomaly_mode_extension",
      "text": "short rule, <=25 words, starts with a visual condition",
      "covers_items": ["D1_0032", "D1_0045"],
      "justification": "<=40 words explaining the common pattern"
    }}
  ],
  "fp_patterns": [
    {{
      "rule_type": "normal_tolerance" | "rule",
      "text": "short rule, <=25 words; must name a SPECIFIC visual feature (no 'do not flag X')",
      "covers_items": ["D1_0070", "D1_0073"],
      "justification": "<=40 words"
    }}
  ],
  "confidence": "high | medium | low"
}}

Items below:

{items_block}
"""


def _format_l2_items_block(oracle_items, oracle_results):
    """Render items for batch reflection: label, score, trajectory."""
    lines = []
    # Split by FN / FP
    fn = []; fp = []
    for it, res in zip(oracle_items, oracle_results):
        gt = int(it.get("label", 0))
        sc = float(res.get("score", 0.5))
        is_fn = gt == 1 and sc < 0.5
        is_fp = gt == 0 and sc >= 0.5
        side = "FN" if is_fn else ("FP" if is_fp else "OTHER")
        traj = _compact_traj_v3(res)
        entry = (f"[{side}] {it['item_id']}  gt={'ANOMALY' if gt else 'NORMAL'}"
                 f"  agent_score={sc:.2f}\n"
                 f"     trajectory: {traj}")
        if side == "FN":
            fn.append(entry)
        elif side == "FP":
            fp.append(entry)
        else:
            fn.append(entry) if gt == 1 else fp.append(entry)
    out = []
    if fn:
        out.append("=== FN items (agent missed anomaly) ===")
        out.extend(fn)
    if fp:
        out.append("")
        out.append("=== FP items (agent over-flagged normal) ===")
        out.extend(fp)
    return "\n".join(out)


def _compact_traj_v3(res, max_chars=400):
    r = res or {}
    parts = []
    cf = r.get("candidate_features") or []
    if cf:
        parts.append("candidates=" + "; ".join(str(x) for x in cf[:4]))
    rv = r.get("refutation_verdicts") or []
    if rv:
        parts.append("refut=" + "; ".join(
            f"t{v.get('turn')}:{v.get('verdict')}" for v in rv[:3]))
    rat = (r.get("rationale") or "").replace("\n", " ")
    if rat:
        parts.append("rat=" + rat[:220])
    return " | ".join(parts)[:max_chars]


def build_l2_cluster(unit_key, oracle_items, oracle_results, client, model,
                     *, max_retries=3, task_anchor=""):
    if not oracle_items:
        return {"unit": list(unit_key), "k": 0, "rules": [],
                "confidence": "n/a"}
    # Build batched user content with all images + text block
    parts = []
    for it in oracle_items:
        parts.append(img_msg(load_and_encode(it["query_path"])))
    block = _format_l2_items_block(oracle_items, oracle_results)
    parts.append(text_msg(L2_V3_USER_TEMPLATE.format(
        unit_name=unit_label(unit_key),
        task_anchor=task_anchor or "(not provided)",
        k=len(oracle_items),
        items_block=block,
    )))
    messages = [
        {"role": "system", "content": L2_V3_SYSTEM},
        {"role": "user", "content": parts},
    ]
    for _ in range(max_retries):
        try:
            resp_text, _, _ = call_llm(client, model, messages,
                                        temperature=0.0, max_tokens=1200)
            parsed = extract_json(resp_text)
            if isinstance(parsed, dict):
                fn_rules = parsed.get("fn_patterns") or []
                fp_rules = parsed.get("fp_patterns") or []
                out_rules = []
                for r in fn_rules:
                    if isinstance(r, dict) and r.get("text"):
                        r.setdefault("rule_type", "anomaly_mode_extension")
                        r["side"] = "FN"
                        out_rules.append(r)
                for r in fp_rules:
                    if isinstance(r, dict) and r.get("text"):
                        r.setdefault("rule_type", "rule")
                        r["side"] = "FP"
                        out_rules.append(r)
                return {
                    "unit": list(unit_key),
                    "k": len(oracle_items),
                    "rules": out_rules,
                    "confidence": parsed.get("confidence", "low"),
                }
        except Exception as e:
            print(f"[L2 v3 cluster] retry {unit_key}: {e}", file=sys.stderr)
            time.sleep(1.0)
    return {"unit": list(unit_key), "k": len(oracle_items), "rules": [],
            "confidence": "failed"}


# ---------------------------------------------------------------------------
# Rule store + RAG (guaranteed invariant)
# ---------------------------------------------------------------------------

def build_rule_store_v3(l1_dir, l2_dir):
    """Flat rule store keyed by (domain, class) with type tags."""
    store = {}

    def push(key, text, src, rtype, priority, order, meta=None):
        if not text or not text.strip():
            return
        store.setdefault(key, []).append({
            "text": text.strip(),
            "source": src,
            "type": rtype,   # 'invariant' | 'corrective_fn' | 'corrective_fp' | 'rule'
            "priority": priority,
            "order": order,
            "meta": meta or {},
        })

    for f in sorted(Path(l1_dir).glob("D*_l1.json")):
        data = json.load(open(f))
        for u in data.get("units", []):
            key = tuple(u["unit"])
            rb = u.get("rulebook", {}) or {}
            for i, iv in enumerate(rb.get("invariants", []) or []):
                txt = f"[{iv.get('type','?')}] normal: {iv.get('statement','')}"
                push(key, txt, "L1", "invariant", priority=1, order=i,
                     meta={"inv_type": iv.get("type")})

    for f in sorted(Path(l2_dir).glob("D*_l2.json")):
        data = json.load(open(f))
        for u in data.get("units", []):
            key = tuple(u["unit"])
            for i, r in enumerate(u.get("rules", []) or []):
                side = r.get("side", "FN")
                rtype = "corrective_fn" if side == "FN" else "corrective_fp"
                prio = 0 if side == "FN" else 2   # FN > invariants > FP
                push(key, r.get("text", ""), "L2", rtype,
                     priority=prio, order=i,
                     meta={"rule_type": r.get("rule_type"),
                           "covers": r.get("covers_items", [])})

    return store


def retrieve_rules_v3(store, domain_code, category, k=3,
                     require_invariant=True, sources=None):
    """Retrieve top-k rules. Guarantee at least one L1 invariant if
    available for the class (unless sources excludes L1)."""
    if domain_code in MULTI_CLASS_DOMAINS:
        key = (domain_code, category)
    else:
        key = (domain_code,)
    pool = list(store.get(key, []))
    if sources is not None:
        pool = [r for r in pool if r["source"] in sources]
    pool.sort(key=lambda r: (r["priority"], r["order"]))

    if require_invariant and sources is None:
        invariants = [r for r in pool if r["type"] == "invariant"]
        others = [r for r in pool if r["type"] != "invariant"]
        out = []
        if invariants:
            out.append(invariants[0])
        # fill remainder from priority-sorted pool, skipping already-added
        for r in pool:
            if r in out:
                continue
            out.append(r)
            if len(out) >= k:
                break
        return out[:k]
    return pool[:k]


def compose_user_rules_block_v3(rules):
    if not rules:
        return ""
    lines = ["Relevant domain rules (advisory — not exhaustive):"]
    for i, r in enumerate(rules, 1):
        tag = r["type"]
        lines.append(f"{i}. [{tag}] {r['text']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI: build-l1, build-l2, eval-test
# ---------------------------------------------------------------------------

def _read_json(p): return json.loads(Path(p).read_text())
def _write_json(p, o):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(o, indent=2, ensure_ascii=False))


def cmd_build_l1(args):
    manifest = _read_json(args.manifest)
    client = get_client(args.backend)
    model = get_model_name(args.backend)
    groups = group_units(manifest)
    dc = load_domain_config(args.domain_config) if args.domain_config else {}

    out = {"domain": None, "units": []}
    for unit_key, items in groups.items():
        out["domain"] = unit_key[0]
        refs = collect_unit_refs(items)
        if args.seed is not None:
            rng = random.Random(args.seed)
            rng.shuffle(refs)
        anchor = compose_anchor(dc, unit_key[0])
        rb = build_l1_invariants(unit_key, refs, client, model,
                                 n_refs=args.n_refs, task_anchor=anchor)
        out["units"].append(rb)
        inv = rb["rulebook"].get("invariants", [])
        print(f"[L1 v3] {unit_key}: {len(inv)} invariants "
              f"conf={rb['rulebook'].get('confidence','?')}")
    _write_json(args.out, out)
    print(f"[L1 v3] wrote {args.out}")


def cmd_build_l2(args):
    manifest = _read_json(args.manifest)
    passive = _read_json(args.passive_dev)
    manifest_by_id = {it["item_id"]: it for it in manifest}
    groups = group_units(manifest)

    dev_items = [it for it in manifest if it.get("split") == "dev"]
    domain_code = dev_items[0]["domain_code"] if dev_items else "?"
    selection_ids, validation_ids = split_dev_ids(
        [it["item_id"] for it in dev_items], seed=args.seed,
        selection_frac=args.selection_frac)
    print(f"[L2 v3] {domain_code} seed={args.seed}: "
          f"sel={len(selection_ids)}, val={len(validation_ids)}")

    passive_dev = {r["item_id"]: r for r in passive
                   if r["item_id"] in {it["item_id"] for it in dev_items}}
    client = get_client(args.backend)
    model = get_model_name(args.backend)
    dc = load_domain_config(args.domain_config) if args.domain_config else {}

    out = {"domain": domain_code, "seed": args.seed, "k": args.k,
           "selection_frac": args.selection_frac,
           "selection_ids": selection_ids,
           "validation_ids": validation_ids,
           "units": []}
    for unit_key, items in groups.items():
        unit_dev = [it for it in items if it.get("split") == "dev"]
        unit_ids = {it["item_id"] for it in unit_dev}
        unit_passive = [passive_dev[i] for i in unit_ids if i in passive_dev]
        if not unit_passive:
            print(f"[L2 v3] {unit_key}: no passive_dev, skip")
            continue
        from verbalized_learning import select_oracle_items_balanced
        oracle_items, oracle_results = select_oracle_items_balanced(
            unit_passive, manifest_by_id, k=args.k,
            selection_ids=selection_ids)
        if not oracle_items:
            print(f"[L2 v3] {unit_key}: empty oracle, skip")
            continue
        anchor = compose_anchor(dc, unit_key[0])
        rb = build_l2_cluster(unit_key, oracle_items, oracle_results,
                              client, model, task_anchor=anchor)
        out["units"].append(rb)
        print(f"[L2 v3] {unit_key}: k={rb['k']}, rules={len(rb['rules'])}, "
              f"conf={rb.get('confidence','?')}")
    _write_json(args.out, out)
    print(f"[L2 v3] wrote {args.out}")


def cmd_eval_test(args):
    manifest = _read_json(args.manifest)
    test_items = [it for it in manifest if it.get("split") == "test"]
    store = build_rule_store_v3(args.l1_dir, args.l2_dir)
    client = get_client(args.backend)
    model = get_model_name(args.backend)
    dc = load_domain_config(args.domain_config) if args.domain_config else {}

    src_map = {
        "anchor": None,
        "l1":     {"L1"},
        "l2":     {"L2"},
        "l1l2":   None,
    }
    if args.variant not in src_map:
        raise ValueError(args.variant)
    sources = src_map[args.variant]
    # anchor variant injects task anchor only; no rules at all
    inject_rules = args.variant != "anchor"

    results = []

    def _compose(it):
        d = it.get("domain_code"); c = it.get("category")
        anchor = compose_anchor(dc, d) if args.use_anchor else None
        if not inject_rules:
            rules = []
        else:
            rules = retrieve_rules_v3(store, d, c, k=args.top_k,
                                      sources=sources,
                                      require_invariant=(args.variant == "l1l2"))
        block = compose_user_rules_block_v3(rules)
        parts = []
        if anchor: parts.append(f"TASK CONTEXT\n{anchor}")
        if block:  parts.append(block)
        return ("\n\n".join(parts) if parts else None), rules

    def _run_one(it):
        payload, rules = _compose(it)
        r = v9_mod.run_v9_item(client, model, it, split="test",
                                max_turns=args.max_turns,
                                rulebook=payload)
        return r, rules

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        fut = {ex.submit(_run_one, it): it for it in test_items}
        for f in as_completed(fut):
            it = fut[f]
            try:
                r, rules = f.result()
                results.append({
                    "item_id": r.item_id,
                    "score": r.score,
                    "mode": r.mode,
                    "rationale": r.rationale,
                    "label": it.get("label"),
                    "domain_code": it.get("domain_code"),
                    "category": it.get("category"),
                    "n_rules_injected": len(rules),
                    "rule_types": [x["type"] for x in rules],
                })
            except Exception as e:
                print(f"[eval v3] {it['item_id']} failed: {e}",
                      file=sys.stderr)
    _write_json(args.out, results)
    print(f"[eval v3] wrote {args.out} ({len(results)} items)")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("build-l1")
    p1.add_argument("--manifest", required=True)
    p1.add_argument("--out", required=True)
    p1.add_argument("--n_refs", type=int, default=8)
    p1.add_argument("--seed", type=int, default=0)
    p1.add_argument("--backend", default="qwen3")
    p1.add_argument("--domain_config", default=DOMAIN_CONFIG_PATH)
    p1.set_defaults(func=cmd_build_l1)

    p2 = sub.add_parser("build-l2")
    p2.add_argument("--manifest", required=True)
    p2.add_argument("--passive_dev", required=True)
    p2.add_argument("--out", required=True)
    p2.add_argument("--k", type=int, default=10)
    p2.add_argument("--seed", type=int, default=0)
    p2.add_argument("--selection_frac", type=float, default=0.5)
    p2.add_argument("--backend", default="qwen3")
    p2.add_argument("--domain_config", default=DOMAIN_CONFIG_PATH)
    p2.set_defaults(func=cmd_build_l2)

    p3 = sub.add_parser("eval-test")
    p3.add_argument("--manifest", required=True)
    p3.add_argument("--out", required=True)
    p3.add_argument("--variant", required=True,
                    choices=["anchor", "l1", "l2", "l1l2"])
    p3.add_argument("--l1_dir",
                    default="/hdd1/jiangxi/AD-Agent/benchmark/results/verbalized/v3_l1")
    p3.add_argument("--l2_dir",
                    default="/hdd1/jiangxi/AD-Agent/benchmark/results/verbalized/v3_l2")
    p3.add_argument("--domain_config", default=DOMAIN_CONFIG_PATH)
    p3.add_argument("--backend", default="qwen3")
    p3.add_argument("--max_turns", type=int, default=3)
    p3.add_argument("--workers", type=int, default=6)
    p3.add_argument("--top_k", type=int, default=3)
    p3.add_argument("--use_anchor", action="store_true", default=True)
    p3.add_argument("--no_anchor", dest="use_anchor", action="store_false")
    p3.set_defaults(func=cmd_eval_test)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
