"""Quick smoke test for v6: run Direct + Agent on 5 items.
Run after vLLM replicas are up and LB listening on 8210.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from infer import get_client, get_model_name  # noqa: E402
from agent_v6 import ReActAgent  # noqa: E402
from run_baselines_v6 import run_direct_item, load_calibration_median, fuse  # noqa: E402
from agent_tools_v6 import _load_expert_scores  # noqa: E402


def main():
    manifest = Path("/hdd1/jiangxi/AD-Agent/benchmark/manifests/full_manifest.json")
    items = json.load(open(manifest))
    # 5 items: 2 D1 + 2 D2 + 1 D4 from calibration (fast, already have expert cache)
    sample = []
    for dom in ("D1", "D2", "D4"):
        for x in items:
            if x.get("split") == "calibration" and x.get("domain_code") == dom:
                sample.append(x)
                if sum(1 for s in sample if s["domain_code"] == dom) >= (2 if dom != "D4" else 1):
                    break
    print(f"Sampled {len(sample)} items: {[x['item_id'] for x in sample]}")

    client = get_client("qwen3")
    model = get_model_name("qwen3")
    print(f"Backend: qwen3  model={model}  base_url={client.base_url}")

    # 1. Direct
    print("\n=== DIRECT ===")
    t0 = time.time()
    direct = [run_direct_item(client, model, x) for x in sample]
    for r in direct:
        print(f"  {r['item_id']} dom={r['domain_code']} gt={r['label_gt']} "
              f"score={r['anomaly_score']:.3f} err={r.get('error')}")
    print(f"Direct time: {time.time()-t0:.1f}s")

    # 2. Fusion
    print("\n=== FUSION ===")
    median = load_calibration_median()
    recs, _ = _load_expert_scores("subspacead", "calibration")
    for r in direct:
        e = recs.get(r["item_id"], {}).get("anomaly_score")
        f = fuse(r["anomaly_score"], e, median, w=0.2)
        print(f"  {r['item_id']} direct={r['anomaly_score']:.3f} "
              f"expert={e} fused={f:.3f}")

    # 3. Agent
    print("\n=== AGENT ===")
    agent = ReActAgent(vlm_client=client, vlm_model=model, max_turns=5)
    t0 = time.time()
    for x in sample:
        t1 = time.time()
        r = agent.run(item_id=x["item_id"], query_path=x["query_path"],
                      ref_paths=x["ref_paths"], split="calibration",
                      domain_code=x["domain_code"])
        dt = time.time() - t1
        print(f"  {x['item_id']} gt={x['label']} "
              f"score={r.score:.3f} turns={r.n_turns} "
              f"tools={r.tools_used} conf={r.confidence} "
              f"({dt:.1f}s) err={r.error}")
    print(f"Total agent time: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
