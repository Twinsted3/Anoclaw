"""MMAD evaluator for v12_mmad agent (experimental fork of v10 eval).

The agent is `agent_v12_mmad._run_v9_agent_v12` — a v12 trajectory that
uses `agent_prompt_v12_mmad` to ENCOURAGE targeted tool use on non-AD
spatial / classification / fine-grained sub-types. Direct branch is
unchanged from v10's eval.

Original v10 eval docstring follows.
---
MMAD evaluator for v10 agent — Plan C: option-score voting.

Difference from `mmad_eval_v9.py`:

  - Both v9 agent and Direct MCQ are run in parallel on every item.
  - For non-AD questions we average their `option_scores` (A/B/C/D floats)
    and argmax the average to pick `ensemble_answer`. Previously the v9
    evaluator only ensembled AD items (score-level blend).
  - For AD questions behaviour is identical to v9's external ensemble:
    `ensemble_score = 0.5 * direct_score + 0.5 * v9_score`, mapped to a
    Yes/No letter.

  This surfaces v10's full ensembling semantics: Direct + v9 cast votes
  together on every MMAD question, not just AD.

Output fields added:
  ensemble_answer  — voting letter (non-AD) or score-based letter (AD)
  ensemble_option_scores  — averaged option_scores (non-AD only)
  ensemble_score   — for AD only, 0.5*direct + 0.5*v9
"""
from __future__ import annotations
import argparse
import json
import os
import random
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from infer import get_client, get_model_name  # noqa: E402
import agent_v12_mmad as v12_mmad_mod  # noqa: E402


# MMAD dataset → CrossDomainVAD-11 D-code mapping. Enables
# tool_expert_score on the matching MMAD subset. VisA is intentionally
# unmapped — none of the v8 experts cover it cleanly. When opt-in flag
# `--use_dataset_dcode` is set, v9_agent_run replaces the default
# class_name domain_code with this mapping; otherwise the legacy
# class_name is forwarded (preserves existing eval semantics).
MMAD_DATASET_TO_DCODE = {
    "DS-MVTec":   "D1",   # MVTec-AD subset, expert_score AUROC 0.97
    "MVTec-AD":   "D1",
    "GoodsAD":    "D5",   # expert_score AUROC 0.84
    "MVTec-LOCO": "D3",   # expert_score AUROC 0.69
    # "VisA":     None    # intentionally unmapped — class_name passes through
}

# Reuse the Direct + iteration utilities from mmad_eval_v9
from mmad_eval_v9 import (  # noqa: E402
    QTYPES_ALL,
    iter_mmad_items,
    stratified_sample_images,
    direct_ad_score,
    direct_mcq_answer,
    ad_score_to_letter,
)


def v9_agent_run(client, model, item, split, max_turns,
                 use_dataset_dcode: bool = False):
    """Run v12_mmad agent on one MMAD item.

    Same I/O contract as mmad_eval_v9.v9_agent_run but routed through
    agent_v12_mmad._run_v9_agent_v12 (uses agent_prompt_v12_mmad and the
    v8 tool catalog).

    Args:
      use_dataset_dcode: if True, map item['dataset'] to a CrossDomainVAD-11
        D-code (D1/D5/D3) so tool_expert_score can be invoked. VisA stays
        on its class_name (no expert). Default False — preserves the
        legacy "class_name as domain_code" behaviour from earlier runs.
    """
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
        # Do NOT pass item["question_type"] — that is a dataset meta-label
        # and feeding it to the agent would be oracle leakage.
        r = v12_mmad_mod._run_v9_agent_v12(
            client, model, agent_item, split, max_turns,
            question=item["question"], options=item["options"])
        return {
            "score": r.score,
            "mcq_answer": r.mcq_answer,
            "free_text": r.free_text,
            "option_scores": r.option_scores,
            "mode": r.mode,
            "rationale": (r.rationale or "")[:200],
            "n_turns": r.n_turns, "tools_used": r.tools_used,
            "error": r.error,
        }
    except Exception as e:
        return {"score": 0.5, "mcq_answer": None, "error":
                f"{type(e).__name__}: {e}"}


# -------------------------- Voting --------------------------

def _valid_opts(x):
    """Return dict with numeric A/B/C/D floats, or None if unusable."""
    if not isinstance(x, dict):
        return None
    out = {}
    for k in ("A", "B", "C", "D"):
        if k not in x:
            continue
        try:
            out[k] = float(x[k])
        except (TypeError, ValueError):
            continue
    return out if out else None


def blend_option_scores(agent_opts, direct_opts):
    """Average agent and direct option_scores; return (answer, blended)."""
    a = _valid_opts(agent_opts)
    d = _valid_opts(direct_opts)
    if a and d:
        keys = set(a.keys()) | set(d.keys())
        blended = {k: 0.5 * a.get(k, 0.0) + 0.5 * d.get(k, 0.0) for k in keys}
    elif a:
        blended = a
    elif d:
        blended = d
    else:
        return None, None
    if not blended:
        return None, None
    ans = max(blended.items(), key=lambda kv: kv[1])[0]
    return ans, blended


