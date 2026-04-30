"""AnomalyClaw v10 — v9 trajectory + parallel independent generic Direct call.

Architecture:
  Runs the v9 agent trajectory (same as `agent_v9.py`) and, when the task is
  pure anomaly detection (mode == "anomaly_detection"), also makes an
  INDEPENDENT generic Direct VLM call (infer.run_v0). Direct and v9 run in
  parallel threads so wall-time cost is max(direct, v9), not sum.

  Final `anomaly_score` for AD mode:
      anomaly_score = w_direct * direct_score + w_v9 * v9_score

  For non-AD modes (MCQ / object_analysis / open_end), v10 passes the v9
  result through unchanged — the Direct call is skipped, and `anomaly_score`
  is v9.score (may be used as a side signal by downstream aggregators).

  The Direct call uses `infer.build_prompt_v0`, which respects the
  `DESCRIPTOR_MODE` environment variable. Set `DESCRIPTOR_MODE=generic` for
  descriptor-free Direct (aligned with v9's descriptor-free task preamble),
  or leave unset / set `task` for the domain-anchored v0 prompt.

CLI is identical to agent_v9.py plus `--w_direct` / `--w_v9` for ablation.
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

from agent_v9 import run_v9_item  # noqa: E402
from infer import get_client, get_model_name, run_v0  # noqa: E402


def _direct_blocking(client, model, item, out):
    try:
        out["result"] = run_v0(client, model, item)
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"


def run_v10_item(client, model, item, split, max_turns,
                 question=None, options=None,
                 w_direct=0.5, w_v9=0.5):
    """Run v9 trajectory and parallel Direct, blend for AD mode.

    Returns a dict with both the v9-native fields (mode / mcq_answer /
    free_text / option_scores) and v10-added fields (direct_score / v9_score /
    weights).
    """
    # If the caller supplies a question+options, it's MCQ / open-ended —
    # skip Direct entirely. Otherwise run Direct in parallel with v9.
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

    # Run v9 on the current thread while Direct runs in parallel.
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

    # Build base dict with all schema keys present.
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
        "error": v9_error,
        "direct_error": direct_error,
    }

    if v9 is None:
        # Agent blew up entirely. Fall back to Direct if we have it.
        fallback_score = (direct_result or {}).get("anomaly_score")
        base["mode"] = "anomaly_detection" if is_ad_expected else "unknown"
        base["anomaly_score"] = fallback_score
        base["direct_score"] = fallback_score
        base["rationale"] = "v9 agent failed; reporting Direct-only score" \
            if fallback_score is not None else "v9 agent failed, no fallback"
        base["error"] = f"v9_failed: {v9_error}"
        return base

    # v9 produced a result — fill its fields.
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

    # Ensemble logic: only for AD mode.
    agent_decided_ad = (v9.mode == "anomaly_detection")
    if agent_decided_ad and direct_result is not None:
        direct_score = direct_result.get("anomaly_score")
        base["direct_score"] = direct_score
        if direct_score is not None and v9.score is not None:
            ens = w_direct * direct_score + w_v9 * v9.score
            base["anomaly_score"] = max(0.0, min(1.0, ens))
        elif v9.score is not None:
            base["anomaly_score"] = v9.score  # Direct score missing
        else:
            base["anomaly_score"] = direct_score
    elif agent_decided_ad and direct_result is None:
        # Direct call failed; use v9 alone and remember the error.
        base["anomaly_score"] = v9.score
    else:
        # Non-AD mode: pass v9.score through as anomaly_score, no blend.
        base["anomaly_score"] = v9.score

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
            return run_v10_item(client, model, x, args.split, args.max_turns,
                                w_direct=args.w_direct, w_v9=args.w_v9)
        except Exception as e:
            return {"item_id": x["item_id"], "anomaly_score": 0.5,
                    "error": f"{type(e).__name__}: {e}"}

    # Dedup on resume: keep by item_id, retries overwrite the errored entry
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
