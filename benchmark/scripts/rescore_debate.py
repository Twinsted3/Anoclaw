"""Re-score existing debate-variant result files using the fixed formula.

Old:  score = clip(0.5 + max_i (c_i - r_i))
      — asymmetric; any positive residual pushes above 0.5, even when refuter dominates.
New:  score = max_i (c_i * (1 - r_i))
      — independent-events factorisation; refuter fully refuting (r=1) drives claim to 0.

Usage:
  python3 benchmark/scripts/rescore_debate.py --input <results.json> --output <rescored.json>
"""
import argparse
import json
from pathlib import Path


def rescore_debate(proposer: dict, refuter: dict) -> float:
    if not proposer:
        return 0.5
    claims = proposer.get("claims", [])
    if not claims:
        label = str(proposer.get("image_label", "")).lower()
        return 0.05 if label == "normal" else 0.6
    reviews = {}
    if refuter:
        for r in refuter.get("reviews", []):
            reviews[r.get("id")] = float(r.get("refute_confidence", 0.0))
    best = 0.0
    for c in claims:
        conf = float(c.get("confidence", 0.0))
        rc = reviews.get(c.get("id", ""), 0.0)
        scored = conf * (1.0 - rc)
        best = max(best, scored)
    return float(max(0.0, min(1.0, best)))


def label_from_score(s: float) -> int:
    return 1 if s >= 0.5 else 0


def rescore_file(path_in: str, path_out: str):
    data = json.load(open(path_in))
    out = []
    n_flipped = 0
    for item in data:
        raw = item.get("raw_output") or {}
        if not isinstance(raw, dict):
            out.append(item)
            continue
        # Try both keys: v3_debate_1r stores under 'v1'; v3_grounded under 'v1_grounded'
        v1 = raw.get("v1") or raw.get("v1_grounded")
        refuter = raw.get("refuter")
        if v1 is None:
            out.append(item)
            continue
        old_score = item.get("anomaly_score")
        new_score = rescore_debate(v1, refuter)
        new_label = label_from_score(new_score)
        if new_label != item.get("label_pred"):
            n_flipped += 1
        new_item = dict(item)
        new_item["anomaly_score"] = new_score
        new_item["label_pred"] = new_label
        new_item["anomaly_score_old"] = old_score
        out.append(new_item)
    Path(path_out).parent.mkdir(parents=True, exist_ok=True)
    with open(path_out, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Rescored {len(out)} items, {n_flipped} labels flipped -> {path_out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    rescore_file(args.input, args.output)


if __name__ == "__main__":
    main()
