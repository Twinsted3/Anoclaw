"""Verbalized Self-Evolution (§5 of paper).

Three-regime learning ladder over CrossDomainVAD-11:

  Passive v9       - training-free baseline (no rulebook); see agent_v9.
  L1  ref-only     - self-supervised; rulebook reflected from NORMAL
                     reference images only; zero oracle.
  L2  active       - semi-supervised; run passive v9 on dev, pick K=10
                     lowest-confidence items, reveal their labels from
                     the manifest, reflect into corrective rules.
  L1+L2 stacked    - concatenated rulebook (with dedup); oracle budget
                     is still K (L2 budget only).

Rulebook granularity: per-class for multi-class domains (D1,D2,D3,D4,
D5,D6), per-domain for single-class domains (D7..D12). The lookup key
is (domain_code, category) read from the manifest.

All test items are STRICTLY held out of the rulebook-construction
pipeline.  L2 only reveals labels for items whose split=='dev'.

Usage:

  # Stage 1: build L1 rulebook for one domain (0 oracle)
  python verbalized_learning.py build-l1 \
      --manifest benchmark/manifests_v2/D1_industrial_manifest.json \
      --out      benchmark/results/verbalized/D1_l1.json \
      --n_refs   8 --seed 0

  # Stage 2: build L2 corrective rules (K=10 oracle)
  python verbalized_learning.py build-l2 \
      --manifest benchmark/manifests_v2/D1_industrial_manifest.json \
      --passive_dev benchmark/results/verbalized/D1_passive_dev.json \
      --l1       benchmark/results/verbalized/D1_l1.json \
      --out      benchmark/results/verbalized/D1_l2.json \
      --k 10

  # Stage 3: evaluate on test with a rulebook
  python verbalized_learning.py eval-test \
      --manifest benchmark/manifests_v2/D1_industrial_manifest.json \
      --rulebook benchmark/results/verbalized/D1_l1l2.json \
      --out      benchmark/results/verbalized/D1_eval_l1l2.json
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


DOMAIN_FILES = {
    "D1": "D1_industrial_manifest.json",
    "D2": "D2_retail_manifest.json",
    "D3": "D3_complex_industrial_manifest.json",
    "D4": "D4_infrastructure_manifest.json",
    "D5": "D5_logical_manifest.json",
    "D6": "D6_industrial_3d_manifest.json",
    "D7": "D7_remote_sensing_manifest.json",
    "D8": "D8_dermatology_manifest.json",
    "D9": "D9_brain_mri_manifest.json",
    "D10": "D10_liver_ct_manifest.json",
    "D11": "D11_gi_endoscopy_manifest.json",
    "D12": "D12_road_safety_manifest.json",
}

MULTI_CLASS_DOMAINS = {"D1", "D2", "D3", "D4", "D5", "D6"}


# ---------------------------------------------------------------------------
# Rulebook granularity: group manifest items into (domain, class) buckets.
# ---------------------------------------------------------------------------

def group_units(manifest):
    """Return dict: unit_key -> list[items].

    unit_key is (domain_code, category) for multi-class domains,
    (domain_code,) for single-class domains.
    """
    groups = {}
    for it in manifest:
        d = it.get("domain_code")
        c = it.get("category")
        key = (d, c) if d in MULTI_CLASS_DOMAINS else (d,)
        groups.setdefault(key, []).append(it)
    return groups


def collect_unit_refs(items):
    """Collect unique ref image paths across items in a unit."""
    seen, refs = set(), []
    for it in items:
        for p in it.get("ref_paths", []) or []:
            if p not in seen:
                seen.add(p)
                refs.append(p)
    return refs


def unit_label(unit_key):
    """Human-readable unit name for prompts."""
    if len(unit_key) == 2:
        return f"{unit_key[0]} / {unit_key[1]}"
    return f"{unit_key[0]}"


# ---------------------------------------------------------------------------
# L1: ref-only reflector
# ---------------------------------------------------------------------------

L1_SYSTEM = (
    "You are a visual anomaly-detection expert. You will see several "
    "NORMAL reference images of a specific class, plus a task anchor "
    "stating what 'anomaly' means in this domain. Your job is to write "
    "a persistent natural-language rulebook that another agent will "
    "consult when it later sees a query image from the SAME class and "
    "must decide whether the query is anomalous. "
    "IMPORTANT: only list anomaly modes you are CONFIDENT about from "
    "(a) visible invariants in the refs that a violation would break, "
    "or (b) well-established failure patterns for this object class. "
    "If you do not have enough information to list specific anomaly "
    "modes for this class, return an empty hypothesized_anomaly_modes "
    "list rather than fabricating generic modes."
)

L1_USER_TEMPLATE = """Class: {unit_name}
Task anchor for this domain: {task_anchor}
Number of reference images: {n_refs}
All reference images shown below are NORMAL examples.

