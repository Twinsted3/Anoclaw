"""Post-hoc compose an EGRA result file from v0_direct + v3_debate_1r.

Escalation trigger (G1): escalate to the two-call debate if either
  (A) the v0 score is in the ambiguous band [tau_low, tau_high], OR
  (B) FN-catcher: v0 predicts normal (s0 < 0.5) AND the DINOv2 patch
      global_score (min-max normalised over the calibration set) is
      above a threshold ptn --- the patch expert is screaming
      anomaly while v0 is confident it is normal.

Aggregation (G2): gated factorised rule c * (1 - r) with high-trust
override when c >= tau_trust = 0.8 (see paper method section).

Output file has the same schema as any other result file, so
evaluate.py can be run on it directly.
"""
import argparse
import json
from pathlib import Path


def gated_debate_score(v1, refuter, high_trust=0.8):
    if not v1:
        return 0.5
    claims = v1.get("claims", [])
    if not claims:
        label = str(v1.get("image_label", "")).lower()
        return 0.05 if label == "normal" else 0.6
    reviews = {r.get("id"): float(r.get("refute_confidence", 0.0))
               for r in (refuter or {}).get("reviews", [])}
    best = 0.0
    for c in claims:
        conf = float(c.get("confidence", 0.0))
        rc = reviews.get(c.get("id", ""), 0.0)
        scored = conf if conf >= high_trust else conf * (1.0 - rc)
        if scored > best:
            best = scored
    return float(max(0.0, min(1.0, best)))


def load_patch_cache(path):
    if not path:
        return None, None, None
    try:
        cache = json.load(open(path))
    except FileNotFoundError:
        return None, None, None
    scores = [e.get("global_score") for e in cache.values()
              if isinstance(e.get("global_score"), (int, float))]
    if not scores:
        return cache, None, None
    return cache, float(min(scores)), float(max(scores))


def compose(v0_path, v3_path, out_path, tau_low=0.20, tau_high=0.85,
            patch_cache_path=None, ptn=0.60):
    v0 = {x["item_id"]: x for x in json.load(open(v0_path))}
    v3 = {x["item_id"]: x for x in json.load(open(v3_path))}
    cache, pmin, pmax = load_patch_cache(patch_cache_path)
    denom = (pmax - pmin) if (pmin is not None and pmax is not None and pmax > pmin) else 1.0

    out = []
    n_esc_band = n_esc_fn = n_esc = 0
    for iid, v0_item in v0.items():
        s0 = float(v0_item.get("anomaly_score", 0.5))
        # Trigger A: band
        in_band = (tau_low <= s0 <= tau_high)
        # Trigger B: FN-catcher (v0 says normal but patch strongly disagrees)
        fn_catch = False
        if cache is not None and pmin is not None:
            entry = cache.get(iid) or {}
            gs = entry.get("global_score")
            if isinstance(gs, (int, float)):
                gs_norm = (gs - pmin) / denom if denom > 0 else 0.5
                if s0 < 0.5 and gs_norm >= ptn:
                    fn_catch = True

        escalate = in_band or fn_catch
        if not escalate:
            new_item = dict(v0_item)
            new_item["path"] = "v0_only"
            out.append(new_item)
            continue

        v3_item = v3.get(iid)
        if not v3_item:
            # v3 missing for this id — fall back to v0
            out.append(v0_item)
            continue
        raw = v3_item.get("raw_output") or {}
        s_gated = gated_debate_score(raw.get("v1"), raw.get("refuter"))
        new_item = dict(v3_item)
        new_item["anomaly_score"] = s_gated
        new_item["label_pred"] = 1 if s_gated >= 0.5 else 0
        new_item["anomaly_score_v0"] = s0
        new_item["path"] = "v0+v3_gated" + ("_band" if in_band else "") + ("_fn" if fn_catch else "")
        out.append(new_item)
        n_esc += 1
        if in_band: n_esc_band += 1
        if fn_catch: n_esc_fn += 1

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(out_path, "w"), indent=2)
    print(f"composed {len(out)} items, escalated {n_esc}/{len(out)} "
          f"({n_esc/len(out)*100:.1f}%) -> {out_path}")
    print(f"  breakdown: band={n_esc_band}  fn_catch={n_esc_fn}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v0", required=True)
    ap.add_argument("--v3", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--tau-low", type=float, default=0.20)
    ap.add_argument("--tau-high", type=float, default=0.85)
    ap.add_argument("--patch-cache", default=None,
                    help="JSON file from build_patch_evidence_cache.py; enables FN-catcher trigger")
    ap.add_argument("--ptn", type=float, default=0.60,
                    help="patch normalised threshold for FN-catcher")
    args = ap.parse_args()
    compose(args.v0, args.v3, args.output,
            tau_low=args.tau_low, tau_high=args.tau_high,
            patch_cache_path=args.patch_cache, ptn=args.ptn)


if __name__ == "__main__":
    main()
