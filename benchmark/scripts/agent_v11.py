"""AnomalyClaw v11 — v10 architecture + optional controller-level verbalized learning.

Architecture:
  learning_enabled=False (default):
    Behavior identical to v10: run v9 agent + Direct v0 in parallel threads,
    final anomaly_score = w_direct * direct_score + w_v9 * v9_score (default
    0.5/0.5). This is the Table 1 Qwen3.5 baseline (0.732).

  learning_enabled=True:
    After both branches finish, a Controller VLM sees the image, refs, both
    branch outputs (score + rationale), and a per-domain rulebook (meta-rules
    about which branch to trust when + domain knowledge). Controller returns
    the final anomaly_score. On controller failure the item falls back to the
    fixed-weight v10 blend.

Rulebook scope:
  Rules are injected ONLY at the controller; the v9 and Direct branches run
  unchanged. This keeps the Passive-v11 == v10 guarantee clean and localizes
  verbalized learning at the arbitration layer.

Rulebook file format (per-domain JSON at ``{rulebook_dir}/{domain_code}.json``):
  {
    "meta":   ["when both disagree and X ...", ...],   # routing rules
    "domain": ["normal refs show N holes per row ...", ...]  # domain knowledge
  }
  A legacy ``{"rules": [...]}`` flat list is also accepted.

CLI mirrors agent_v10.py plus ``--learning_enabled``, ``--rulebook_dir``,
``--controller_max_tokens``.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent_v9 import run_v9_item  # noqa: E402
from infer import (  # noqa: E402
    call_llm, extract_json, get_client, get_model_name,
    img_msg, load_and_encode, run_v0, text_msg,
)

N_REFS = 2


CONTROLLER_SYSTEM = (
    "You are the arbitrator for a two-branch visual anomaly detection ensemble.\n"
    "Branch A (Agent) analyzed the query image via multi-turn reasoning with tool use.\n"
    "Branch B (Direct) made a single-pass judgment with no tools.\n"
    "Given both branch outputs and any applicable rules, decide the final anomaly score.\n"
    "Higher score (closer to 1.0) means more likely anomalous; lower (closer to 0.0) means normal.\n"
    "0.5 means equally uncertain. Avoid exact 0.0 or 1.0."
)

CONTROLLER_USER_TEMPLATE = (
    "[APPLICABLE RULES]\n"
    "{rules}\n\n"
    "[BRANCH A — Agent]\n"
    "Score: {a_score:.3f}\n"
    "Rationale: {a_rationale}\n\n"
    "[BRANCH B — Direct]\n"
    "Score: {b_score:.3f}\n"
    "Rationale: {b_rationale}\n\n"
    "Decide the final anomaly score. Return JSON only:\n"
    "{{\n"
    "  \"final_score\": <float in [0,1]>,\n"
    "  \"trust\": \"A\" | \"B\" | \"blend\",\n"
    "  \"reasoning\": \"<one short sentence>\"\n"
    "}}"
)


def _direct_blocking(client, model, item, out):
    try:
        out["result"] = run_v0(client, model, item)
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"


@lru_cache(maxsize=256)
def _retrieve_rules_cached(rulebook_dir: str, domain_code: str,
                           category: str, max_meta: int,
                           max_domain: int) -> str:
    """RAG retrieval wrapper around ``verbalized_v4.retrieve_rules_v4``.

    Cached by (rulebook_dir, domain_code, category, max_meta, max_domain) so
    each (domain, category) pair pays one filter pass, not one per item.
    Empty string if the rulebook is missing or has nothing applicable.
    """
    if not rulebook_dir:
        return ""
    # Lazy import to avoid a hard dependency when learning_enabled=False.
    from verbalized_v4 import retrieve_rules_v4  # noqa: E402
    rb_path = str(Path(rulebook_dir) / f"{domain_code}.json")
    return retrieve_rules_v4(rb_path, domain_code, category or None,
                             max_meta=max_meta, max_domain=max_domain)


def _direct_rationale(direct_out: dict) -> str:
    """Extract a short rationale string from a run_v0 result."""
    raw = (direct_out.get("raw_output") or {}).get("v0") or {}
    txt = raw.get("rationale") or raw.get("explanation") or ""
    if not txt:
        # Fall back to serialized JSON without images.
        txt = json.dumps({k: v for k, v in raw.items() if k != "images"})
    return txt[:600]


def _controller_arbitrate(client, model, item, v9_score, v9_rationale,
                          direct_score, direct_rationale, rules_text,
                          max_tokens=400):
    """Call controller VLM to decide final score.

    Returns (score: float|None, meta: dict). If ``score`` is None the caller
    must fall back (e.g., to the fixed-weight blend).
    """
    query_path = item["query_path"]
    ref_paths = item.get("ref_paths", [])[:N_REFS]

    user_text = CONTROLLER_USER_TEMPLATE.format(
        rules=rules_text or "(none)",
        a_score=float(v9_score),
        a_rationale=(v9_rationale or "")[:600],
        b_score=float(direct_score),
        b_rationale=(direct_rationale or "")[:600],
    )

    content = []
    for rp in ref_paths:
        content.append(text_msg("Normal reference:"))
        content.append(img_msg(load_and_encode(rp)))
    content.append(text_msg("Query image:"))
    content.append(img_msg(load_and_encode(query_path)))
    content.append(text_msg(user_text))

    messages = [
        {"role": "system", "content": CONTROLLER_SYSTEM},
        {"role": "user", "content": content},
    ]

    try:
        text, inp, out = call_llm(client, model, messages, max_tokens=max_tokens)
    except Exception as e:
        return None, {"error": f"{type(e).__name__}: {e}"}

    parsed = extract_json(text)
    if not parsed:
        return None, {"error": "parse_failed", "raw": text[:200]}
    s = parsed.get("final_score")
    if not isinstance(s, (int, float)):
        return None, {"error": "no_score_field", "parsed": parsed}
    s = max(0.0, min(1.0, float(s)))
    return s, {
        "trust": parsed.get("trust"),
        "reasoning": parsed.get("reasoning"),
        "tokens": {"input": inp, "output": out},
    }


def run_v11_item(client, model, item, split, max_turns,
                 question=None, options=None,
                 w_direct=0.5, w_v9=0.5,
                 learning_enabled=False, rulebook_dir=None,
                 controller_max_tokens=400,
                 controller_client=None, controller_model=None):
    """Run v11 on a single item.

    When ``learning_enabled=False``, returns the same score a v10 runner would.
    When ``learning_enabled=True`` and the item is AD-mode with both branch
    outputs present, the controller VLM arbitrates.
    """
    is_ad_expected = (question is None or options is None)

    direct_holder = {"result": None, "error": None}
    direct_thread = None
    if is_ad_expected:
        direct_thread = threading.Thread(
            target=_direct_blocking,
            args=(client, model, item, direct_holder),
            daemon=True,
        )
        direct_thread.start()

    try:
        v9 = run_v9_item(client, model, item, split, max_turns,
                         question=question, options=options)
        v9_error = v9.error
    except Exception as e:
        v9 = None
        v9_error = f"{type(e).__name__}: {e}"

    if direct_thread is not None:
        direct_thread.join()
    direct_result = direct_holder["result"]
    direct_error = direct_holder["error"]

    base = {
        "item_id": item.get("item_id"),
        "domain_code": item.get("domain_code"),
        "label_gt": item.get("label"),
        "mode": None,
        "anomaly_score": None,
        "direct_score": None,
        "v9_score": None,
        "v9_initial_score": None,
        "v9_updated_score": None,
        "mcq_answer": None,
        "free_text": None,
        "option_scores": None,
        "rationale": "",
        "n_turns": 0,
        "tools_used": [],
        "confidence": 0,
        "candidate_features": None,
        "remaining_features": None,
        "refutation_verdicts": [],
        "history": [],
        "w_direct": w_direct,
        "w_v9": w_v9,
        "learning_enabled": bool(learning_enabled),
        "controller": None,
        "error": v9_error,
        "direct_error": direct_error,
    }

    if v9 is None:
        fallback_score = (direct_result or {}).get("anomaly_score")
        base["mode"] = "anomaly_detection" if is_ad_expected else "unknown"
        base["anomaly_score"] = fallback_score
        base["direct_score"] = fallback_score
        base["rationale"] = ("v9 agent failed; reporting Direct-only score"
                             if fallback_score is not None
                             else "v9 agent failed, no fallback")
        base["error"] = f"v9_failed: {v9_error}"
        return base

    base.update({
        "mode": v9.mode,
        "v9_score": v9.score,
        "v9_initial_score": v9.initial_score,
        "v9_updated_score": v9.updated_score,
        "mcq_answer": v9.mcq_answer,
        "free_text": v9.free_text,
        "option_scores": v9.option_scores,
        "rationale": v9.rationale,
        "n_turns": v9.n_turns,
        "tools_used": v9.tools_used,
        "confidence": v9.confidence,
        "candidate_features": v9.candidate_features,
        "remaining_features": v9.remaining_features,
        "refutation_verdicts": v9.refutation_verdicts,
        "history": v9.history,
    })

    agent_decided_ad = (v9.mode == "anomaly_detection")
    direct_score = (direct_result or {}).get("anomaly_score")
    base["direct_score"] = direct_score if agent_decided_ad else None
    # Preserve Direct rationale text so the downstream meta-rule reflector
    # (verbalized_v4) has something to reason over. Cheap — just a string.
    if direct_result is not None and agent_decided_ad:
        base["direct_rationale"] = _direct_rationale(direct_result)
    else:
        base["direct_rationale"] = ""

    # Fixed-weight blend: always computed as the v10-equivalent baseline /
    # controller fallback.
    if agent_decided_ad and direct_score is not None and v9.score is not None:
        blend_score = max(0.0, min(1.0, w_direct * direct_score + w_v9 * v9.score))
    elif v9.score is not None:
        blend_score = v9.score
    else:
        blend_score = direct_score

    # learning_enabled=False OR non-AD mode OR missing branch → behave as v10.
    if (not learning_enabled) or (not agent_decided_ad) \
       or (direct_score is None) or (v9.score is None):
        base["anomaly_score"] = blend_score
        if learning_enabled and agent_decided_ad and \
           (direct_score is None or v9.score is None):
            base["controller"] = {"skipped": "missing_branch"}
        return base

    # learning_enabled + AD + both branches present → controller arbitration.
    rules_text = _retrieve_rules_cached(
        rulebook_dir or "",
        item.get("domain_code", "") or "",
        item.get("category") or "",
        max_meta=3, max_domain=4,
    )
    ctrl_client = controller_client or client
    ctrl_model = controller_model or model
    ctrl_score, ctrl_meta = _controller_arbitrate(
        ctrl_client, ctrl_model, item,
        v9_score=v9.score, v9_rationale=v9.rationale,
        direct_score=direct_score,
        direct_rationale=_direct_rationale(direct_result),
        rules_text=rules_text,
        max_tokens=controller_max_tokens,
    )
    if ctrl_score is None:
        base["anomaly_score"] = blend_score
        base["controller"] = {**(ctrl_meta or {}), "fallback": "blend"}
    else:
        base["anomaly_score"] = ctrl_score
        base["controller"] = ctrl_meta
    return base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", choices=["calibration", "dev", "test"],
                    required=True)
    ap.add_argument("--backend", choices=["gpt", "seedvl", "qwen3"],
                    required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--max_turns", type=int, default=5)
    ap.add_argument("--max_workers", type=int, default=9)
    ap.add_argument("--max_items", type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--w_direct", type=float, default=0.5)
    ap.add_argument("--w_v9", type=float, default=0.5)
    ap.add_argument("--learning_enabled", action="store_true",
                    help="Activate the controller VLM stage. Without this "
                         "flag the runner is byte-equivalent to agent_v10.")
    ap.add_argument("--rulebook_dir", default="",
                    help="Directory with per-domain rulebook JSON files "
                         "({domain_code}.json). Ignored unless "
                         "--learning_enabled.")
    ap.add_argument("--controller_max_tokens", type=int, default=400)
    args = ap.parse_args()

    items = json.load(open(args.manifest))
    items = [x for x in items if x.get("split") == args.split]
    if args.max_items:
        items = items[:args.max_items]

    prev = []
    done_ids = set()
    if args.resume and os.path.exists(args.output):
        prev = json.load(open(args.output))
        done_ids = {r["item_id"] for r in prev if r.get("error") is None}
        items = [x for x in items if x["item_id"] not in done_ids]

    client = get_client(args.backend)
    model = get_model_name(args.backend)

    def _run(x):
        try:
            return run_v11_item(
                client, model, x, args.split, args.max_turns,
                w_direct=args.w_direct, w_v9=args.w_v9,
                learning_enabled=args.learning_enabled,
                rulebook_dir=args.rulebook_dir,
                controller_max_tokens=args.controller_max_tokens,
            )
        except Exception as e:
            return {"item_id": x["item_id"], "anomaly_score": 0.5,
                    "error": f"{type(e).__name__}: {e}"}

    results_by_id = {x["item_id"]: x for x in prev}
    t0 = time.time()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futs = [ex.submit(_run, x) for x in items]
        for i, f in enumerate(as_completed(futs)):
            r = f.result()
            results_by_id[r["item_id"]] = r
            if (i + 1) % 25 == 0:
                with open(args.output, "w") as ff:
                    json.dump(list(results_by_id.values()), ff)
                print(f"[{i+1}/{len(items)}] t={time.time()-t0:.1f}s",
                      flush=True)

    with open(args.output, "w") as f:
        json.dump(list(results_by_id.values()), f)
    print(f"Wrote {len(results_by_id)} → {args.output}")


if __name__ == "__main__":
    main()
