#!/usr/bin/env python3
"""AnomalyClaw with logit-based Direct branch (replacing JSON-confidence Direct).

Same parallel-Direct + refutation architecture as agent_v12, but:
- Direct branch = call_logit() (yes/no binary prompt, softmax of first-token logprobs)
  instead of run_v0() (JSON {label, confidence})
- Refutation branch = run_v9_item() (unchanged)
- Final score = 0.5 * direct_logit + 0.5 * v9_score

Refutation trajectory still uses the v12 specialty-aware tool catalog and
prompts; only the direct branch's score is replaced.
"""
import argparse
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "benchmark/scripts"))

from agent_v11 import _direct_rationale  # noqa: E402
from agent_v12 import _run_v9_agent_v12 as run_v9_item  # noqa: E402 (use v12 specialty-aware refutation)
from infer import get_client, get_model_name, label_from_score  # noqa: E402
from direct_logit_qwen3 import call_logit


def _logit_blocking(client, model, item, out):
    try:
        r = call_logit(client, model, item)
        out["result"] = {
            "label_pred": label_from_score(r["score"]) if r["score"] is not None else None,
            "anomaly_score": r["score"],
            "anomaly_type_pred": None,
            "raw_output": {"v0_logit": {"raw_text": r.get("raw_text"),
                                          "logit_yes": r.get("logit_yes"),
                                          "logit_no": r.get("logit_no"),
                                          "first_top": r.get("first_top")}},
            "cost_tokens": {"input": 0, "output": 0},
            "latency_sec": 0.0,
        }
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"


def run_logitdirect_item(client, model, item, split, max_turns,
                          w_direct=0.5, w_v9=0.5):
    direct_holder = {"result": None, "error": None}
    direct_thread = threading.Thread(
        target=_logit_blocking, args=(client, model, item, direct_holder), daemon=True,
    )
    direct_thread.start()

    try:
        v9 = run_v9_item(client, model, item, split, max_turns)
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
        "anomaly_score": None,
        "direct_score": None,
        "v9_score": None,
        "n_turns": getattr(v9, "n_turns", 0) if v9 is not None else 0,
        "tools_used": getattr(v9, "tools_used", []) if v9 is not None else [],
        "candidate_features": getattr(v9, "candidate_features", []) if v9 is not None else [],
        "refutation_verdicts": getattr(v9, "refutation_verdicts", {}) if v9 is not None else {},
        "v9_initial_score": getattr(v9, "initial_score", None) if v9 is not None else None,
        "v9_updated_score": getattr(v9, "updated_score", None) if v9 is not None else None,
        "rationale": getattr(v9, "rationale", "") if v9 is not None else "",
        "history": getattr(v9, "history", []) if v9 is not None else [],
        "w_direct": w_direct,
        "w_v9": w_v9,
        "error": v9_error,
        "direct_error": direct_error,
        "direct_rationale": "",
    }

    direct_score = (direct_result or {}).get("anomaly_score")
    v9_score = getattr(v9, "score", None) if v9 is not None else None
    base["direct_score"] = direct_score
    base["v9_score"] = v9_score
    if direct_score is not None and v9_score is not None:
        base["anomaly_score"] = max(0.0, min(1.0, w_direct * direct_score + w_v9 * v9_score))
    elif direct_score is not None:
        base["anomaly_score"] = direct_score
    elif v9_score is not None:
        base["anomaly_score"] = v9_score
    base["direct_rationale"] = _direct_rationale(direct_result) if direct_result else ""
    return base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--backend", choices=["gpt", "seedvl", "qwen3"], required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--max_turns", type=int, default=5)
    ap.add_argument("--max_workers", type=int, default=24)
    ap.add_argument("--w_direct", type=float, default=0.5)
    ap.add_argument("--w_v9", type=float, default=0.5)
    args = ap.parse_args()

    items = json.load(open(args.manifest))
    if isinstance(items, dict) and "items" in items:
        items = items["items"]
    items = [it for it in items if it.get("split") == args.split]
    print(f"loaded {len(items)} items split={args.split}")

    client = get_client(args.backend)
    model = get_model_name(args.backend)
    out_path = Path(args.output)
    results = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        futs = {pool.submit(run_logitdirect_item, client, model, it, args.split,
                              args.max_turns, args.w_direct, args.w_v9): it for it in items}
        done = 0
        for f in as_completed(futs):
            results.append(f.result())
            done += 1
            if done % 20 == 0:
                el = time.time() - t0
                rate = done / el
                eta = (len(items) - done) / max(rate, 0.001)
                errs = sum(1 for r in results if r.get("error"))
                print(f"[{done}/{len(items)}] t={el:.1f}s rate={rate:.2f}/s eta={eta/60:.1f}min errs={errs}", flush=True)
                json.dump(results, open(out_path, "w"))
    json.dump(results, open(out_path, "w"))
    print(f"Wrote {len(results)} -> {out_path}")


if __name__ == "__main__":
    main()
