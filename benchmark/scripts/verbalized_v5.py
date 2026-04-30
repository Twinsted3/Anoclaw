"""Verbalized Self-Evolution v5 — wraps the §4 v12 ensemble.

Delta vs verbalized_v3:
  - Calls agent_v12.run_v12_item (parallel Direct + v9 refutation, alpha=0.5)
    instead of agent_v9.run_v9_item.
  - Rulebook payload is injected into the refutation branch only via the
    new refutation_rulebook= keyword (Direct branch is unchanged).
  - Baseline is v12 Passive (learning_enabled=False, no rulebook).

L1 / L2 rulebook construction is unchanged (we re-use v3's rule store).
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import agent_v12 as v12_mod  # noqa: E402
from infer import get_client, get_model_name  # noqa: E402
from verbalized_v3 import (  # noqa: E402
    DOMAIN_CONFIG_PATH, build_rule_store_v3, compose_anchor,
    compose_user_rules_block_v3, load_domain_config, retrieve_rules_v3,
)


def _read_json(p): return json.loads(Path(p).read_text())


def _write_json(p, o):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(o, indent=2, ensure_ascii=False))


def cmd_eval_test(args):
    manifest = _read_json(args.manifest)
    test_items = [it for it in manifest if it.get("split") == "test"]
    store = build_rule_store_v3(args.l1_dir, args.l2_dir)
    client = get_client(args.backend)
    model = get_model_name(args.backend)
    dc = load_domain_config(args.domain_config) if args.domain_config else {}

    src_map = {
        "passive": "passive",
        "anchor": None,
        "l1":     {"L1"},
        "l2":     {"L2"},
        "l1l2":   None,
    }
    if args.variant not in src_map:
        raise ValueError(args.variant)
    sources = src_map[args.variant]

    if args.variant == "passive":
        inject_rules = False
        use_anchor = False
    elif args.variant == "anchor":
        inject_rules = False
        use_anchor = True
    else:
        inject_rules = True
        use_anchor = True

    # Resume support
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prev = []
    done_ids = set()
    if args.resume and out_path.exists():
        try:
            prev = json.load(open(out_path))
            done_ids = {r["item_id"] for r in prev if r.get("error") is None}
            print(f"[resume] {len(done_ids)} already done", file=sys.stderr)
        except Exception:
            prev, done_ids = [], set()
    pending = [it for it in test_items if it["item_id"] not in done_ids]

    def _compose(it):
        d = it.get("domain_code"); c = it.get("category")
        anchor = compose_anchor(dc, d) if use_anchor else None
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
        r = v12_mod.run_v12_item(
            client, model, it, split="test",
            max_turns=args.max_turns,
            w_direct=args.w_direct, w_v9=args.w_v9,
            learning_enabled=False, rulebook_dir=None,
            refutation_rulebook=payload,
        )
        return r, rules

    results = list(prev)
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        fut = {ex.submit(_run_one, it): it for it in pending}
        n_done = 0
        for f in as_completed(fut):
            it = fut[f]
            try:
                r, rules = f.result()
                results.append({
                    "item_id": r.get("item_id"),
                    "domain_code": r.get("domain_code"),
                    "label_gt": it.get("label"),
                    "category": it.get("category"),
                    "anomaly_score": r.get("anomaly_score"),
                    "direct_score": r.get("direct_score"),
                    "v9_score": r.get("v9_score"),
                    "v9_initial_score": r.get("v9_initial_score"),
                    "v9_updated_score": r.get("v9_updated_score"),
                    "mode": r.get("mode"),
                    "rationale": (r.get("rationale") or "")[:500],
                    "tools_used": r.get("tools_used"),
                    "n_turns": r.get("n_turns"),
                    "n_rules_injected": len(rules),
                    "rule_types": [x["type"] for x in rules],
                    "error": r.get("error"),
                })
            except Exception as e:
                print(f"[eval v5] {it['item_id']} failed: {e}",
                      file=sys.stderr)
                results.append({"item_id": it["item_id"],
                                "label_gt": it.get("label"),
                                "anomaly_score": None,
                                "error": f"{type(e).__name__}: {e}"})
            n_done += 1
            if n_done % 10 == 0:
                _write_json(out_path, results)
    _write_json(out_path, results)
    print(f"[eval v5] wrote {out_path} ({len(results)} items)")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("eval-test")
    p.add_argument("--manifest", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--variant", required=True,
                   choices=["passive", "anchor", "l1", "l2", "l1l2"])
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
    p.add_argument("--resume", action="store_true")
    p.set_defaults(func=cmd_eval_test)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
