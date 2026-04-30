"""Verbalized v6 — rules in BOTH Direct and refutation branches.

Motivation: under v12 ensemble alpha=0.5, the refutation Δ from v3
(+2-3 pp) is halved at the ensemble level (~+1-1.5 pp), insufficient to
hit the +3 pp target. To recover the lost gain we inject the same RAG
rule payload into the Direct branch's prompt as well, so both branches
benefit from the rulebook before they are blended.

Design:
  - Direct branch: replicate run_v0() but inject `rule_text` between the
    query image and the JSON-output instruction. This is the single
    minimal change vs the §4 main Direct call.
  - Refutation branch: unchanged from verbalized_v5 (rule_text passed
    via _run_v9_agent_v12's `rulebook` arg).
  - Final score = 0.5 * direct_with_rules + 0.5 * refut_with_rules.

The rulebook construction (L1/L2 stores) is identical to v3, so we
re-use the existing v3_l1/ and v3_l2/ artefacts.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import agent_v12 as v12_mod  # noqa: E402
from agent_v12 import _run_v9_agent_v12, _OBS_IMAGE_KEYS  # noqa: E402
import agent_v9 as _v9  # noqa: E402
from infer import (  # noqa: E402
    N_REFS, build_prompt_v0, call_llm, extract_json, get_client,
    get_model_name, img_msg, label_from_score, load_and_encode,
    score_from_v0, text_msg,
)
from verbalized_v3 import (  # noqa: E402
    DOMAIN_CONFIG_PATH, build_rule_store_v3, compose_anchor,
    compose_user_rules_block_v3, load_domain_config, retrieve_rules_v3,
)


# ---------------------------------------------------------------------------
# Direct + rules
# ---------------------------------------------------------------------------

def run_v0_with_rules(client, model, item, rule_text: str | None,
                     max_tokens: int = 700) -> dict:
    """run_v0 variant: identical content layout but with rule_text
    inserted right after the query image, BEFORE the JSON-output prompt."""
    ref_imgs = [load_and_encode(p) for p in item["ref_paths"][:N_REFS]]
    query_img = load_and_encode(item["query_path"])
    domain_code = item["domain_code"]
    prompt = build_prompt_v0(domain_code, bool(ref_imgs))

    content = []
    for b64 in ref_imgs:
        content.append(text_msg("Normal reference:"))
        content.append(img_msg(b64))
    content.append(text_msg("Query image:"))
    content.append(img_msg(query_img))
    if rule_text and rule_text.strip():
        content.append(text_msg(rule_text.strip()))
    content.append(text_msg(prompt))

    t0 = time.time()
    text, inp, out = call_llm(client, model,
                              [{"role": "user", "content": content}],
                              max_tokens)
    latency = time.time() - t0

    parsed = extract_json(text)
    score = score_from_v0(parsed)
    anomaly_type = parsed.get("anomaly_type") if parsed else None

    return {
        "label_pred": label_from_score(score),
        "anomaly_score": score,
        "anomaly_type_pred": anomaly_type,
        "raw_output": {"v0": parsed},
        "cost_tokens": {"input": inp, "output": out},
        "latency_sec": round(latency, 2),
    }


def _direct_with_rules_blocking(client, model, item, rule_text, out):
    try:
        out["result"] = run_v0_with_rules(client, model, item, rule_text)
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
# v6 item runner
# ---------------------------------------------------------------------------

def run_v6_item(client, model, item, split, max_turns,
                w_direct=0.5, w_v9=0.5,
                direct_rule_text: str | None = None,
                refutation_rulebook: str | None = None):
    """Parallel Direct-with-rules + v9-with-rules; fixed-weight blend."""
    direct_holder = {"result": None, "error": None}
    direct_thread = threading.Thread(
        target=_direct_with_rules_blocking,
        args=(client, model, item, direct_rule_text, direct_holder),
        daemon=True,
    )
    direct_thread.start()

    try:
        v9 = _run_v9_agent_v12(client, model, item, split, max_turns,
                               rulebook=refutation_rulebook)
        v9_error = v9.error
    except Exception as e:
        v9 = None
        v9_error = f"{type(e).__name__}: {e}"

    direct_thread.join()
    direct_result = direct_holder["result"]
    direct_error = direct_holder["error"]

    base = {
        "item_id": item.get("item_id"),
        "domain_code": item.get("domain_code"),
        "label_gt": item.get("label"),
        "category": item.get("category"),
        "anomaly_score": None,
        "direct_score": None,
        "v9_score": None,
        "mode": None,
        "rationale": "",
        "n_turns": 0,
        "tools_used": [],
        "error": v9_error,
        "direct_error": direct_error,
        "w_direct": w_direct,
        "w_v9": w_v9,
    }

    if v9 is None:
        fallback_score = (direct_result or {}).get("anomaly_score")
        base["anomaly_score"] = fallback_score
        base["direct_score"] = fallback_score
        base["error"] = f"v9_failed: {v9_error}"
        return base

    base.update({
        "mode": v9.mode,
        "v9_score": v9.score,
        "rationale": v9.rationale,
        "n_turns": v9.n_turns,
        "tools_used": v9.tools_used,
    })

    direct_score = (direct_result or {}).get("anomaly_score")
    base["direct_score"] = direct_score

    agent_decided_ad = (v9.mode == "anomaly_detection")
    if agent_decided_ad and direct_score is not None and v9.score is not None:
        blend = max(0.0, min(1.0, w_direct * direct_score + w_v9 * v9.score))
    elif v9.score is not None:
        blend = v9.score
    else:
        blend = direct_score
    base["anomaly_score"] = blend
    return base


# ---------------------------------------------------------------------------
# Eval driver
# ---------------------------------------------------------------------------

def _read_json(p): return json.loads(Path(p).read_text())


def _write_json(p, o):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(o, indent=2, ensure_ascii=False))


def cmd_eval_test(args):
    manifest = _read_json(args.manifest)
    items = [it for it in manifest if it.get("split") == args.split]
    store = build_rule_store_v3(args.l1_dir, args.l2_dir)
    client = get_client(args.backend)
    model = get_model_name(args.backend)
    dc = load_domain_config(args.domain_config) if args.domain_config else {}

    src_map = {
        "passive": ("none", False, None),
        "anchor":  ("none", True,  None),
        "l1":      ("rules", True, {"L1"}),
        "l2":      ("rules", True, {"L2"}),
        "l1l2":    ("rules", True, None),
    }
    if args.variant not in src_map:
        raise ValueError(args.variant)
    rule_mode, use_anchor, sources = src_map[args.variant]

    out_path = Path(args.out)
    prev = []
    done_ids = set()
    if args.resume and out_path.exists():
        try:
            prev = json.load(open(out_path))
            done_ids = {r["item_id"] for r in prev if r.get("error") is None}
        except Exception:
            prev, done_ids = [], set()
    pending = [it for it in items if it["item_id"] not in done_ids]

    def _compose(it):
        d = it.get("domain_code"); c = it.get("category")
        anchor = compose_anchor(dc, d) if use_anchor else None
        if rule_mode == "rules":
            rules = retrieve_rules_v3(store, d, c, k=args.top_k,
                                      sources=sources,
                                      require_invariant=(args.variant == "l1l2"))
        else:
            rules = []
        block = compose_user_rules_block_v3(rules)
        parts = []
        if anchor: parts.append(f"TASK CONTEXT\n{anchor}")
        if block:  parts.append(block)
        return ("\n\n".join(parts) if parts else None), rules

    def _run_one(it):
        payload, rules = _compose(it)
        # Direct gets the same payload as refutation (or the trimmed
        # version below if we want a lighter Direct context).
        direct_text = payload if args.direct_rules else None
        r = run_v6_item(
            client, model, it, split=args.split,
            max_turns=args.max_turns,
            w_direct=args.w_direct, w_v9=args.w_v9,
            direct_rule_text=direct_text,
            refutation_rulebook=payload if args.refut_rules else None,
        )
        return r, rules

    results = list(prev)
    n_done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        fut = {ex.submit(_run_one, it): it for it in pending}
        for f in as_completed(fut):
            it = fut[f]
            try:
                r, rules = f.result()
                results.append({**r,
                                "n_rules_injected": len(rules),
                                "rule_types": [x["type"] for x in rules]})
            except Exception as e:
                print(f"[v6] {it['item_id']} failed: {e}", file=sys.stderr)
                results.append({"item_id": it["item_id"],
                                "label_gt": it.get("label"),
                                "anomaly_score": None,
                                "error": f"{type(e).__name__}: {e}"})
            n_done += 1
            if n_done % 10 == 0:
                _write_json(out_path, results)
    _write_json(out_path, results)
    print(f"[v6 {args.variant}] wrote {out_path} ({len(results)} items)")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("eval")
    p.add_argument("--manifest", required=True)
    p.add_argument("--split", default="test", choices=["dev","test"])
    p.add_argument("--out", required=True)
    p.add_argument("--variant", required=True,
                   choices=["passive","anchor","l1","l2","l1l2"])
    p.add_argument("--l1_dir",
                   default="/hdd1/jiangxi/AD-Agent/benchmark/results/verbalized/v3_l1")
    p.add_argument("--l2_dir",
                   default="/hdd1/jiangxi/AD-Agent/benchmark/results/verbalized/v3_l2")
    p.add_argument("--domain_config", default=DOMAIN_CONFIG_PATH)
    p.add_argument("--backend", default="qwen3")
    p.add_argument("--max_turns", type=int, default=3)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--top_k", type=int, default=3)
    p.add_argument("--w_direct", type=float, default=0.5)
    p.add_argument("--w_v9", type=float, default=0.5)
    p.add_argument("--direct_rules", action="store_true",
                   help="Inject rule payload into Direct branch's prompt.")
    p.add_argument("--no_direct_rules", dest="direct_rules",
                   action="store_false")
    p.set_defaults(direct_rules=True)
    p.add_argument("--refut_rules", action="store_true",
                   help="Inject rule payload into refutation branch.")
    p.add_argument("--no_refut_rules", dest="refut_rules",
                   action="store_false")
    p.set_defaults(refut_rules=True)
    p.add_argument("--resume", action="store_true")
    p.set_defaults(func=cmd_eval_test)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
