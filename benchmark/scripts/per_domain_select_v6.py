"""Per-domain variant selector.

For each of 12 domains, pick {anchor, l2, or passive_v12} with highest
dev macro AUROC. Apply that selection to test results. Compute final
macro AUROC and paired bootstrap 95% CI vs v12 Passive.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

DOMAINS = ["D1","D5","D2","D6","D3","D4","D7","D8","D9","D10","D11","D12"]
ROOT = Path("/hdd1/jiangxi/AD-Agent/benchmark/results")


def load_dir(p, item_key="item_id", label_key="label_gt", score_key="anomaly_score"):
    """Return {D: list of (item_id, label, score)}."""
    out = {}
    for D in DOMAINS:
        # try several filename patterns
        for cand in [f"{D}.json", f"{D}_v6_anchor.json", f"{D}_v6_l2.json"]:
            f = p / cand
            if f.exists() and f.stat().st_size > 1000:
                r = json.load(open(f))
                rows = []
                for x in r:
                    lbl = x.get(label_key)
                    if lbl is None:
                        lbl = x.get("label")
                    sc = x.get(score_key)
                    if x.get("error") is not None:
                        continue
                    if lbl is None or sc is None:
                        continue
                    rows.append((x.get(item_key), int(lbl), float(sc)))
                out[D] = rows
                break
        else:
            out[D] = None
    return out


def per_domain_auroc(d):
    out = {}
    for D in DOMAINS:
        rows = d.get(D)
        if not rows: out[D] = None; continue
        y = [r[1] for r in rows]; s = [r[2] for r in rows]
        if len(set(y)) < 2: out[D] = None
        else:
            try: out[D] = float(roc_auc_score(y, s))
            except: out[D] = None
    return out


def stratified_paired_bootstrap(per_dom_a, per_dom_b, n_boot=1000, seed=0):
    rng = np.random.default_rng(seed)
    deltas = []
    common = [D for D in DOMAINS if per_dom_a.get(D) and per_dom_b.get(D)]
    pairs_by_dom = {}
    for D in common:
        a_map = {r[0]: r for r in per_dom_a[D]}
        b_map = {r[0]: r for r in per_dom_b[D]}
        ids = sorted(a_map.keys() & b_map.keys())
        pairs_by_dom[D] = [(i, a_map[i], b_map[i]) for i in ids]
    for _ in range(n_boot):
        macro_a = []; macro_b = []
        for D in common:
            pairs = pairs_by_dom[D]
            n = len(pairs)
            idx = rng.integers(0, n, n)
            ya = [pairs[i][1][1] for i in idx]; sa = [pairs[i][1][2] for i in idx]
            yb = [pairs[i][2][1] for i in idx]; sb = [pairs[i][2][2] for i in idx]
            if len(set(ya)) < 2 or len(set(yb)) < 2: continue
            macro_a.append(roc_auc_score(ya, sa))
            macro_b.append(roc_auc_score(yb, sb))
        if macro_a and macro_b:
            deltas.append(np.mean(macro_b) - np.mean(macro_a))
    deltas = np.array(deltas)
    return float(np.percentile(deltas, 2.5)), float(np.percentile(deltas, 97.5)), float((deltas>0).mean()), float(deltas.mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev_anchor", default=str(ROOT / "verbalized/v6_dev_anchor"))
    ap.add_argument("--dev_l2",     default=str(ROOT / "verbalized/v6_dev_l2"))
    ap.add_argument("--dev_passive",default=str(ROOT / "verbalized/v12_passive_dev"))
    ap.add_argument("--test_anchor",default=str(ROOT / "verbalized/v6_test_anchor"))
    ap.add_argument("--test_l2",    default=str(ROOT / "verbalized/v6_test_l2"))
    ap.add_argument("--test_passive",default=str(ROOT / "v2/v12_passive_test"))
    ap.add_argument("--n_boot", type=int, default=1000)
    args = ap.parse_args()

    # Load dev
    dev_anchor = load_dir(Path(args.dev_anchor))
    dev_l2     = load_dir(Path(args.dev_l2))
    dev_passive= load_dir(Path(args.dev_passive))

    test_anchor = load_dir(Path(args.test_anchor))
    test_l2     = load_dir(Path(args.test_l2))
    test_passive= load_dir(Path(args.test_passive))

    # Dev macro per variant
    print("\n=== Dev AUROC per domain ===")
    print(f"{'D':<5}{'Passive':>10}{'+Anchor':>10}{'+L2':>10}{'pick':>10}")
    selection = {}
    for D in DOMAINS:
        a_p = per_domain_auroc({D: dev_passive.get(D)}).get(D)
        a_a = per_domain_auroc({D: dev_anchor.get(D)}).get(D)
        a_l = per_domain_auroc({D: dev_l2.get(D)}).get(D)
        cands = [("passive", a_p), ("anchor", a_a), ("l2", a_l)]
        cands_valid = [(n,v) for n,v in cands if v is not None]
        if not cands_valid:
            selection[D] = "passive"
            continue
        # Among non-None, pick max
        pick = max(cands_valid, key=lambda x: x[1])[0]
        selection[D] = pick
        print(f"{D:<5}{a_p if a_p is not None else '----':>10}{a_a if a_a is not None else '----':>10}"
              f"{a_l if a_l is not None else '----':>10}{pick:>10}")

    # Build per-domain selected test results
    selected_test = {}
    for D in DOMAINS:
        pick = selection.get(D, "passive")
        if pick == "passive":   src = test_passive
        elif pick == "anchor":  src = test_anchor
        elif pick == "l2":      src = test_l2
        else:                   src = test_passive
        selected_test[D] = src.get(D)

    # Compute per-domain test AUROC for final selection
    print("\n=== Test AUROC ===")
    print(f"{'D':<5}{'Passive':>10}{'+Anchor':>10}{'+L2':>10}{'sel':>10}{'Δ vs P':>10}")
    pass_aurocs = []; sel_aurocs = []; anch_aurocs = []; l2_aurocs = []
    for D in DOMAINS:
        ap_v = per_domain_auroc({D: test_passive.get(D)}).get(D)
        an_v = per_domain_auroc({D: test_anchor.get(D)}).get(D)
        l2_v = per_domain_auroc({D: test_l2.get(D)}).get(D)
        sel_v = per_domain_auroc({D: selected_test.get(D)}).get(D)
        if ap_v is not None: pass_aurocs.append(ap_v)
        if an_v is not None: anch_aurocs.append(an_v)
        if l2_v is not None: l2_aurocs.append(l2_v)
        if sel_v is not None: sel_aurocs.append(sel_v)
        delta = (sel_v - ap_v) * 100 if (sel_v is not None and ap_v is not None) else None
        print(f"{D:<5}{ap_v if ap_v is not None else '-':>10.4f}{an_v if an_v is not None else '-':>10.4f}"
              f"{l2_v if l2_v is not None else '-':>10.4f}{selection.get(D, '-'):>10}"
              f"{(delta if delta is not None else 0):>+10.2f}")

    print(f"\nMacro Passive: {np.mean(pass_aurocs):.4f}")
    print(f"Macro +Anchor: {np.mean(anch_aurocs):.4f}  Δ={np.mean(anch_aurocs)*100-np.mean(pass_aurocs)*100:+.2f}pp")
    print(f"Macro +L2:     {np.mean(l2_aurocs):.4f}  Δ={np.mean(l2_aurocs)*100-np.mean(pass_aurocs)*100:+.2f}pp")
    print(f"Macro Selected (dev-based per-domain): {np.mean(sel_aurocs):.4f}  "
          f"Δ={np.mean(sel_aurocs)*100-np.mean(pass_aurocs)*100:+.2f}pp")

    # Bootstrap CI
    if all(test_passive.get(D) for D in DOMAINS) and all(selected_test.get(D) for D in DOMAINS):
        lo, hi, p, mu = stratified_paired_bootstrap(test_passive, selected_test, n_boot=args.n_boot)
        print(f"\nPaired bootstrap CI (Selected vs Passive): "
              f"Δ={mu*100:+.2f}pp [{lo*100:+.2f}, {hi*100:+.2f}], P(Δ>0)={p:.3f}")


if __name__ == "__main__":
    main()
