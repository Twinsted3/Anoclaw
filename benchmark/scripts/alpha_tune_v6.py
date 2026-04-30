"""Continuous per-domain alpha tuning (Option 1).

For each variant V in {Passive, +Anchor, +L2}:
  - Load per-item (direct_score, v9_score) on dev.
  - Search alpha in [0, 1] step 0.05 → pick alpha_d* that maximizes
    dev AUROC for each domain.
  - On test: blend with alpha_d* per domain, compute macro AUROC and
    paired bootstrap CI vs Passive (alpha=0.5).

Also reports a GLOBAL alpha (single scalar across all domains) for
comparison.
"""
import json
import argparse
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

DOMAINS = ["D1","D5","D2","D6","D3","D4","D7","D8","D9","D10","D11","D12"]
ROOT = Path("/hdd1/jiangxi/AD-Agent/benchmark/results")


def load_branched(p):
    """Return {D: list of (item_id, label, direct_score, v9_score)}."""
    out = {}
    for D in DOMAINS:
        for cand in [f"{D}.json", f"{D}_v6_anchor.json", f"{D}_v6_l2.json", f"{D}_v6_l1.json"]:
            f = p / cand
            if f.exists() and f.stat().st_size > 1000:
                r = json.load(open(f))
                rows = []
                for x in r:
                    lbl = x.get("label_gt")
                    if lbl is None:
                        lbl = x.get("label")
                    d = x.get("direct_score")
                    v = x.get("v9_score")
                    if x.get("error") is not None: continue
                    if lbl is None or d is None or v is None: continue
                    try:
                        rows.append((x.get("item_id"), int(lbl), float(d), float(v)))
                    except: pass
                out[D] = rows; break
    return out


def auroc(y, s):
    if len(set(y)) < 2: return None
    try: return float(roc_auc_score(y, s))
    except: return None


def best_alpha(rows, alphas):
    y = [r[1] for r in rows]
    best_a, best_au = 0.5, -1
    for a in alphas:
        s = [a * r[2] + (1-a) * r[3] for r in rows]
        au = auroc(y, s)
        if au is None: continue
        if au > best_au:
            best_au = au; best_a = a
    return best_a, best_au


def macro_with_alphas(test, alphas_per_dom):
    aurocs = []
    for D in DOMAINS:
        rows = test.get(D)
        if not rows: continue
        a = alphas_per_dom.get(D, 0.5)
        y = [r[1] for r in rows]
        s = [a * r[2] + (1-a) * r[3] for r in rows]
        au = auroc(y, s)
        if au is not None: aurocs.append(au)
    return float(np.mean(aurocs)) if aurocs else None


