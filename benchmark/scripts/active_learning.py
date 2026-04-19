"""Per-domain active self-evolution experiment.

Protocol per domain:
  1. Passive eval: run v9 agent on test items → baseline AUROC.
  2. Oracle selection: from DEV split (not test), pick K items with
     highest uncertainty (|agent_score - 0.5|) weighted by
     agent/direct disagreement.
  3. Oracle query: obtain GT labels for those K items (from manifest).
  4. Build per-domain RAG keyed by DINOv2 CLS embedding of query image.
  5. Active eval: re-run v9 on test items with top-3 labelled neighbors
     injected as few-shot context in turn-1 user message.
  6. Report per-domain AUROC Δ.

Output: one JSON per domain with pre/post scores, plus combined summary.

Usage:
  python benchmark/scripts/active_learning.py \
    --manifest_dir benchmark/manifests_v2 \
    --domain D1 \
    --output benchmark/results/al_q35_D1.json \
    --k 10 --backend qwen3
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

import agent_v9 as v9_mod  # noqa: E402
import agent_tools_v7 as _t7  # noqa: E402
from infer import get_client, get_model_name  # noqa: E402


DOMAIN_FILES = {
    "D1": "D1_industrial_manifest.json",
    "D2": "D2_retail_manifest.json",
    "D3": "D3_complex_industrial_manifest.json",
    "D4": "D4_infrastructure_manifest.json",
    "D5": "D5_logical_manifest.json",
    "D6": "D6_industrial_3d_manifest.json",
    "D7": "D7_remote_sensing_manifest.json",
    "D8": "D8_dermatology_manifest.json",
    "D9": "D9_brain_mri_manifest.json",
    "D10": "D10_liver_ct_manifest.json",
    "D11": "D11_gi_endoscopy_manifest.json",
    "D12": "D12_road_safety_manifest.json",
}


def dinov2_embed(image_path, device="cuda"):
    """Return L2-normalised DINOv2 CLS embedding (384d)."""
    from PIL import Image
    import numpy as np
    import torch
    model, transform = _t7._load_retrieval_model_v6(device)
    img = Image.open(image_path).convert("RGB")
    t = transform(img).unsqueeze(0).to(device)
    with torch.no_grad():
        e = model(t).cpu().numpy().flatten()
    return e / (np.linalg.norm(e) + 1e-8)


def build_fewshot_context(oracle_pool, query_image, k=3):
    """Retrieve top-k labelled neighbors by DINOv2 similarity.

    oracle_pool: list of dicts {item_id, query_path, label, rationale}
        each augmented with .embed (np.array 384).
    Returns a list of dicts {query_path, label, rationale, similarity}.
    """
    import numpy as np
    q_emb = dinov2_embed(query_image)
    sims = np.array([float(q_emb @ x["embed"]) for x in oracle_pool])
    if len(oracle_pool) == 0:
        return []
    top_idx = np.argsort(sims)[::-1][:k]
    return [{"query_path": oracle_pool[i]["query_path"],
             "label": oracle_pool[i]["label"],
             "rationale": oracle_pool[i].get("rationale", ""),
             "similarity": float(sims[i])} for i in top_idx]


def run_one(client, model, item, split, max_turns, fewshot=None):
    """Wrap v9 runner with optional fewshot injection (thread-safe via kwarg)."""
    return v9_mod.run_v9_item(client, model, item, split, max_turns,
                              fewshot_context=fewshot)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest_dir", default="benchmark/manifests_v2")
    ap.add_argument("--domain", required=True, choices=list(DOMAIN_FILES))
    ap.add_argument("--backend", default="qwen3")
    ap.add_argument("--output", required=True)
    ap.add_argument("--k", type=int, default=10, help="oracle queries per domain")
    ap.add_argument("--fewshot_k", type=int, default=3)
    ap.add_argument("--max_turns", type=int, default=4)
    ap.add_argument("--max_workers", type=int, default=6)
    ap.add_argument("--selection", choices=["random", "uncertainty"],
                    default="uncertainty")
    ap.add_argument("--skip_passive", action="store_true",
                    help="Reuse existing passive result file if present.")
    args = ap.parse_args()

    manifest = json.load(open(os.path.join(args.manifest_dir,
                                           DOMAIN_FILES[args.domain])))
    dev_items = [x for x in manifest if x.get("split") == "dev"]
    test_items = [x for x in manifest if x.get("split") == "test"]
    print(f"[AL] domain={args.domain} dev={len(dev_items)} test={len(test_items)}",
          flush=True)

    client = get_client(args.backend)
    model = get_model_name(args.backend)

    # -------- Passive pass on TEST --------
    passive_path = args.output.replace(".json", "_passive.json")
    if args.skip_passive and os.path.exists(passive_path):
        passive = json.load(open(passive_path))
        print(f"[AL] reusing passive: {len(passive)} items", flush=True)
    else:
        def _passive(x):
            try:
                r = v9_mod.run_v9_item(client, model, x, "test",
                                       args.max_turns)
                return {"item_id": r.item_id, "score": r.score,
                        "label_gt": x.get("label"),
                        "domain_code": x.get("domain_code"),
                        "rationale": r.rationale, "n_turns": r.n_turns,
                        "error": r.error}
            except Exception as e:
                return {"item_id": x["item_id"], "score": 0.5,
                        "label_gt": x.get("label"),
                        "error": f"{type(e).__name__}: {e}"}
        passive: list = []
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
            futs = [ex.submit(_passive, x) for x in test_items]
            for i, f in enumerate(as_completed(futs)):
                passive.append(f.result())
                if (i + 1) % 20 == 0:
                    print(f"[passive {args.domain}] {i+1}/{len(test_items)} "
                          f"t={time.time()-t0:.0f}s", flush=True)
        Path(passive_path).parent.mkdir(parents=True, exist_ok=True)
        with open(passive_path, "w") as f:
            json.dump(passive, f)

    # -------- Select oracle queries from DEV --------
    # First run agent on dev to get scores for uncertainty
    print(f"[AL] running on dev ({len(dev_items)}) for selection", flush=True)

    def _dev(x):
        try:
            r = v9_mod.run_v9_item(client, model, x, "dev", args.max_turns)
            return {"item_id": r.item_id, "query_path": x["query_path"],
                    "label": x.get("label"), "score": r.score,
                    "rationale": r.rationale, "error": r.error}
        except Exception as e:
            return {"item_id": x["item_id"], "query_path": x["query_path"],
                    "label": x.get("label"), "score": 0.5,
                    "rationale": "", "error": f"{type(e).__name__}: {e}"}

    dev_results = []
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futs = [ex.submit(_dev, x) for x in dev_items]
        for f in as_completed(futs):
            dev_results.append(f.result())

    if args.selection == "random":
        import random
        random.seed(42)
        oracle = random.sample(dev_results, args.k)
    else:
        dev_results.sort(key=lambda d: abs((d.get("score") or 0.5) - 0.5))
        oracle = dev_results[:args.k]

    # Embed oracle pool
    print(f"[AL] embedding {len(oracle)} oracle items", flush=True)
    for d in oracle:
        try:
            d["embed"] = dinov2_embed(d["query_path"])
        except Exception as e:
            d["embed"] = None
            d["embed_error"] = str(e)
    oracle = [d for d in oracle if d.get("embed") is not None]

    # -------- Active pass on TEST --------
    print(f"[AL] running active pass on TEST with {len(oracle)} neighbors",
          flush=True)
    import numpy as np

    def _active(x):
        try:
            ctx = build_fewshot_context(oracle, x["query_path"],
                                        k=args.fewshot_k)
            r = run_one(client, model, x, "test", args.max_turns, fewshot=ctx)
            return {"item_id": r.item_id, "score": r.score,
                    "label_gt": x.get("label"),
                    "domain_code": x.get("domain_code"),
                    "fewshot": [{"p": c["query_path"], "l": c["label"],
                                 "s": c["similarity"]} for c in ctx],
                    "rationale": r.rationale, "n_turns": r.n_turns,
                    "error": r.error}
        except Exception as e:
            return {"item_id": x["item_id"], "score": 0.5,
                    "label_gt": x.get("label"),
                    "error": f"{type(e).__name__}: {e}"}

    active: list = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futs = [ex.submit(_active, x) for x in test_items]
        for i, f in enumerate(as_completed(futs)):
            active.append(f.result())
            if (i + 1) % 20 == 0:
                print(f"[active {args.domain}] {i+1}/{len(test_items)} "
                      f"t={time.time()-t0:.0f}s", flush=True)

    # Drop embed arrays before dumping
    oracle_out = [{k: v for k, v in d.items() if k != "embed"} for d in oracle]
    out = {
        "domain": args.domain,
        "k": args.k,
        "fewshot_k": args.fewshot_k,
        "selection": args.selection,
        "oracle_items": oracle_out,
        "passive": passive,
        "active": active,
    }

    # Compute AUROC
    try:
        from sklearn.metrics import roc_auc_score
        passive_map = {r["item_id"]: r for r in passive}
        ids_with_label = [r["item_id"] for r in active
                          if r.get("label_gt") is not None]
        oracle_ids = {d["item_id"] for d in oracle}
        # Exclude oracle items from eval (none should appear in test anyway,
        # since oracle comes from dev)
        hold = [r for r in active
                if r["item_id"] not in oracle_ids
                and r.get("label_gt") is not None]
        y = [int(r["label_gt"]) for r in hold]
        s_active = [float(r["score"]) for r in hold]
        s_passive = [float(passive_map[r["item_id"]]["score"]) for r in hold
                     if r["item_id"] in passive_map]
        y_passive = [int(passive_map[r["item_id"]]["label_gt"]) for r in hold
                     if r["item_id"] in passive_map]
        out["auroc_active"] = float(roc_auc_score(y, s_active))
        out["auroc_passive"] = float(roc_auc_score(y_passive, s_passive))
        out["delta_auroc"] = out["auroc_active"] - out["auroc_passive"]
        print(f"[AL {args.domain}] passive AUROC={out['auroc_passive']:.4f} "
              f"active AUROC={out['auroc_active']:.4f} "
              f"Δ={out['delta_auroc']:+.4f}", flush=True)
    except Exception as e:
        out["auroc_error"] = str(e)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(out, f, default=str)
    print(f"[AL] wrote {args.output}")


if __name__ == "__main__":
    main()
