"""Aggregate macro AUROC from a v12 passive-test directory.

This is the canonical paper-aggregation script. Given a directory of
``D{1..12}.json`` produced by ``agent_v12.py`` in Passive mode (no
``--learning_enabled``), it filters to AD-mode items with both branch
scores populated, re-blends them with the paper's α=0.5, and reports
per-domain plus macro AUROC.

Usage:
  python benchmark/scripts/aggregate_v12.py \
      --results benchmark/results/v2/v12_passive_test

Reproduces the paper §4 Table 1 main-results numbers exactly:

  v12_passive_test         (Qwen3.5-VL-27B) → macro 0.7480
  v12_passive_test_seedvl  (Seed2.0-lite)   → macro 0.7672
  v12_passive_gpt55_test   (GPT-5.5)        → macro 0.8135
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import re
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score


def load_dir(path: Path) -> list[dict]:
    rows: list[dict] = []
    files = sorted(
        glob.glob(str(path / "D*.json")),
        key=lambda x: int(re.search(r"D(\d+)\.json", x).group(1)),
    )
    for f in files:
        rows.extend(json.load(open(f)))
    return rows


def filter_ok(rows: list[dict]) -> list[dict]:
    """Paper's AD-mode filter: keep rows with both branch scores."""
    return [
        x for x in rows
        if x.get("mode") == "anomaly_detection"
        and x.get("direct_score") is not None
        and x.get("v9_score") is not None
        and not x.get("error")
        and x.get("label_gt") is not None
    ]


def blend(x: dict, alpha: float = 0.5) -> float:
    return alpha * x["direct_score"] + (1 - alpha) * x["v9_score"]


def per_domain_auroc(rows: list[dict], scorer):
    out: dict[str, tuple[float, int]] = {}
    by_dom: dict[str, list[dict]] = collections.defaultdict(list)
    for x in rows:
        by_dom[x["domain_code"]].append(x)
    for dc, items in by_dom.items():
        y = np.array([x["label_gt"] for x in items])
        if len(set(y)) < 2:
            continue
        s = np.array([scorer(x) for x in items])
        out[dc] = (float(roc_auc_score(y, s)), len(items))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--results", type=Path, required=True,
                    help="Directory of per-domain D*.json result files")
    ap.add_argument("--alpha", type=float, default=0.5,
                    help="Blend weight for direct_score; v9_score gets 1-alpha")
    args = ap.parse_args()

    all_rows = load_dir(args.results)
    ok = filter_ok(all_rows)
    n_err = sum(1 for r in all_rows if r.get("error"))

    def _scorer(x: dict) -> float:
        return blend(x, args.alpha)

    direct = per_domain_auroc(ok, lambda x: x["direct_score"])
    v9     = per_domain_auroc(ok, lambda x: x["v9_score"])
    blend_ = per_domain_auroc(ok, _scorer)

    print(f"Source: {args.results}")
    print(f"Rows total / AD-mode usable / errors: {len(all_rows)} / {len(ok)} / {n_err}")
    print(f"Blend weights: α={args.alpha} on direct_score, {1-args.alpha} on v9_score\n")
    print(f"{'Domain':<7} {'Direct':>8} {'v9':>8} {'Blend':>8} {'n':>5}")
    for dc in sorted(blend_, key=lambda d: int(d[1:])):
        bd, n = blend_[dc]
        dd, _ = direct.get(dc, (float("nan"), n))
        vd, _ = v9.get(dc, (float("nan"), n))
        print(f"{dc:<7} {dd:>8.4f} {vd:>8.4f} {bd:>8.4f} {n:>5d}")

    macro_direct = float(np.mean([a for a, _ in direct.values()]))
    macro_v9     = float(np.mean([a for a, _ in v9.values()]))
    macro_blend  = float(np.mean([a for a, _ in blend_.values()]))
    print(f"\n{'macro':<7} {macro_direct:>8.4f} {macro_v9:>8.4f} {macro_blend:>8.4f}")


if __name__ == "__main__":
    main()