def boot_paired(test_a, test_b, alphas_a, alphas_b, n_boot=1000, seed=0):
    rng = np.random.default_rng(seed)
    common = [D for D in DOMAINS if test_a.get(D) and test_b.get(D)]
    pairs = {}
    for D in common:
        a_map = {r[0]: r for r in test_a[D]}
        b_map = {r[0]: r for r in test_b[D]}
        ids = sorted(a_map.keys() & b_map.keys())
        pairs[D] = [(i, a_map[i], b_map[i]) for i in ids]
    deltas = []
    for _ in range(n_boot):
        ma=[]; mb=[]
        for D in common:
            ps = pairs[D]; n=len(ps); idx=rng.integers(0,n,n)
            aa = alphas_a.get(D, 0.5); ab = alphas_b.get(D, 0.5)
            ya=[ps[i][1][1] for i in idx]; sa=[aa*ps[i][1][2] + (1-aa)*ps[i][1][3] for i in idx]
            yb=[ps[i][2][1] for i in idx]; sb=[ab*ps[i][2][2] + (1-ab)*ps[i][2][3] for i in idx]
            if len(set(ya))<2 or len(set(yb))<2: continue
            ma.append(roc_auc_score(ya, sa)); mb.append(roc_auc_score(yb, sb))
        if ma and mb: deltas.append(np.mean(mb)-np.mean(ma))
    d = np.array(deltas)
    return float(d.mean()*100), float(np.percentile(d, 2.5)*100), float(np.percentile(d, 97.5)*100), float((d>0).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n_boot", type=int, default=1000)
    ap.add_argument("--alpha_step", type=float, default=0.05)
    args = ap.parse_args()

    alphas = np.arange(0, 1+args.alpha_step, args.alpha_step)

    sources = {
        "Passive":  (ROOT/"verbalized/v12_passive_dev", ROOT/"v2/v12_passive_test"),
        "+Anchor":  (ROOT/"verbalized/v6_dev_anchor",   ROOT/"verbalized/v6_test_anchor"),
        "+L2":      (ROOT/"verbalized/v6_dev_l2",       ROOT/"verbalized/v6_test_l2"),
    }
    if (ROOT/"verbalized/v6_dev_l1").exists() and (ROOT/"verbalized/v6_test_l1").exists():
        sources["+L1"] = (ROOT/"verbalized/v6_dev_l1", ROOT/"verbalized/v6_test_l1")

    print(f"Searching alpha in [0, 1] step {args.alpha_step}\n")
    results = {}
    for name, (dev_p, test_p) in sources.items():
        dev = load_branched(dev_p)
        test = load_branched(test_p)
        print(f"=== {name} ===")
        # Per-domain alpha
        alpha_pd = {}
        alpha_dev_au = {}
        for D in DOMAINS:
            rows = dev.get(D)
            if not rows or len(rows) < 5:
                alpha_pd[D] = 0.5; alpha_dev_au[D] = None; continue
            a, au = best_alpha(rows, alphas)
            alpha_pd[D] = a; alpha_dev_au[D] = au
        # Global alpha
        all_dev_rows = []
        for D in DOMAINS:
            all_dev_rows.extend(dev.get(D) or [])
        # global α: average per-domain AUROC over alphas (not flat AUROC since domains heterogeneous)
        best_global_a, best_macro = 0.5, -1
        for a in alphas:
            macros = []
            for D in DOMAINS:
                rows = dev.get(D)
                if not rows: continue
                y=[r[1] for r in rows]; s=[a*r[2]+(1-a)*r[3] for r in rows]
                au = auroc(y, s)
                if au is not None: macros.append(au)
            if macros and np.mean(macros) > best_macro:
                best_macro = np.mean(macros); best_global_a = a

        # Test macros
        macro_05 = macro_with_alphas(test, {D: 0.5 for D in DOMAINS})
        macro_global = macro_with_alphas(test, {D: best_global_a for D in DOMAINS})
        macro_pd = macro_with_alphas(test, alpha_pd)

        results[name] = {
            "alpha_per_domain": alpha_pd,
            "alpha_global": float(best_global_a),
            "test_macro_alpha_0.5": macro_05,
            "test_macro_alpha_global": macro_global,
            "test_macro_alpha_per_domain": macro_pd,
            "test": test,
        }
        print(f"  α=0.5:        macro={macro_05:.4f}")
        print(f"  α_global={best_global_a:.2f}: macro={macro_global:.4f}")
        print(f"  α per-domain: macro={macro_pd:.4f}")
        print(f"  per-domain α picks: {alpha_pd}")
        print()

    # Bootstrap CIs vs Passive(α=0.5) baseline
    print("\n=== Paired bootstrap CIs vs Passive(α=0.5) ===")
    base = results["Passive"]["test"]
    base_alphas = {D: 0.5 for D in DOMAINS}
    for name in results:
        r = results[name]
        for tag, alphas_b in [(f"α=0.5", {D: 0.5 for D in DOMAINS}),
                              (f"α_global={r['alpha_global']:.2f}", {D: r['alpha_global'] for D in DOMAINS}),
                              ("α per-domain", r["alpha_per_domain"])]:
            if name == "Passive" and tag == "α=0.5":
                print(f"  {name} | {tag:<25} | macro={r['test_macro_alpha_0.5']:.4f}  (baseline)")
                continue
            mu, lo, hi, p = boot_paired(base, r["test"], base_alphas, alphas_b, n_boot=args.n_boot)
            macro_v = (r["test_macro_alpha_0.5"] if "0.5" in tag else
                       r["test_macro_alpha_global"] if "global" in tag else
                       r["test_macro_alpha_per_domain"])
            print(f"  {name} | {tag:<25} | macro={macro_v:.4f} | Δ={mu:+.2f}pp [{lo:+.2f}, {hi:+.2f}] | P={p:.3f}")


if __name__ == "__main__":
    main()
