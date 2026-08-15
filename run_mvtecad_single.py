#!/usr/bin/env python3
"""
Single-image MVTec-AD anomaly detection pipeline using AnomalyClaw v12.

Runs the identical v12 passive pipeline that produced
  benchmark/results/v2/v12_passive_test/D1.json
Output format matches that file exactly.

Two usage modes
───────────────
Mode A — pull an existing benchmark item from the D1 manifest
  (lets you reproduce D1.json results one item at a time):

    python run_mvtecad_single.py \
        --item_id D1_0077 \
        --manifest benchmark/manifests_v2/D1_industrial_manifest.json \
        --backend gpt \
        --output output/D1_0077.json

Mode B — supply your own query + reference images:

    python run_mvtecad_single.py \
        --query /data/MVTec-AD/hazelnut/test/crack/001.png \
        --refs  /data/MVTec-AD/hazelnut/train/good/081.png \
                /data/MVTec-AD/hazelnut/train/good/380.png \
        --category hazelnut \
        --backend gpt \
        --output output/my_result.json

Backend environment variables
─────────────────────────────
  GPT backend  :  GPT_API_KEY (required)
                  GPT_API_BASE (optional, for proxies / custom endpoints)
                  GPT_MODEL   (optional, default: gpt-4o)

  Qwen3 backend:  QWEN_API_KEY (optional, default "EMPTY")
                  QWEN_API_BASE (optional, default http://localhost:8000/v1)
                  QWEN_MODEL  (optional, default: Qwen3-VL-8B-Instruct)

  SeedVL backend: SEED_API_KEY (required)
                  SEED_API_BASE (optional)
                  SEED_MODEL  (optional)

Data path resolution
────────────────────
  Manifest paths begin with {DATA_ROOT}/ and are expanded at runtime via
  the ANOMALYCLAW_DATA environment variable.  If the variable is not set
  the code falls back to <repo>/benchmark/data.

  Custom paths (Mode B) are used as-is; absolute paths are recommended.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# ── resolve benchmark/scripts so local imports work ──────────────────────────
REPO_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = REPO_ROOT / "benchmark" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))  # prepend benchmark/scripts to sys.path so local imports work

import agent_v12 as _v12
from infer import get_client, get_model_name
# from .benchmark.scripts import agent_v12 as _v12
# from .benchmark.scripts.infer import get_client, get_model_name


# ── helpers ───────────────────────────────────────────────────────────────────

def _load_item_from_manifest(manifest_path: str, item_id: str) -> dict:
    with open(manifest_path, encoding="utf-8") as fh:
        items = json.load(fh)
    for item in items:
        if item.get("item_id") == item_id:
            return item
    sample_ids = [x.get("item_id") for x in items[:10]]
    raise ValueError(
        f"item_id {item_id!r} not found in {manifest_path}.\n"
        f"First 10 available IDs: {sample_ids}"
    )


def _build_item_from_paths(query: str, refs: list[str],
                            category: str, item_id: str = "custom_001") -> dict:
    return {
        "item_id":        item_id,
        "domain":         "industrial",
        "domain_code":    "D1",
        "query_path":     query,
        "ref_paths":      refs,
        "label":          None,
        "anomaly_type":   None,
        "source_dataset": "MVTec-AD",
        "category":       category,
        "split":          "test",
    }


def _print_summary(result: dict) -> None:
    sep = "─" * 62
    print(f"\n{'═' * 62}")
    print(f"  AnomalyClaw v12 Passive — Result")
    print(f"{'═' * 62}")
    print(f"  item_id   : {result['item_id']}")
    print(f"  domain    : {result.get('domain_code', 'D1')}  (MVTec-AD industrial)")
    print(f"  category  : {result.get('category', '—')}")

    score = result.get("anomaly_score")
    if score is not None:
        verdict = "ANOMALOUS" if score > 0.5 else "NORMAL"
        print(f"\n  anomaly_score : {score:.4f}  →  {verdict}")
    else:
        print(f"\n  anomaly_score : N/A")

    print(f"  direct_score  : {result.get('direct_score')}")
    print(f"  v9_score      : {result.get('v9_score')}")

    gt = result.get("label_gt")
    if gt is not None:
        gt_str = "anomalous" if gt == 1 else "normal"
        correct = (score is not None) and ((score > 0.5) == (gt == 1))
        mark = "CORRECT" if correct else "WRONG"
        print(f"  ground_truth  : {gt_str}  ({mark})")

    print(f"\n  agent_turns   : {result.get('n_turns', 0)}")
    tools = result.get("tools_used") or []
    print(f"  tools_used    : {tools if tools else '(none)'}")
    print(f"  confidence    : {result.get('confidence', 0)}")

    rationale = (result.get("rationale") or "").strip()
    if rationale:
        snippet = rationale[:300] + ("…" if len(rationale) > 300 else "")
        print(f"\n  agent rationale:\n    {snippet}")

    dr_raw = result.get("direct_rationale") or ""
    if isinstance(dr_raw, str) and dr_raw.strip():
        try:
            dr = json.loads(dr_raw)
            evidence = (dr.get("evidence") or "").strip()
            if evidence:
                snippet = evidence[:200] + ("…" if len(evidence) > 200 else "")
                print(f"\n  direct evidence:\n    {snippet}")
        except Exception:
            pass

    errors = [e for e in [result.get("error"), result.get("direct_error")] if e]
    if errors:
        print(f"\n  errors: {errors}")

    print(f"{'═' * 62}\n")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Run AnomalyClaw v12 passive pipeline on one MVTec-AD image.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Mode A
    ap.add_argument(
        "--item_id", default=None, metavar="D1_XXXX",
        help="Item ID from the D1 manifest, e.g. D1_0077  (Mode A)"
    )
    ap.add_argument(
        "--manifest",
        default="benchmark/manifests_v2/D1_industrial_manifest.json",
        help="Path to the D1 manifest JSON  (default: benchmark/manifests_v2/D1_industrial_manifest.json)"
    )

    # Mode B
    ap.add_argument("--query", default=None,
                    help="Path to the query image  (Mode B)")
    ap.add_argument("--refs", nargs="+", default=None,
                    help="Paths to reference normal images  (Mode B)")
    ap.add_argument("--category", default="unknown",
                    help="MVTec-AD category name, e.g. hazelnut  (Mode B)")

    # Shared
    ap.add_argument("--backend", choices=["gpt", "seedvl", "qwen3"], default="gpt",
                    help="LLM backend  (default: gpt)")
    ap.add_argument("--output", default="output/single_result.json",
                    help="Output JSON path  (default: output/single_result.json)")
    ap.add_argument("--max_turns", type=int, default=4,
                    help="Maximum agent turns  (default: 4)")
    ap.add_argument("--w_direct", type=float, default=0.5,
                    help="Weight for direct-branch score  (default: 0.5)")
    ap.add_argument("--w_v9", type=float, default=0.5,
                    help="Weight for v9-agent score  (default: 0.5)")

    args = ap.parse_args()

    # ── resolve item ─────────────────────────────────────────────────────────
    if args.item_id is not None:
        manifest_path = args.manifest
        if not os.path.isabs(manifest_path):
            manifest_path = str(REPO_ROOT / manifest_path)
        print(f"[Mode A] Loading {args.item_id!r} from {manifest_path}")
        item = _load_item_from_manifest(manifest_path, args.item_id)
        n_refs = len(item.get("ref_paths") or [])
        gt_str = {0: "normal", 1: "anomalous"}.get(item.get("label"), "unknown")
        print(f"         query   : {item['query_path']}")
        print(f"         refs    : {n_refs} reference images")
        print(f"         label   : {gt_str}  (split: {item.get('split', '?')})")

    elif args.query is not None:
        if not args.refs:
            ap.error("--refs is required in Mode B (provide at least one reference image)")
        item = _build_item_from_paths(args.query, args.refs, args.category)
        print(f"[Mode B] Custom image")
        print(f"         query    : {args.query}")
        print(f"         refs     : {args.refs}")
        print(f"         category : {args.category}")

    else:
        ap.error(
            "Specify either --item_id (Mode A: manifest item)\n"
            "or --query + --refs (Mode B: custom image)."
        )

    # ── init backend ─────────────────────────────────────────────────────────
    print(f"\nInitialising {args.backend!r} backend …")
    client = get_client(args.backend)
    model  = get_model_name(args.backend)
    print(f"Model : {model}")

    # ── run pipeline ─────────────────────────────────────────────────────────
    print(
        f"\nRunning v12 passive pipeline  "
        f"(max_turns={args.max_turns}, "
        f"w_direct={args.w_direct}, w_v9={args.w_v9}) …"
    )
    t0 = time.time()

    result = _v12.run_v12_item(
        client=client,
        model=model,
        item=item,
        split=item.get("split", "test"),
        max_turns=args.max_turns,
        w_direct=args.w_direct,
        w_v9=args.w_v9,
        learning_enabled=False,   # passive mode — same settings as D1.json
    )

    elapsed = time.time() - t0
    print(f"Completed in {elapsed:.1f}s")

    # Attach the human-readable category field (not in the agent output)
    result["category"] = item.get("category", args.category)

    # ── save ─────────────────────────────────────────────────────────────────
    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = REPO_ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
    print(f"Result saved → {out_path}")

    _print_summary(result)


if __name__ == "__main__":
    main()
