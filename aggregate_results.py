#!/usr/bin/env python3
"""
Aggregate experiment results into paper-ready tables.
Reads from result/experiments/*_results.json and generates:
- Table 3: Main results (all methods × all domains)
- Table 7: Multi-VLM comparison
- Summary statistics
"""

import json
import os
import sys
from collections import defaultdict

import numpy as np

RESULT_DIR = "result/experiments"
DOMAINS = [f"D{i}" for i in range(1, 13)]
DOMAIN_NAMES = {
    "D1": "MVTec", "D5": "Goods", "D2": "VisA", "D6": "SDNET",
    "D3": "LOCO", "D4": "Real3D", "D7": "LEVIR", "D8": "Derm",
    "D9": "Brain", "D10": "Liver", "D11": "GI", "D12": "Road"
}

# Method display order for Table 3
TABLE3_ORDER = [
    ("clip_zeroshot", "CLIP-ZeroShot"),
    ("patchcore", "PatchCore"),
    ("vlm_direct_seedvl", "VLM-Direct"),
    ("retrieval_vlm_seedvl", "Retrieval+VLM"),
    ("expert_vlm_seedvl", "Expert+VLM"),
    ("symmetric_debate_seedvl", "Symmetric Debate"),
    ("anomaclaw_seedvl", "AnomalyClaw"),
]


def load_all_results():
    results = {}
    for f in os.listdir(RESULT_DIR):
        if f.endswith("_results.json"):
            with open(os.path.join(RESULT_DIR, f)) as fh:
                d = json.load(fh)
                results[d["tag"]] = d
    return results


def print_table3(results):
    """Main results table."""
    print("\n" + "=" * 120)
    print("TABLE 3: Main Results (AUROC) — Seed2.0-Lite Backend")
    print("=" * 120)

    # Header
    header = f"{'Method':<22}"
    for d in DOMAINS:
        header += f" {DOMAIN_NAMES[d]:>6}"
    header += f" {'Macro':>7}"
    print(header)
    print("-" * 120)

    for tag, name in TABLE3_ORDER:
        if tag not in results:
            row = f"{name:<22}"
            for d in DOMAINS:
                row += f" {'—':>6}"
            row += f" {'—':>7}"
            print(row)
            continue

        data = results[tag]
        row = f"{name:<22}"
        for d in DOMAINS:
            v = data["domain_aurocs"].get(d, float("nan"))
            if np.isnan(v):
                row += f" {'—':>6}"
            else:
                row += f" {v:>6.3f}"
        row += f" {data['macro_auroc']:>7.4f}"
        print(row)

    print("-" * 120)

    # Compute improvement over VLM-Direct
    if "anomaclaw_seedvl" in results and "vlm_direct_seedvl" in results:
        ac = results["anomaclaw_seedvl"]
        vd = results["vlm_direct_seedvl"]
        diff = ac["macro_auroc"] - vd["macro_auroc"]
        print(f"\nAnomalyClaw vs VLM-Direct: {diff:+.4f} macro AUROC")

    if "anomaclaw_seedvl" in results and "expert_vlm_seedvl" in results:
        ac = results["anomaclaw_seedvl"]
        ev = results["expert_vlm_seedvl"]
        diff = ac["macro_auroc"] - ev["macro_auroc"]
        print(f"AnomalyClaw vs Expert+VLM: {diff:+.4f} macro AUROC")


def print_table7(results):
    """Multi-VLM generalization table."""
    print("\n" + "=" * 80)
    print("TABLE 7: Multi-VLM Generalization (AUROC)")
    print("=" * 80)

    vlm_backends = {
        "seedvl": "Seed2.0-Lite",
        "gpt4o": "GPT-4o",
        "qwen25vl": "Qwen2.5-VL-7B",
        "qwen35": "Qwen3.5-27B",
    }

    header = f"{'Method':<22} {'Backend':<16} {'Macro':>7} {'Micro':>7}"
    print(header)
    print("-" * 80)

    for backend_key, backend_name in vlm_backends.items():
        for method in ["vlm_direct", "expert_vlm", "anomaclaw"]:
            tag = f"{method}_{backend_key}"
            if tag not in results:
                print(f"{'AnomalyClaw' if method == 'anomaclaw' else 'VLM-Direct':<22} {backend_name:<16} {'—':>7} {'—':>7}")
                continue

            data = results[tag]
            name = {"anomaclaw": "AnomalyClaw", "vlm_direct": "VLM-Direct", "expert_vlm": "Expert+VLM"}.get(method, method)
            print(f"{name:<22} {backend_name:<16} {data['macro_auroc']:>7.4f} {data['micro_auroc']:>7.4f}")

        # Compute gain
        direct_tag = f"vlm_direct_{backend_key}"
        claw_tag = f"anomaclaw_{backend_key}"
        if direct_tag in results and claw_tag in results:
            gain = results[claw_tag]["macro_auroc"] - results[direct_tag]["macro_auroc"]
            print(f"  → Gain:{'':>28} {gain:>+7.4f}")
        print()


def print_summary(results):
    """Quick summary stats."""
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    completed = {k: v for k, v in results.items() if v["completed"] == v["total_items"]}
    running = {k: v for k, v in results.items() if v["completed"] < v["total_items"]}

    print(f"\nCompleted: {len(completed)} experiments")
    for tag in sorted(completed.keys()):
        d = completed[tag]
        print(f"  {tag}: macro={d['macro_auroc']:.4f} ({d['total_items']} items, {d['elapsed_seconds']:.0f}s)")

    if running:
        print(f"\nRunning: {len(running)} experiments")
        for tag in sorted(running.keys()):
            d = running[tag]
            print(f"  {tag}: {d['completed']}/{d['total_items']} items")


def main():
    results = load_all_results()
    if not results:
        print("No results found in", RESULT_DIR)
        sys.exit(1)

    print_summary(results)
    print_table3(results)
    print_table7(results)


if __name__ == "__main__":
    main()