Emit a strict-JSON rulebook in EXACTLY this shape (no extra keys, no \
prose outside JSON):

{{
  "normal_signature": [
    "short phrase describing an invariant feature of the normal class",
    "..."
  ],
  "hypothesized_anomaly_modes": [
    "plausible defect grounded in either (a) a visible invariant in \
the refs that a violation would break, or (b) a well-known failure \
pattern for this object class",
    "..."
  ],
  "rules": [
    "if <visible predicate that is likely to indicate anomaly> then lean anomaly",
    "..."
  ],
  "confidence": "high | medium | low"
}}

Guidelines:
  - 3 to 6 items per list; be specific, not generic.
  - PREFER ref-grounded invariants (count, symmetry, structure) over \
guessed appearance rules. When the refs show e.g. "always exactly 3 \
fruits in the left compartment", that is a strong rule.
  - For anomaly_modes: ONLY list modes you would stake your reputation \
on. If the domain is outside your training experience (e.g. obscure \
medical imaging, specific satellite change types), return an empty \
list — the downstream agent will rely on its own reasoning rather \
than follow a fabricated checklist.
  - Do NOT write generic rules like "if the object looks damaged then \
lean anomaly" — those add noise.
  - Rules must be testable on a single image (no counterfactuals, no \
comparison to hypothetical states).
  - Set confidence="low" if you had to guess most of the anomaly \
modes; confidence="high" if the refs themselves grounded your rules.
  - Output JSON only; no markdown, no explanation.
