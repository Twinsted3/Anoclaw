"""Branch-frozen controller replay.

For a cleanest ablation, v9 + Direct must be IDENTICAL across rule regimes.
This script reads the v11 full-run per-item results (which contain the
v9 and Direct outputs), re-calls the controller with an alternative rule
prompt on the SAME cached branch outputs, and writes a new per-item JSON
file with the replayed anomaly_score.

Usage:
  replay_controller.py --source benchmark/results/verbalized/v11_eval_test \\
                       --rulebook_dir '' \\   # empty = no-rules replay
                       --out benchmark/results/verbalized/v11_eval_test_frozen_no_rules

  replay_controller.py --source benchmark/results/verbalized/v11_eval_test \\
                       --rulebook_dir benchmark/results/verbalized/v4_rulebook_meta_only \\
                       --out benchmark/results/verbalized/v11_eval_test_frozen_meta_only

The full run is reused as-is; no replay needed for it (it's the canonical
"meta+domain" regime).
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent_v11 import (  # noqa: E402
    _controller_arbitrate, _retrieve_rules_cached,
)
from infer import get_client, get_model_name  # noqa: E402


def load_manifest_items(manifest_dir):
    """Return {item_id: row} across all 12 D*_manifest.json files."""
    idx = {}
    for p in sorted(Path(manifest_dir).glob("D*_manifest.json")):
        for x in json.load(open(p)):
            idx[x["item_id"]] = x
    return idx


def replay_one(client, model, rec, manifest_row, rulebook_dir,
               controller_max_tokens=400):
    """Replay controller on a single full-run record. Returns a new record
    with updated anomaly_score and controller fields; preserves v9/direct
    scores, rationales, trust counts, and all other bookkeeping.
    """
    out = dict(rec)  # shallow copy
    # Items that were never AD-mode in the original run: skip (keep original).
    agent_decided_ad = (rec.get("mode") == "anomaly_detection")
    v9_score = rec.get("v9_score")
    direct_score = rec.get("direct_score")
    # v11-style blend for fallback if controller declines to produce a score
    if v9_score is None or direct_score is None:
        blend_score = rec.get("anomaly_score", 0.5)
    else:
        blend_score = 0.5 * float(v9_score) + 0.5 * float(direct_score)

    if (not agent_decided_ad) or (v9_score is None) or (direct_score is None):
        out["anomaly_score"] = blend_score
        out["controller"] = {"skipped": "non-ad-or-missing-branch"}
        out["replay_from"] = "frozen"
        return out

    # Build an item dict with the paths needed by _controller_arbitrate
    item = {
        "query_path": manifest_row.get("query_path"),
        "ref_paths": manifest_row.get("ref_paths", [])[:2],
    }
    rules_text = _retrieve_rules_cached(
        rulebook_dir or "",
        rec.get("domain_code") or "",
        manifest_row.get("category") or "",
        max_meta=3, max_domain=4,
    )
    ctrl_score, ctrl_meta = _controller_arbitrate(
        client, model, item,
        v9_score=float(v9_score),
        v9_rationale=rec.get("rationale", "")[:600],
        direct_score=float(direct_score),
        direct_rationale=rec.get("direct_rationale", "")[:600],
        rules_text=rules_text,
        max_tokens=controller_max_tokens,
    )
    if ctrl_score is None:
        out["anomaly_score"] = blend_score
        out["controller"] = {**(ctrl_meta or {}), "fallback": "blend",
                             "replay_from": "frozen"}
    else:
        out["anomaly_score"] = ctrl_score
        out["controller"] = {**ctrl_meta, "replay_from": "frozen"}
    return out


def replay_file(client, model, src_path, dst_path, manifest_items,
                rulebook_dir, max_workers=8, controller_max_tokens=400):
    records = json.load(open(src_path))
    done = {}
    if os.path.exists(dst_path):
        prev = json.load(open(dst_path))
        done = {r["item_id"]: r for r in prev
                if r.get("controller") and not r["controller"].get("error")}
    pending = [r for r in records if r["item_id"] not in done]
    results = dict(done)

    def _go(rec):
        mrow = manifest_items.get(rec["item_id"]) or {}
        try:
            return replay_one(client, model, rec, mrow, rulebook_dir,
                              controller_max_tokens)
        except Exception as e:
            return {**rec, "controller": {"error": f"{type(e).__name__}: {e}"},
                    "replay_from": "frozen"}

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(_go, r) for r in pending]
        for i, f in enumerate(as_completed(futs)):
            r = f.result()
            results[r["item_id"]] = r
            if (i + 1) % 25 == 0:
                Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
                json.dump(list(results.values()), open(dst_path, "w"))
                print(f"  [{i+1}/{len(pending)}] t={time.time()-t0:.1f}s",
                      flush=True)
    Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
    json.dump(list(results.values()), open(dst_path, "w"))
    print(f"  wrote {len(results)} → {dst_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True,
                    help="Directory with full-run v11 JSON files (D*.json).")
    ap.add_argument("--out", required=True,
                    help="Output directory for replayed files.")
    ap.add_argument("--rulebook_dir", default="",
                    help="Rulebook to inject at replay. Empty = no rules.")
    ap.add_argument("--manifest_dir",
                    default="/hdd1/jiangxi/AD-Agent/benchmark/manifests_v2")
    ap.add_argument("--backend", choices=["gpt", "seedvl", "qwen3"],
                    default="qwen3")
    ap.add_argument("--max_workers", type=int, default=8)
    ap.add_argument("--controller_max_tokens", type=int, default=400)
    args = ap.parse_args()

    client = get_client(args.backend)
    model = get_model_name(args.backend)
    manifest_items = load_manifest_items(args.manifest_dir)
    Path(args.out).mkdir(parents=True, exist_ok=True)

    for p in sorted(Path(args.source).glob("D*.json")):
        dst = Path(args.out) / p.name
        print(f"[replay] {p.name} ← {p}  rulebook={args.rulebook_dir or '(none)'}")
        replay_file(client, model, p, dst, manifest_items,
                    args.rulebook_dir, args.max_workers,
                    args.controller_max_tokens)


if __name__ == "__main__":
    main()
