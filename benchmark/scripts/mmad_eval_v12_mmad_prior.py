"""MMAD evaluator — Implementation 2: Direct-as-prior agent.

Architecture per item:
  1) Direct (text MCQ) → option_scores + answer letter
  2) Direct's output is formatted into a "prior hint" text block:
       "An independent visual MCQ model gave a preliminary answer of
        {letter} with confidence {scores}. Use this as a soft prior:
        it may be wrong. Verify with your own observation and tools."
  3) Agent v12_mmad trajectory runs WITH prior_hint injected into turn 1.
  4) Final answer = agent.mcq_answer (no separate ensemble step).

Difference from v12_mmad eval:
  - Direct's output enters the agent's reasoning (not just averaged
    afterwards).
  - There is no "ensemble_answer" — the agent IS the final arbiter.
  - For AD items, Direct still uses ad_score path (anomaly_score in
    [0,1]); we convert to a letter via ad_score_to_letter and feed
    THAT into the prior hint.

Output schema retains the existing direct_* / agent_* fields so the
result file is comparable to mmad_v10_dev500.json. The headline metric
is `agent_answer` (the agent under prior hint) — there is no
`ensemble_answer` field; we set it to `agent_answer` for downstream
analysis convenience.
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

from infer import get_client, get_model_name  # noqa: E402
import agent_v12_mmad as v12_mmad_mod  # noqa: E402

from mmad_eval_v9 import (  # noqa: E402
    QTYPES_ALL,
    iter_mmad_items,
    stratified_sample_images,
    direct_ad_score,
    direct_mcq_answer,
    ad_score_to_letter,
)
from mmad_eval_v12_mmad import MMAD_DATASET_TO_DCODE  # noqa: E402


_AD_PRIOR_TEMPLATE = (
    "PRIOR FROM AN INDEPENDENT MODEL:\n"
    "  Another visual model (no tools, single look) estimated\n"
    "  anomaly_probability = {score:.3f} for the QUERY image\n"
    "  (= preliminary letter answer: {letter}).\n"
    "  Treat this as a soft prior — it may be wrong, especially when\n"
    "  the anomaly is subtle. Verify with refutation + tools and form\n"
    "  your own conclusion. You may agree or override."
)

_MCQ_PRIOR_TEMPLATE = (
    "PRIOR FROM AN INDEPENDENT MODEL:\n"
    "  Another visual model (no tools, single look) gave a preliminary\n"
    "  answer to this MCQ:\n"
    "    chosen letter: {letter}\n"
    "    option_scores: {scores}\n"
    "  Treat this as a soft prior — it may be wrong. Verify with your\n"
    "  own observation; you may agree or override."
)


def _format_prior_hint(is_ad, direct_out, options):
    """Build the textual prior hint from Direct's output."""
    if is_ad:
        score = direct_out.get("score") if direct_out else None
        if score is None:
            return None
        letter = ad_score_to_letter(score, options)
        return _AD_PRIOR_TEMPLATE.format(score=float(score),
                                         letter=letter or "?")
    else:
        ans = direct_out.get("answer") if direct_out else None
        scores = direct_out.get("option_scores") if direct_out else None
        if ans is None and not scores:
            return None
        scores_str = (json.dumps(scores) if isinstance(scores, dict)
                      else "(unavailable)")
        return _MCQ_PRIOR_TEMPLATE.format(letter=ans or "?",
                                          scores=scores_str)


