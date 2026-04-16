"""Run the two v6 baselines: Direct VLM and Fixed-fusion (w=0.2, SubspaceAD).

Protocol:
  * Direct: build_prompt_v0 + run per item, record anomaly_score from score_from_v0.
  * Fixed-fusion: 0.8 * direct_score + 0.2 * sigmoid(expert, calibration-median).
  * NO per-domain tuning; NO test-split access beyond the prediction itself.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from infer import (  # noqa: E402
    build_prompt_v0, call_llm, extract_json, get_client, get_model_name,
    img_msg, load_and_encode, score_from_v0, text_msg,
)
from agent_tools_v6 import _load_expert_scores  # noqa: E402


def run_direct_item(client, model, item: dict) -> dict:
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
    try:
        text, _, _ = call_llm(client, model, messages,
                              max_tokens=500, temperature=0.0)
        parsed = extract_json(text)
        score = score_from_v0(parsed)
        return {"item_id": item["item_id"],
                "domain_code": item.get("domain_code"),
                "label_gt": item.get("label"),
                "anomaly_score": float(score),
                "raw_output": parsed, "error": None}
    except Exception as e:
        return {"item_id": item["item_id"],
                "domain_code": item.get("domain_code"),
                "label_gt": item.get("label"),
                "anomaly_score": 0.5,
                "raw_output": None,
                "error": f"{type(e).__name__}: {e}"}


def load_calibration_median(expert: str = "subspacead") -> float:
    _, all_scores = _load_expert_scores(expert, "calibration")
    if len(all_scores) == 0:
        return 1.0
    return float(np.median(all_scores))


def fuse(direct_score: float, expert_score: float | None,
         median: float, w: float = 0.2) -> float:
    if expert_score is None:
        return float(direct_score)
    sig = 1.0 / (1.0 + np.exp(-2.0 * (expert_score - median)
                              / max(median, 1e-6)))
    return float((1 - w) * direct_score + w * sig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", choices=["calibration", "test"], required=True)
    ap.add_argument("--backend", choices=["qwen3", "seedvl", "gpt"], required=True)
    ap.add_argument("--output_dir", required=True)
    ap.add_argument("--domains", nargs="*", default=None)
    ap.add_argument("--max_items", type=int, default=0)
    ap.add_argument("--max_workers", type=int, default=8)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    items = json.load(open(args.manifest))
    items = [x for x in items if x.get("split") == args.split]
    if args.domains:
        items = [x for x in items if x.get("domain_code") in args.domains]
    if args.max_items:
        items = items[:args.max_items]

    client = get_client(args.backend)
    model = get_model_name(args.backend)
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    direct_path = Path(args.output_dir) / f"v6_direct_{args.backend}_{args.split}.json"

    # Resume?
    direct_out = []
    if args.resume and direct_path.exists():
        direct_out = json.load(open(direct_path))
        done = {r["item_id"] for r in direct_out if r.get("error") is None}
        items = [x for x in items if x["item_id"] not in done]
        print(f"[resume] {len(done)} items already complete; {len(items)} remaining")

    print(f"[Direct] {len(items)} items to process", flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futs = [ex.submit(run_direct_item, client, model, x) for x in items]
        for i, f in enumerate(as_completed(futs)):
            direct_out.append(f.result())
            if (i + 1) % 50 == 0:
                with open(direct_path, "w") as fh:
                    json.dump(direct_out, fh)
                print(f"  [{i+1}/{len(items)}] {time.time()-t0:.1f}s  "
                      f"written={len(direct_out)}", flush=True)

    with open(direct_path, "w") as f:
        json.dump(direct_out, f)
    print(f"Wrote {direct_path}")

    # Fixed-fusion
    median = load_calibration_median()
    expert_recs, _ = _load_expert_scores("subspacead", args.split)
    fusion_out = []
    for r in direct_out:
        expert = expert_recs.get(r["item_id"], {}).get("anomaly_score")
        fused = fuse(r["anomaly_score"], expert, median, w=0.2)
        fusion_out.append({**r, "anomaly_score": fused,
                           "direct_score_orig": r["anomaly_score"],
                           "expert_score": expert,
                           "fusion_w": 0.2, "fusion_median": median})

    fusion_path = Path(args.output_dir) / f"v6_fusion_{args.backend}_{args.split}.json"
    with open(fusion_path, "w") as f:
        json.dump(fusion_out, f)
    print(f"Wrote {fusion_path}")


if __name__ == "__main__":
    main()
