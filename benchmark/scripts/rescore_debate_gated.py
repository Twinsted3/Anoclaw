"""Re-score debate results with a confidence-gated refuter policy.

Rule: trust the proposer outright when its top confidence is outside the
ambiguous band (c < low or c > high). Only use the refuter to attenuate the
score inside the band.

This is a post-hoc re-scoring; no new VLM calls. It lets us sweep the band
on the calibration split and pick the best (low, high) before running on
test.
"""
import argparse
import json
from pathlib import Path
from sklearn.metrics import roc_auc_score


def score_gated(proposer, refuter, low=0.3, high=0.8):
    if not proposer:
        return 0.5
    claims = proposer.get("claims", [])
    if not claims:
        label = str(proposer.get("image_label", "")).lower()
        return 0.05 if label == "normal" else 0.6
    # Match refuter reviews by id
    reviews = {}
    if refuter:
        for r in refuter.get("reviews", []):
            reviews[r.get("id")] = float(r.get("refute_confidence", 0.0))
    best = 0.0
    for c in claims:
        conf = float(c.get("confidence", 0.0))
        rc = reviews.get(c.get("id", ""), 0.0)
        if low <= conf <= high:
            # Ambiguous: apply refuter attenuation
            scored = conf * (1.0 - rc)
        else:
            # Confident (either high-conf anomaly or low-conf): trust proposer
            scored = conf
        best = max(best, scored)
    return float(max(0.0, min(1.0, best)))


def evaluate_auroc(items, low, high):
    y_true = []
    y_score = []
    for item in items:
        raw = item.get("raw_output") or {}
        v1 = raw.get("v1") or raw.get("v1_grounded")
        refuter = raw.get("refuter")
        if v1 is None:
            continue
        s = score_gated(v1, refuter, low, high)
        y_true.append(item.get("label_gt"))
        y_score.append(s)
    if len(set(y_true)) < 2:
        return None
    return roc_auc_score(y_true, y_score)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--sweep", action="store_true", help="sweep (low, high) band")
    ap.add_argument("--low", type=float, default=0.3)
    ap.add_argument("--high", type=float, default=0.8)
    args = ap.parse_args()

    items = json.load(open(args.input))

    if args.sweep:
        print(f"Sweeping band on {args.input}")
        print(f"{'low':>5s} {'high':>5s} {'AUROC':>6s}")
        for low in [0.0, 0.2, 0.3, 0.4, 0.5]:
            for high in [0.6, 0.7, 0.8, 0.9, 1.0]:
                if low >= high:
                    continue
                a = evaluate_auroc(items, low, high)
                if a is not None:
                    print(f"{low:>5.2f} {high:>5.2f} {a:>6.3f}")
    else:
        a = evaluate_auroc(items, args.low, args.high)
        print(f"AUROC @ low={args.low} high={args.high}: {a:.3f}")


if __name__ == "__main__":
    main()
