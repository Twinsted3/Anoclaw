"""AnomalyClaw v6.10 — self-consistency pure agent.

Runs the Direct VLM prompt N times with temperature > 0 and takes the
MEDIAN score. No tools, no ReAct loop. Just multi-sample voting.

Codex's suggested experiment #5 (simplified): if the VLM is noisy and
errors are decorrelated across samples, median should be more robust.

Tested as a PURE agent: no expert, no ensemble with Direct (the Direct
is already part of the N samples).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import statistics

sys.path.insert(0, str(Path(__file__).parent))

from infer import (  # noqa: E402
    build_prompt_v0, call_llm, extract_json, get_client, get_model_name,
    img_msg, load_and_encode, score_from_v0, text_msg,
)


def _one_sample(client, model, item, temperature):
    messages = [
        {"role": "system",
         "content": "You are a visual anomaly inspector. Return JSON only."},
        {"role": "user", "content": (
            [text_msg(build_prompt_v0(item.get("domain_code", "D?"),
                                      has_refs=True))] +
            [img_msg(load_and_encode(p)) for p in item.get("ref_paths", [])[:4]] +
            [text_msg("QUERY:"), img_msg(load_and_encode(item["query_path"]))]
        )},
    ]
    text, _, _ = call_llm(client, model, messages, max_tokens=500,
                          temperature=temperature)
    parsed = extract_json(text)
    return float(score_from_v0(parsed))


def _aggregate(scores, mode="median"):
    scores = [s for s in scores if s is not None]
    if not scores:
        return 0.5
    if mode == "median":
        return statistics.median(scores)
    if mode == "mean":
        return sum(scores) / len(scores)
    if mode == "max":
        return max(scores)
    raise ValueError(mode)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", choices=["calibration", "dev", "test"],
                    required=True)
    ap.add_argument("--backend", choices=["qwen3", "seedvl", "gpt"],
                    required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--domains", nargs="*", default=None)
    ap.add_argument("--n_samples", type=int, default=3)
    ap.add_argument("--temperature", type=float, default=0.3)
    ap.add_argument("--aggregate", choices=["median", "mean", "max"],
                    default="median")
    ap.add_argument("--max_workers", type=int, default=8)
    ap.add_argument("--max_items", type=int, default=0)
    args = ap.parse_args()

    items = json.load(open(args.manifest))
    items = [x for x in items if x.get("split") == args.split]
    if args.domains:
        items = [x for x in items if x.get("domain_code") in args.domains]
    if args.max_items:
        items = items[:args.max_items]

    client = get_client(args.backend)
    model = get_model_name(args.backend)

    results = []
    t0 = time.time()

    def _run_one(x):
        try:
            samples = []
            for i in range(args.n_samples):
                s = _one_sample(client, model, x, args.temperature)
                samples.append(s)
            score = _aggregate(samples, args.aggregate)
            return {
                "item_id": x["item_id"], "domain_code": x.get("domain_code"),
                "label_gt": x.get("label"), "anomaly_score": float(score),
                "samples": samples,
                "aggregate": args.aggregate, "temperature": args.temperature,
                "n_samples": args.n_samples, "error": None,
            }
        except Exception as e:
            return {"item_id": x["item_id"], "domain_code": x.get("domain_code"),
                    "label_gt": x.get("label"), "anomaly_score": 0.5,
                    "error": f"{type(e).__name__}: {e}"}

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futures = [ex.submit(_run_one, x) for x in items]
        for i, fut in enumerate(as_completed(futures)):
            results.append(fut.result())
            if (i + 1) % 25 == 0:
                with open(args.output, "w") as f:
                    json.dump(results, f)
                print(f"[{i+1}/{len(items)}] {time.time()-t0:.1f}s  "
                      f"written={len(results)}", flush=True)

    with open(args.output, "w") as f:
        json.dump(results, f)
    print(f"Wrote {len(results)} results → {args.output}")


if __name__ == "__main__":
    main()