"""


def build_l1_rulebook(unit_key, ref_paths, client, model, n_refs=8,
                      max_retries=3, task_anchor=""):
    """Ask a reflector VLM to emit a rulebook for one (domain, class) unit.

    Returns dict with keys: normal_signature, hypothesized_anomaly_modes,
    rules, confidence, plus meta fields (unit, n_refs_seen).

    Args:
      task_anchor: the domain task anchor string (from domain_config).
        Passed to the reflector so it writes rules aligned with what
        this benchmark considers anomalous — addresses the missing
        task-anchor problem diagnosed in v1 (agent on D7 treated
        building-change as "normal urbanisation" because refs alone
        didn't convey the task).
    """
    refs_used = ref_paths[:n_refs]
    parts = []
    for rp in refs_used:
        parts.append(img_msg(load_and_encode(rp)))
    parts.append(text_msg(L1_USER_TEMPLATE.format(
        unit_name=unit_label(unit_key), n_refs=len(refs_used),
        task_anchor=task_anchor or "(not provided)")))
    messages = [
        {"role": "system", "content": L1_SYSTEM},
        {"role": "user", "content": parts},
    ]
    for _ in range(max_retries):
        try:
            resp_text, _, _ = call_llm(client, model, messages, temperature=0.0)
            parsed = extract_json(resp_text)
            if (isinstance(parsed, dict)
                    and "normal_signature" in parsed
                    and "hypothesized_anomaly_modes" in parsed):
                parsed.setdefault("rules", [])
                return {
                    "unit": list(unit_key),
                    "n_refs_seen": len(refs_used),
                    "rulebook": parsed,
                }
        except Exception as e:  # pragma: no cover - log and retry
            print(f"[L1 reflect] retry after error: {e}", file=sys.stderr)
            time.sleep(1.0)
    raise RuntimeError(f"L1 reflector failed for {unit_key}")


# ---------------------------------------------------------------------------
# L2: active verbalized reflector (dev oracle + agent trajectory)
# ---------------------------------------------------------------------------

L2_SYSTEM = (
    "You are a visual anomaly-detection expert. A colleague agent just "
    "ran on a DEV image and was uncertain. The ground-truth label has "
    "been revealed to you. Your job is to propose ONE corrective rule "
    "that, if added to the agent's rulebook, would have prevented the "
    "mistake or reduced its uncertainty."
)

L2_USER_TEMPLATE = """DEV item: {item_id}
Class: {unit_name}
Task anchor: {task_anchor}
Agent predicted anomaly score: {score:.3f}  (0=normal, 1=anomaly)
GROUND-TRUTH label: {gt_name} (={gt_int})

Existing L1 rulebook for this class:
{l1_json}

Agent trajectory (condensed):
{trajectory}

Emit strict JSON, exactly ONE rule, of this shape:

{{
  "rule_type": "anomaly_mode_extension" | "normal_tolerance" | "rule",
  "text": "short actionable rule, <= 25 words, starts with a condition",
  "justification": "<= 40 words explaining why this rule would resolve \
THIS dev item AND generalises to other items of the same class",
  "confidence": "high | medium | low"
}}

Decision logic:
  - FN case (gt=1 anomaly, agent said normal):
      ALWAYS write "anomaly_mode_extension" — add a specific visible
      anomaly predicate that the agent missed.
  - FP case (gt=0 normal, agent said anomaly):
      DEFAULT to "rule" (neutral predicate); ONLY use "normal_tolerance"
      if BOTH (i) the feature the agent flagged appears in MULTIPLE
      normal refs, AND (ii) the rule can be phrased as a specific
      visual pattern to ignore (NOT a blanket "do not flag X").
      If unsure, write an "anomaly_mode_extension" that specifies what
      WOULD constitute a true anomaly of this type, so the agent can
      discriminate rather than blanket-ignore.
  - Borderline (agent score 0.4-0.6 regardless of gt): "rule".

HARD CONSTRAINTS:
  - "normal_tolerance" rules must name a SPECIFIC FEATURE (not a
    generic suppression). Bad: "do not classify as anomaly based on
    dark blotch". Good: "a central dark blotch with smooth border and
    uniform colour is normal for this class; flag only if border is
    jagged or colour is heterogeneous".
  - Do NOT restate the ground truth. Do NOT name the specific dev item.
  - Rules must GENERALISE to unseen items of the SAME class.
  - Output JSON only.
"""


def _compact_trajectory(v9_item_result, max_chars=800):
    """Render a v9 per-item result dict into a compact trajectory string."""
    r = v9_item_result
    parts = []
    if r.get("initial_score") is not None:
        parts.append(f"initial_score={r['initial_score']}")
    cf = r.get("candidate_features") or []
    if cf:
        parts.append("candidate_features=" + "; ".join(str(x) for x in cf[:5]))
    rv = r.get("refutation_verdicts") or []
    if rv:
        parts.append("refutation=" + "; ".join(
            f"t{v.get('turn')}:{v.get('verdict')}" for v in rv))
    rm = r.get("remaining_features") or []
    if rm:
        parts.append("remaining=" + "; ".join(str(x) for x in rm[:5]))
    tools = r.get("tools_used") or []
    if tools:
        parts.append("tools=" + ",".join(str(t) for t in tools[:5]))
    rat = r.get("rationale") or ""
    if rat:
        parts.append("rationale=" + rat[:300])
    s = "\n".join(parts)
    return s[:max_chars]


def build_l2_rulebook(unit_key, oracle_items, passive_results, l1_rulebook,
                      client, model, max_retries=3, use_l1_context=False,
                      task_anchor=""):
    """Build L2 corrective rules from K oracle dev items.

    Args:
      oracle_items: list of manifest items (dev split). Selection policy
        is decided upstream (see select_oracle_items_balanced).
      passive_results: list of v9 result dicts matching oracle_items 1:1.
      l1_rulebook: dict (may be empty). Only passed to the reflector when
        use_l1_context=True.
      task_anchor: domain task anchor string; helps reflector write rules
        aligned with the benchmark's definition of anomaly.

    Returns dict {unit, k, rules: [rule, ...]} — rules is a list of
    {rule_type, text, justification, confidence, from_item}.
    """
    if use_l1_context:
        l1_json = json.dumps(l1_rulebook.get("rulebook", {}), indent=2)
    else:
        l1_json = "(hidden — L2 is a dev-only regime; see §5.2 stacking paragraph)"
    out_rules = []
    for item, res in zip(oracle_items, passive_results):
        gt = int(item.get("label", 0))
        gt_name = "ANOMALY" if gt == 1 else "NORMAL"
        prompt = L2_USER_TEMPLATE.format(
            item_id=item["item_id"],
            unit_name=unit_label(unit_key),
            task_anchor=task_anchor or "(not provided)",
            score=float(res.get("score", 0.5)),
            gt_name=gt_name, gt_int=gt,
            l1_json=l1_json,
            trajectory=_compact_trajectory(res),
        )
        messages = [
            {"role": "system", "content": L2_SYSTEM},
            {"role": "user", "content": [
                img_msg(load_and_encode(item["query_path"])),
                text_msg(prompt),
            ]},
        ]
        for _ in range(max_retries):
            try:
                resp_text, _, _ = call_llm(client, model, messages,
                                            temperature=0.0)
                parsed = extract_json(resp_text)
                if (isinstance(parsed, dict)
                        and "rule_type" in parsed and "text" in parsed):
                    parsed["from_item"] = item["item_id"]
                    out_rules.append(parsed)
                    break
            except Exception as e:
                print(f"[L2 reflect] retry ({item['item_id']}): {e}",
                      file=sys.stderr)
                time.sleep(1.0)
    return {
        "unit": list(unit_key),
        "k": len(oracle_items),
        "rules": out_rules,
    }


# ---------------------------------------------------------------------------
# Rulebook stacking and injection
# ---------------------------------------------------------------------------

def stack_rulebook(l1, l2):
    """Merge L1 ref-only rulebook with L2 corrective rules.

    De-duplication is string-level on the ``rules`` list.
    """
    rb = dict(l1.get("rulebook", {})) if l1 else {}
    rb.setdefault("normal_signature", [])
    rb.setdefault("hypothesized_anomaly_modes", [])
    rb.setdefault("rules", [])

    for r in (l2 or {}).get("rules", []):
        text = r.get("text", "").strip()
        if not text:
            continue
        tagged = f"(corrective) {text}"
        if r.get("rule_type") == "anomaly_mode_extension":
            if text not in rb["hypothesized_anomaly_modes"]:
                rb["hypothesized_anomaly_modes"].append(text)
        elif r.get("rule_type") == "normal_tolerance":
            if text not in rb["normal_signature"]:
                rb["normal_signature"].append(text)
        if tagged not in rb["rules"]:
            rb["rules"].append(tagged)
    return rb


def rulebook_to_prompt(rb):
    """Render a rulebook dict as the DOMAIN RULEBOOK block injected into v9."""
    return (
        "DOMAIN RULEBOOK for this class (read before reasoning):\n"
        + json.dumps(rb, indent=2, ensure_ascii=False)
    )


# ---------------------------------------------------------------------------
# Oracle selection: lowest-confidence K dev items from a passive-v9 run
# ---------------------------------------------------------------------------

def split_dev_ids(dev_ids, seed, selection_frac=0.5):
    """Deterministic per-seed split of a domain's dev item IDs into
    selection vs validation subsets (50/50 by default).

    Args:
      dev_ids: iterable of item_id strings (all dev items in one domain).
      seed: int seed for the shuffle (identical per (domain, seed) pair).
      selection_frac: fraction that becomes the selection pool.

    Returns (selection_ids, validation_ids) — two sorted lists.
    """
    ids = sorted(dev_ids)  # deterministic starting order
    rng = random.Random(seed)
    shuffled = ids[:]
    rng.shuffle(shuffled)
    cut = int(round(len(shuffled) * selection_frac))
    sel = sorted(shuffled[:cut])
    val = sorted(shuffled[cut:])
    return sel, val


def select_oracle_items(passive_dev_results, manifest_by_id, k=10,
                        selection_ids=None):
    """[LEGACY] Pick the K dev items with smallest |score - 0.5|.

    Kept for back-compat. For new runs prefer
    select_oracle_items_balanced which forces K/2 FN + K/2 FP balance.
    """
    pool = passive_dev_results
    if selection_ids is not None:
        sel_set = set(selection_ids)
        pool = [r for r in pool if r["item_id"] in sel_set]
    ranked = sorted(
        pool,
        key=lambda r: abs(float(r.get("score", 0.5)) - 0.5),
    )
    chosen = ranked[:k]
    items = [manifest_by_id[r["item_id"]] for r in chosen]
    return items, chosen


def select_oracle_items_balanced(passive_dev_results, manifest_by_id, k=10,
                                 selection_ids=None):
    """Pick K dev items balanced K/2 FN + K/2 FP (or closest available).

    Why: the uncertainty-only selection (lowest |s-0.5|) in v1 tended to
    over-sample one side (the side the model happened to be confused
    about), biasing the L2 reflector toward producing many
    "normal_tolerance" rules. Balancing FN/FP gives the reflector
    roughly equal error cases of both signs, which stabilises the
    rule-type distribution.

    Definitions:
      FN = gt=1 (anomaly) AND score<0.5 (agent said normal → missed)
      FP = gt=0 (normal)  AND score>=0.5 (agent said anomaly → false alarm)
      TN = gt=0 AND score<0.5 (not an error; not useful for reflection)
      TP = gt=1 AND score>=0.5 (not an error; not useful for reflection)

    Selection (within selection_ids):
      1. Rank FN candidates by |score-0.5| ascending (closest to
         flipping) — prefer high-ambiguity misses.
      2. Rank FP candidates the same way.
      3. Take ceil(k/2) FN + floor(k/2) FP; if one side is short,
         fill from the other side's nearest-to-0.5 TN/TP.

    Returns (oracle_items, oracle_results) 1:1 aligned, length <= k.
    """
    pool = passive_dev_results
    if selection_ids is not None:
        sel_set = set(selection_ids)
        pool = [r for r in pool if r["item_id"] in sel_set]

    def label(r):
        return int(manifest_by_id[r["item_id"]].get("label", 0))

    fn = [r for r in pool
          if label(r) == 1 and float(r.get("score", 0.5)) < 0.5]
    fp = [r for r in pool
          if label(r) == 0 and float(r.get("score", 0.5)) >= 0.5]
    tn = [r for r in pool
          if label(r) == 0 and float(r.get("score", 0.5)) < 0.5]
    tp = [r for r in pool
          if label(r) == 1 and float(r.get("score", 0.5)) >= 0.5]

    key = lambda r: abs(float(r.get("score", 0.5)) - 0.5)
    fn.sort(key=key); fp.sort(key=key); tn.sort(key=lambda r: -key(r)); tp.sort(key=lambda r: -key(r))

    k_fn = (k + 1) // 2   # ceil
    k_fp = k // 2          # floor
    picks_fn = fn[:k_fn]
    picks_fp = fp[:k_fp]
    # Fill shortfalls: prefer near-boundary TN/TP of the under-filled side.
    short_fn = k_fn - len(picks_fn)
    short_fp = k_fp - len(picks_fp)
    if short_fn > 0:
        # borrow from FP high-confidence first, then TP near boundary
        picks_fp += fp[k_fp:k_fp+short_fn]
        picks_fn += tp[:short_fn-len(fp[k_fp:k_fp+short_fn])]
    if short_fp > 0:
        picks_fn += fn[k_fn:k_fn+short_fp]
        picks_fp += tn[:short_fp-len(fn[k_fn:k_fn+short_fp])]

    chosen = (picks_fn + picks_fp)[:k]
    items = [manifest_by_id[r["item_id"]] for r in chosen]
    return items, chosen


def per_class_coverage(selected_items):
    """Return dict: category -> count, for reporting §5.3 coverage."""
    cov = {}
    for it in selected_items:
        c = it.get("category", "?")
        cov[c] = cov.get(c, 0) + 1
    return cov


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False))


def read_json(path):
    return json.loads(Path(path).read_text())


# ---------------------------------------------------------------------------
# CLI: three subcommands (build-l1 / build-l2 / eval-test)
# ---------------------------------------------------------------------------

def _load_task_anchor(domain_code, domain_config_path):
    """Compose task anchor string from domain_config.json entry."""
    if not domain_config_path or not os.path.exists(domain_config_path):
        return ""
    dc = json.load(open(domain_config_path))
    d = dc.get(domain_code, {}) or {}
    name = d.get("name", domain_code)
    at = d.get("anomaly_type", "anomaly")
    desc = d.get("description", "")
    return f"Detect {at} anomalies in {name}. {desc}".strip()


def cmd_build_l1(args):
    manifest = read_json(args.manifest)
    client = get_client(args.backend)
    model = get_model_name(args.backend)
    groups = group_units(manifest)

    out = {"domain": None, "units": []}
    for unit_key, items in groups.items():
        out["domain"] = unit_key[0]
        refs = collect_unit_refs(items)
        if args.seed is not None:
            rng = random.Random(args.seed)
            rng.shuffle(refs)
        anchor = _load_task_anchor(unit_key[0], args.domain_config)
        rb = build_l1_rulebook(unit_key, refs, client, model,
                               n_refs=args.n_refs, task_anchor=anchor)
        out["units"].append(rb)
        rl = rb['rulebook']
        print(f"[L1] {unit_key}: rules={len(rl.get('rules', []))}, "
              f"modes={len(rl.get('hypothesized_anomaly_modes', []))}, "
              f"conf={rl.get('confidence','?')}")
    write_json(args.out, out)
    print(f"[L1] wrote {args.out}")


def cmd_build_l2(args):
    manifest = read_json(args.manifest)
    passive = read_json(args.passive_dev)  # list of V9Result-as-dict
    l1 = read_json(args.l1) if args.l1 else {"units": []}
    manifest_by_id = {it["item_id"]: it for it in manifest}
    groups = group_units(manifest)
    l1_by_unit = {tuple(u["unit"]): u for u in l1.get("units", [])}

    # Dev pre-split (per §5.3): 20 selection (oracle pool) + 20 validation
    # (untouched holdout). Deterministic per (domain, seed).
    dev_items = [it for it in manifest if it.get("split") == "dev"]
    domain_code = dev_items[0]["domain_code"] if dev_items else "?"
    selection_ids, validation_ids = split_dev_ids(
        [it["item_id"] for it in dev_items], seed=args.seed,
        selection_frac=args.selection_frac)
    print(f"[L2] {domain_code} seed={args.seed}: "
          f"selection={len(selection_ids)}, validation={len(validation_ids)}")

    passive_dev = {r["item_id"]: r for r in passive
                   if r["item_id"] in {it["item_id"] for it in dev_items}}

    client = get_client(args.backend)
    model = get_model_name(args.backend)

    out = {
        "domain": domain_code,
        "seed": args.seed,
        "k": args.k,
        "use_l1_context": args.use_l1_context,
        "selection_frac": args.selection_frac,
        "selection_ids": selection_ids,
        "validation_ids": validation_ids,
        "units": [],
        "coverage": {},
    }
    for unit_key, items in groups.items():
        unit_dev = [it for it in items if it.get("split") == "dev"]
        unit_ids = {it["item_id"] for it in unit_dev}
        unit_passive = [passive_dev[i] for i in unit_ids if i in passive_dev]
        if not unit_passive:
            print(f"[L2] {unit_key}: no passive-dev results, skip")
            continue
        if args.balanced:
            oracle_items, oracle_results = select_oracle_items_balanced(
                unit_passive, manifest_by_id, k=args.k,
                selection_ids=selection_ids)
        else:
            oracle_items, oracle_results = select_oracle_items(
                unit_passive, manifest_by_id, k=args.k,
                selection_ids=selection_ids)
        if not oracle_items:
            print(f"[L2] {unit_key}: empty oracle pool after selection filter, skip")
            continue
        l1_rb = l1_by_unit.get(unit_key, {"rulebook": {}})
        anchor = _load_task_anchor(unit_key[0], args.domain_config)
        rb = build_l2_rulebook(unit_key, oracle_items, oracle_results,
                               l1_rb, client, model,
                               use_l1_context=args.use_l1_context,
                               task_anchor=anchor)
        out["units"].append(rb)
        cov = per_class_coverage(oracle_items)
        out["coverage"][" / ".join(unit_key)] = cov
        print(f"[L2] {unit_key}: k={rb['k']}, new_rules={len(rb['rules'])}, "
              f"class_cov={cov}")
    write_json(args.out, out)
    print(f"[L2] wrote {args.out}")


def cmd_stack(args):
    l1 = read_json(args.l1)
    l2 = read_json(args.l2)
    l1_by = {tuple(u["unit"]): u for u in l1.get("units", [])}
    l2_by = {tuple(u["unit"]): u for u in l2.get("units", [])}
    out = {"domain": l1.get("domain") or l2.get("domain"), "units": []}
    for key in sorted(set(l1_by) | set(l2_by)):
        rb = stack_rulebook(l1_by.get(key, {}), l2_by.get(key, {}))
        out["units"].append({"unit": list(key), "rulebook": rb})
    write_json(args.out, out)
    print(f"[stack] wrote {args.out}: {len(out['units'])} units")


def _l2_unit_to_rulebook(l2_unit):
    """Convert an L2 unit (dev-oracle corrective rules) into rulebook shape.

    L2 unit has {unit, k, rules: [{rule_type, text, justification, from_item}]};
    we reshape into {normal_signature, hypothesized_anomaly_modes, rules}
    so cmd_eval_test can treat L1/L2/stack uniformly.
    """
    rb = {"normal_signature": [], "hypothesized_anomaly_modes": [],
          "rules": []}
    for r in l2_unit.get("rules", []):
        text = r.get("text", "").strip()
        if not text:
            continue
        tagged = f"(corrective) {text}"
        if r.get("rule_type") == "anomaly_mode_extension":
            rb["hypothesized_anomaly_modes"].append(text)
        elif r.get("rule_type") == "normal_tolerance":
            rb["normal_signature"].append(text)
        rb["rules"].append(tagged)
    return rb


def cmd_eval_test(args):
    """Run v9 on test items with a pre-built rulebook injected.

    The rulebook is looked up by (domain_code, category).  Rulebook
    string is injected via the `rulebook` kwarg of v9_mod.run_v9_item
    (see patch to agent_v9.py).

    Shape handling: L1 and stack(L1+L2) files have per-unit "rulebook"
    dicts natively; L2 files have per-unit "rules" lists (corrective
    rules tagged by rule_type). We auto-detect and reshape L2 via
    _l2_unit_to_rulebook so all three variants share one eval code
    path.
    """
    manifest = read_json(args.manifest)
    rulebook_file = read_json(args.rulebook)
    rb_by_unit = {}
    for u in rulebook_file.get("units", []):
        key = tuple(u["unit"])
        if "rulebook" in u:
            rb_by_unit[key] = u["rulebook"]
        elif "rules" in u:
            rb_by_unit[key] = _l2_unit_to_rulebook(u)
    test_items = [it for it in manifest if it.get("split") == "test"]

    client = get_client(args.backend)
    model = get_model_name(args.backend)

    results = []
    def _run_one(it):
        d = it.get("domain_code")
        c = it.get("category")
        key = (d, c) if d in MULTI_CLASS_DOMAINS else (d,)
        rb = rb_by_unit.get(key) or {}
        rulebook_str = rulebook_to_prompt(rb) if rb else None
        return v9_mod.run_v9_item(
            client, model, it, split="test",
            max_turns=args.max_turns,
            rulebook=rulebook_str,  # NEW kwarg; see agent_v9 patch
        )

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        fut = {ex.submit(_run_one, it): it for it in test_items}
        for f in as_completed(fut):
            it = fut[f]
            try:
                r = f.result()
                results.append({
                    "item_id": r.item_id,
                    "score": r.score,
                    "mode": r.mode,
                    "rationale": r.rationale,
                    "label": it.get("label"),
                    "domain_code": it.get("domain_code"),
                    "category": it.get("category"),
                })
            except Exception as e:
                print(f"[eval] {it['item_id']} failed: {e}", file=sys.stderr)
    write_json(args.out, results)
    print(f"[eval-test] wrote {args.out}: {len(results)} items")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_l1 = sub.add_parser("build-l1")
    ap_l1.add_argument("--manifest", required=True)
    ap_l1.add_argument("--out", required=True)
    ap_l1.add_argument("--n_refs", type=int, default=8)
    ap_l1.add_argument("--seed", type=int, default=0)
    ap_l1.add_argument("--backend", default="qwen3")
    ap_l1.add_argument("--domain_config",
                       default="/hdd1/jiangxi/AD-Agent/benchmark/manifests_v2/domain_config.json",
                       help="Path to domain_config.json for task anchor.")
    ap_l1.set_defaults(func=cmd_build_l1)

    ap_l2 = sub.add_parser("build-l2")
    ap_l2.add_argument("--manifest", required=True)
    ap_l2.add_argument("--passive_dev", required=True,
                       help="JSON array of v9 per-item results on dev.")
    ap_l2.add_argument("--l1", default=None,
                       help="Only used when --use_l1_context is set.")
    ap_l2.add_argument("--out", required=True)
    ap_l2.add_argument("--k", type=int, default=10)
    ap_l2.add_argument("--seed", type=int, default=0,
                       help="Deterministic dev selection/validation split.")
    ap_l2.add_argument("--selection_frac", type=float, default=0.5,
                       help="Fraction of dev used as oracle selection pool. "
                            "0.5 gives 20/20 split on a 40-item dev.")
    ap_l2.add_argument("--use_l1_context", action="store_true",
                       help="Pass L1 rulebook to the L2 reflector (ablation "
                            "only). Main +L2 row uses default (False).")
    ap_l2.add_argument("--balanced", action="store_true", default=True,
                       help="Balanced FN/FP oracle selection (default ON in "
                            "v2 rebuild). Pass --no-balanced for legacy.")
    ap_l2.add_argument("--no-balanced", dest="balanced",
                       action="store_false",
                       help="Fall back to legacy lowest-confidence ranking.")
    ap_l2.add_argument("--domain_config",
                       default="/hdd1/jiangxi/AD-Agent/benchmark/manifests_v2/domain_config.json",
                       help="Path to domain_config.json for task anchor.")
    ap_l2.add_argument("--backend", default="qwen3")
    ap_l2.set_defaults(func=cmd_build_l2)

    ap_st = sub.add_parser("stack")
    ap_st.add_argument("--l1", required=True)
    ap_st.add_argument("--l2", required=True)
    ap_st.add_argument("--out", required=True)
    ap_st.set_defaults(func=cmd_stack)

    ap_ev = sub.add_parser("eval-test")
    ap_ev.add_argument("--manifest", required=True)
    ap_ev.add_argument("--rulebook", required=True)
    ap_ev.add_argument("--out", required=True)
    ap_ev.add_argument("--backend", default="qwen3")
    ap_ev.add_argument("--max_turns", type=int, default=3)
    ap_ev.add_argument("--workers", type=int, default=3)
    ap_ev.set_defaults(func=cmd_eval_test)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
