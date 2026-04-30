#!/usr/bin/env python3
"""
Reproduce the final AnomaClaw results from saved inference outputs.

Reads calibration and test JSON files, tunes family-adaptive fusion weights
on the calibration split, and evaluates on the test split.

Usage:
    python reproduce_final_results.py
"""

import json
import numpy as np
from pathlib import Path
from sklearn.metrics import roc_auc_score

RESULTS_DIR = Path(__file__).parent.parent / "results" / "v4"
KEEP_DOMAINS = ['D1', 'D5', 'D6', 'D3', 'D3b', 'D3c', 'D3d', 'D7', 'D9', 'D10']

ANOMALY_FAMILY = {
    "D1": "local_appearance", "D5": "local_appearance",
    "D6": "local_appearance", "D10": "local_appearance",
    "D3": "semantic_medical", "D3b": "semantic_medical",
    "D3c": "semantic_medical", "D3d": "semantic_medical",
    "D7": "semantic_scene",
    "D9": "logical_structural",
}

FAMILIES = ["local_appearance", "semantic_medical", "semantic_scene", "logical_structural"]


def load_and_filter(filename):
    with open(RESULTS_DIR / filename) as f:
        data = json.load(f)
    return [r for r in data if r['domain_code'] in KEEP_DOMAINS]


def domain_auroc(data, domain):
    rows = [r for r in data if r['domain_code'] == domain]
    gt = [r['label_gt'] for r in rows]
    scores = [r['anomaly_score'] for r in rows]
    if len(set(gt)) < 2:
        return float('nan')
    return roc_auc_score(gt, scores)


def macro_auroc(data):
    aucs = [domain_auroc(data, d) for d in KEEP_DOMAINS]
    return np.mean(aucs), {d: a for d, a in zip(KEEP_DOMAINS, aucs)}


def get_expert_vlm_scores(informed_data):
    """Extract per-item expert and VLM scores from expert_informed output."""
    items = []
    for r in informed_data:
        raw = r.get('raw_output', {})
        expert_score = raw.get('expert', {}).get('anomaly_score', r['anomaly_score'])
        vlm_score = raw.get('vlm_score', r['anomaly_score'])
        items.append({
            'domain_code': r['domain_code'],
            'label_gt': r['label_gt'],
            'expert_score': expert_score,
            'vlm_score': vlm_score,
        })
    return items


def tune_family_alphas(calib_items):
    """Grid search for family-specific fusion weights on calibration split."""
    alphas = {}
    for family in FAMILIES:
        family_items = [it for it in calib_items if ANOMALY_FAMILY.get(it['domain_code']) == family]
        if not family_items:
            alphas[family] = 0.0
            continue
        gt = [it['label_gt'] for it in family_items]
        if len(set(gt)) < 2:
            alphas[family] = 0.0
            continue

        best_alpha, best_auc = 0.0, 0.0
        for alpha_int in range(0, 101, 5):
            alpha = alpha_int / 100.0
            scores = [alpha * it['expert_score'] + (1 - alpha) * it['vlm_score'] for it in family_items]
            auc = roc_auc_score(gt, scores)
            if auc > best_auc:
                best_auc = auc
                best_alpha = alpha
        alphas[family] = best_alpha
    return alphas


def apply_fusion(test_items, alphas):
    """Apply family-adaptive fusion to test items."""
    fused = []
    for it in test_items:
        family = ANOMALY_FAMILY.get(it['domain_code'], 'local_appearance')
        alpha = alphas.get(family, 0.0)
        score = alpha * it['expert_score'] + (1 - alpha) * it['vlm_score']
        fused.append({
            'domain_code': it['domain_code'],
            'label_gt': it['label_gt'],
            'anomaly_score': score,
        })
    return fused


def bootstrap_ci(aucs, n_boot=10000, seed=42):
    rng = np.random.default_rng(seed)
    arr = np.array(aucs)
    boot_means = [np.mean(arr[rng.choice(len(arr), len(arr), replace=True)]) for _ in range(n_boot)]
    return np.percentile(boot_means, [2.5, 97.5])


def main():
    print("=" * 60)
    print("AnomaClaw Final Results Reproduction")
    print("=" * 60)

    # Load data
    calib_data = load_and_filter("expert_informed_calib.json")
    test_data = load_and_filter("expert_informed_test.json")
    print(f"\nCalibration: {len(calib_data)} items")
    print(f"Test: {len(test_data)} items")

    # Expert-Informed VLM (no fusion)
    macro, per_domain = macro_auroc(test_data)
    print(f"\n--- Expert-Informed VLM (no fusion) ---")
    print(f"Macro AUROC: {macro:.4f}")
    for d in KEEP_DOMAINS:
        print(f"  {d}: {per_domain[d]:.4f}")

    # Tune family alphas on calibration
    calib_items = get_expert_vlm_scores(calib_data)
    test_items = get_expert_vlm_scores(test_data)
    alphas = tune_family_alphas(calib_items)
    print(f"\n--- Calibrated Family Alphas ---")
    for f, a in alphas.items():
        print(f"  {f}: {a:.2f}")

    # Apply fusion to test
    fused_test = apply_fusion(test_items, alphas)
    fused_macro, fused_per = macro_auroc(fused_test)
    fused_aucs = [fused_per[d] for d in KEEP_DOMAINS]
    ci = bootstrap_ci(fused_aucs)

    print(f"\n--- Cal-Tuned Fusion (final result) ---")
    print(f"Macro AUROC: {fused_macro:.4f} [{ci[0]:.3f}, {ci[1]:.3f}]")
    for d in KEEP_DOMAINS:
        print(f"  {d}: {fused_per[d]:.4f}")

    # Save metrics
    metrics = {
        "method": "Cal-Tuned Family-Adaptive Fusion (reproduced)",
        "macro_auroc": round(fused_macro, 4),
        "ci_95": [round(ci[0], 3), round(ci[1], 3)],
        "cal_alphas": alphas,
        "per_domain": {d: round(fused_per[d], 4) for d in KEEP_DOMAINS},
        "n_test": len(test_data),
        "n_calib": len(calib_data),
        "domains": KEEP_DOMAINS,
    }
    out_path = RESULTS_DIR / "reproduced_final_metrics.json"
    with open(out_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"\nSaved to: {out_path}")


if __name__ == "__main__":
    main()