def _run_one(client, model, item, split, max_turns, use_dataset_dcode):
    is_ad = (item["question_type"] == "Anomaly Detection")
    out = {
        "item_id": item["item_id"], "image": item["raw_key"],
        "correct_answer": item["correct_answer"],
        "question_type": item["question_type"],
        "question": item["question"], "options": item["options"],
        "class_name": item["class_name"], "dataset": item["dataset"],
        "label_gt": item["label_gt"],
    }

    # --- 1. Direct ---
    if is_ad:
        dr = direct_ad_score(client, model, item["image"], item["refs"])
        out["direct_score"] = dr.get("score")
        out["direct_rationale"] = dr.get("rationale", "")
        out["direct_answer"] = ad_score_to_letter(
            dr.get("score", 0.5), item["options"])
        if dr.get("error"):
            out["direct_error"] = dr["error"]
    else:
        dm = direct_mcq_answer(client, model, item["image"], item["refs"],
                               item["question"], item["options"])
        out["direct_answer"] = dm.get("answer")
        out["direct_option_scores"] = dm.get("option_scores")
        out["direct_rationale"] = dm.get("rationale", "")
        if dm.get("error"):
            out["direct_error"] = dm["error"]
        dr = dm

    # --- 2. Build prior hint from Direct output ---
    prior_hint = _format_prior_hint(is_ad, dr, item["options"])

    # --- 3. Agent v12_mmad with prior_hint injected ---
    if use_dataset_dcode:
        domain_code = MMAD_DATASET_TO_DCODE.get(
            item.get("dataset"), item["class_name"])
    else:
        domain_code = item["class_name"]
    agent_item = {
        "item_id": item["item_id"],
        "query_path": item["image"],
        "ref_paths": item["refs"],
        "domain_code": domain_code,
    }
    try:
        r = v12_mmad_mod._run_v9_agent_v12(
            client, model, agent_item, split, max_turns,
            question=item["question"], options=item["options"],
            prior_hint=prior_hint)
        out["agent_score"] = r.score
        out["agent_option_scores"] = r.option_scores
        out["agent_mode"] = r.mode
        out["agent_n_turns"] = r.n_turns
        out["agent_tools_used"] = r.tools_used
        out["agent_rationale"] = (r.rationale or "")[:200]
        if is_ad:
            out["agent_answer"] = ad_score_to_letter(r.score or 0.5,
                                                     item["options"])
        else:
            out["agent_answer"] = r.mcq_answer
        if r.error:
            out["agent_error"] = r.error
    except Exception as e:
        out["agent_answer"] = None
        out["agent_error"] = f"{type(e).__name__}: {e}"

    # --- 4. Final = agent_answer (no separate ensemble) ---
    out["ensemble_answer"] = out.get("agent_answer")
    out["prior_hint_used"] = prior_hint is not None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mmad_root", default="MMAD/dataset/MMAD")
    ap.add_argument("--output", required=True)
    ap.add_argument("--sample", type=int, default=500)
    ap.add_argument("--only_types", default=None)
    ap.add_argument("--backend", default="qwen3")
    ap.add_argument("--max_workers", type=int, default=16)
    ap.add_argument("--max_turns", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--use_dataset_dcode", action="store_true", default=True)
    args = ap.parse_args()

    if args.sample and args.sample > 0:
        items = stratified_sample_images(args.mmad_root, args.sample,
                                         seed=args.seed)
    else:
        items = list(iter_mmad_items(args.mmad_root))
    if args.only_types:
        keep = set(t.strip() for t in args.only_types.split(","))
        items = [x for x in items if x["question_type"] in keep]
    print(f"[mmad_prior] {len(items)} QA items", flush=True)

    prev = []; done_ids = set()
    if args.resume and os.path.exists(args.output):
        prev = json.load(open(args.output))
        done_ids = {r["item_id"] for r in prev if r.get("agent_answer")}
        items = [x for x in items if x["item_id"] not in done_ids]
        print(f"[resume] {len(done_ids)} done; {len(items)} remaining",
              flush=True)

    client = get_client(args.backend)
    model = get_model_name(args.backend)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    results = list(prev)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futs = [ex.submit(_run_one, client, model, x, "test",
                           args.max_turns, args.use_dataset_dcode)
                for x in items]
        for i, f in enumerate(as_completed(futs)):
            try:
                results.append(f.result())
            except Exception as e:
                print(f"[err] worker: {type(e).__name__}: {e}", flush=True)
            if (i + 1) % 10 == 0:
                with open(args.output, "w") as ff:
                    json.dump(results, ff)
                dt = time.time() - t0
                rate = (i + 1) / dt if dt > 0 else 0
                eta = (len(items) - (i + 1)) / rate if rate > 0 else 0
                print(f"[{i+1}/{len(items)}] t={dt:.1f}s rate={rate:.2f}/s "
                      f"eta={eta:.0f}s", flush=True)

    with open(args.output, "w") as f:
        json.dump(results, f)
    print(f"Wrote {len(results)} → {args.output}")

    print("\n=== Per-type letter accuracy (Direct-as-prior agent) ===",
          flush=True)
    by_type = defaultdict(list)
    for r in results:
        by_type[r.get("question_type")].append(r)
    for qt in QTYPES_ALL:
        subset = by_type.get(qt) or []
        if not subset:
            continue
        for fld in ("direct_answer", "agent_answer"):
            corr = sum(1 for r in subset
                       if r.get(fld) and r.get(fld) == r["correct_answer"])
            tot = sum(1 for r in subset if r.get(fld))
            if tot:
                print(f"  {qt:25s} {fld:18s} {corr:3d}/{tot:<4d} "
                      f"{100*corr/tot:5.2f}%")


if __name__ == "__main__":
    main()