# -------------------------- Main --------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mmad_root", default="MMAD/dataset/MMAD")
    ap.add_argument("--output", required=True)
    ap.add_argument("--sample", type=int, default=1000,
                    help="Sample size in IMAGES; expanded to all questions "
                         "on those images. 0 = all images.")
    ap.add_argument("--only_types", default=None)
    ap.add_argument("--backend", default="qwen3")
    ap.add_argument("--max_workers", type=int, default=9)
    ap.add_argument("--max_turns", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--use_dataset_dcode", action="store_true",
                    help="Map MMAD dataset → CrossDomainVAD-11 D-code so "
                         "tool_expert_score becomes available on MVTec/"
                         "GoodsAD/MVTec-LOCO subsets. VisA stays on "
                         "class_name (no expert). Default off preserves "
                         "legacy behaviour.")
    args = ap.parse_args()

    if args.sample and args.sample > 0:
        print(f"[mmad_v10] stratified sampling {args.sample} images",
              flush=True)
        items = stratified_sample_images(args.mmad_root, args.sample,
                                         seed=args.seed)
    else:
        items = list(iter_mmad_items(args.mmad_root))
    if args.only_types:
        keep = set(t.strip() for t in args.only_types.split(","))
        items = [x for x in items if x["question_type"] in keep]
    print(f"[mmad_v10] {len(items)} QA items across "
          f"{len({i['class_name'] for i in items})} classes", flush=True)

    prev: list = []
    done_ids: set = set()
    if args.resume and os.path.exists(args.output):
        prev = json.load(open(args.output))
        done_ids = {r["item_id"] for r in prev if not r.get("fatal_error")}
        items = [x for x in items if x["item_id"] not in done_ids]
        print(f"[resume] {len(done_ids)} done; {len(items)} remaining",
              flush=True)

    client = get_client(args.backend)
    model = get_model_name(args.backend)
    t0 = time.time()

    def _run(x):
        is_ad = (x["question_type"] == "Anomaly Detection")
        out = {
            "item_id": x["item_id"], "image": x["raw_key"],
            "correct_answer": x["correct_answer"],
            "question_type": x["question_type"],
            "question": x["question"], "options": x["options"],
            "class_name": x["class_name"], "dataset": x["dataset"],
            "label_gt": x["label_gt"],
        }

        # --- Direct ---
        if is_ad:
            dr = direct_ad_score(client, model, x["image"], x["refs"])
            out["direct_score"] = dr.get("score")
            out["direct_rationale"] = dr.get("rationale", "")
            out["direct_answer"] = ad_score_to_letter(
                dr.get("score", 0.5), x["options"])
            if dr.get("error"):
                out["direct_error"] = dr["error"]
            direct_opts = None  # AD direct path has no option_scores
        else:
            dm = direct_mcq_answer(client, model, x["image"], x["refs"],
                                   x["question"], x["options"])
            out["direct_answer"] = dm.get("answer")
            direct_opts = dm.get("option_scores")
            out["direct_option_scores"] = direct_opts
            out["direct_rationale"] = dm.get("rationale", "")
            if dm.get("error"):
                out["direct_error"] = dm["error"]

        # --- Agent (v9 trajectory, same as v10's v9 inner loop) ---
        ag = v9_agent_run(client, model, x, "test", args.max_turns,
                          use_dataset_dcode=args.use_dataset_dcode)
        out["agent_score"] = ag.get("score")
        out["agent_option_scores"] = ag.get("option_scores")
        out["agent_mode"] = ag.get("mode")
        out["agent_n_turns"] = ag.get("n_turns")
        out["agent_tools_used"] = ag.get("tools_used")
        out["agent_rationale"] = ag.get("rationale", "")
        if is_ad:
            out["agent_answer"] = ad_score_to_letter(
                ag.get("score", 0.5), x["options"])
        else:
            out["agent_answer"] = ag.get("mcq_answer")
        if ag.get("error"):
            out["agent_error"] = ag["error"]

        # --- Ensemble ---
        if is_ad:
            # AD: score-level blend (same as v9 evaluator / v10 internal blend)
            if (out.get("direct_score") is not None
                    and out.get("agent_score") is not None):
                ens = 0.5 * out["direct_score"] + 0.5 * out["agent_score"]
                out["ensemble_score"] = ens
                out["ensemble_answer"] = ad_score_to_letter(ens, x["options"])
        else:
            # Non-AD: option-score voting
            ans, blended = blend_option_scores(
                ag.get("option_scores"), direct_opts)
            out["ensemble_option_scores"] = blended
            if ans is not None:
                out["ensemble_answer"] = ans
            else:
                # Fall back: prefer agent letter, then direct letter
                out["ensemble_answer"] = (
                    ag.get("mcq_answer") or out.get("direct_answer"))

        return out

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    results = list(prev)
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futs = [ex.submit(_run, x) for x in items]
        for i, f in enumerate(as_completed(futs)):
            try:
                results.append(f.result())
            except Exception as e:
                print(f"[err] worker: {type(e).__name__}: {e}", flush=True)
            if (i + 1) % 10 == 0:
                with open(args.output, "w") as ff:
                    json.dump(results, ff)
                dt = time.time() - t0
                rate = (i + 1) / dt if dt > 0 else 0.0
                eta = (len(items) - (i + 1)) / rate if rate > 0 else 0
                print(f"[{i+1}/{len(items)}] t={dt:.1f}s "
                      f"rate={rate:.2f}/s eta={eta:.0f}s", flush=True)

    with open(args.output, "w") as f:
        json.dump(results, f)
    print(f"Wrote {len(results)} → {args.output}")

    # Accuracy report
    print("\n=== Per-type MCQ accuracy ===", flush=True)
    header = f"  {'type':25s} {'field':20s} corr/tot  acc"
    print(header, flush=True)
    for qt in QTYPES_ALL:
        subset = [r for r in results if r.get("question_type") == qt]
        if not subset:
            continue
        for field in ("direct_answer", "agent_answer", "ensemble_answer"):
            correct = sum(1 for r in subset
                          if r.get(field)
                          and r.get(field) == r.get("correct_answer"))
            total = sum(1 for r in subset if r.get(field))
            if total:
                print(f"  {qt:25s} {field:20s} {correct:4d}/{total:<4d} "
                      f"{100 * correct / total:5.2f}%")


if __name__ == "__main__":
    main()
