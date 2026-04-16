import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmark" / "scripts"))
from eval_v6 import (  # noqa: E402
    macro_auroc, bootstrap_ci_per_domain, paired_permutation_test,
    tool_usage_stats,
)


def test_macro_auroc_perfect():
    items = [
        {"domain_code": "D1", "label_gt": 0, "anomaly_score": 0.1},
        {"domain_code": "D1", "label_gt": 1, "anomaly_score": 0.9},
        {"domain_code": "D2", "label_gt": 0, "anomaly_score": 0.2},
        {"domain_code": "D2", "label_gt": 1, "anomaly_score": 0.8},
    ]
    out = macro_auroc(items)
    assert out["macro"] == 1.0
    assert out["per_domain"]["D1"] == 1.0


def test_bootstrap_ci_returns_lohi():
    items = [{"domain_code": "D1", "label_gt": i % 2,
              "anomaly_score": np.random.rand()} for i in range(100)]
    ci = bootstrap_ci_per_domain(items, n_boot=100, seed=0)
    assert "D1" in ci
    lo, hi = ci["D1"]
    assert 0.0 <= lo <= hi <= 1.0


def test_paired_permutation_detects_difference():
    a_items = [{"item_id": f"x{i}", "domain_code": "D1",
                "label_gt": i % 2,
                "anomaly_score": 0.9 if i % 2 else 0.1} for i in range(50)]
    b_items = [{"item_id": f"x{i}", "domain_code": "D1",
                "label_gt": i % 2,
                "anomaly_score": 0.5} for i in range(50)]
    p = paired_permutation_test(a_items, b_items, n_perm=200, seed=0)
    assert p["delta"] > 0
    assert p["p_value"] < 0.1


def test_tool_usage_stats():
    items = [
        {"n_turns": 1, "tools_used": []},
        {"n_turns": 3, "tools_used": ["tool_expert_score", "tool_hotspot_cropper"]},
    ]
    s = tool_usage_stats(items)
    assert s["avg_turns"] == 2.0
    assert s["pct_single_turn_no_tool"] == 50.0
    assert s["tool_call_counts"]["tool_expert_score"] == 1
