"""Option 2: per-item routing by Direct confidence.

For each item, a "gate" decides whether to use Passive or rule-injected.
Gate logic: if Direct branch is decisive (|s_D - 0.5| > tau) → use Passive
(no rule injection); else → use rule-injected variant. Tau is tuned on dev.

Test variants: each combination of (rule mode, gate)
  - Passive (no gate, baseline)
  - +Anchor full (always inject) — already known
  - +Anchor gated (inject only when Direct uncertain)
  - +L2 full / gated
"""
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

DOMAINS = ["D1","D2","D3","D4","D5","D6","D7","D8","D9","D10","D11","D12"]
ROOT = Path("/hdd1/jiangxi/AD-Agent/benchmark/results")


def load(p):
    out = {}
    for D in DOMAINS:
        for cand in [f"{D}.json", f"{D}_v6_anchor.json", f"{D}_v6_l2.json", f"{D}_v6_l1.json"]:
            f = p / cand
            if f.exists() and f.stat().st_size > 1000:
                r = json.load(open(f))
                rows = []
                for x in r:
                    lbl = x.get("label_gt")
                    if lbl is None: lbl = x.get("label")
                    sc = x.get("anomaly_score")
                    d  = x.get("direct_score")
                    if x.get("error") is not None: continue
                    if lbl is None or sc is None: continue
                    try:
                        rows.append((x.get("item_id"), int(lbl), float(sc), float(d) if d is not None else None))
                    except: pass
                out[D] = rows; break
    return out


def gated_score(passive_row, variant_row, tau):
    """Item-level gating: if Direct is decisive, use passive_row's score;
    else use variant_row's score."""
    _, _, _, d_p = passive_row
    if d_p is None:
        return variant_row[2]
    if abs(d_p - 0.5) > tau:
        return passive_row[2]
    return variant_row[2]


def macro_for(passive, variant, tau):
    aurocs = []
    for D in DOMAINS:
        p_rows = passive.get(D)
        v_rows = variant.get(D)
        if not p_rows or not v_rows: continue
        p_map = {r[0]: r for r in p_rows}
        v_map = {r[0]: r for r in v_rows}
        ids = sorted(p_map.keys() & v_map.keys())
        y = []
        s = []
        for i in ids:
            y.append(p_map[i][1])
            s.append(gated_score(p_map[i], v_map[i], tau))
        if len(set(y)) >= 2:
            aurocs.append(roc_auc_score(y, s))
    return float(np.mean(aurocs)) if aurocs else None


def boot(passive_test, variant_test, tau, n_boot=1000, seed=0):
    rng = np.random.default_rng(seed)
    common = [D for D in DOMAINS if passive_test.get(D) and variant_test.get(D)]
    pairs = {}
    for D in common:
        p_map = {r[0]: r for r in passive_test[D]}
        v_map = {r[0]: r for r in variant_test[D]}
        ids = sorted(p_map.keys() & v_map.keys())
        pairs[D] = [(p_map[i], v_map[i]) for i in ids]
    deltas = []
    for _ in range(n_boot):
        ma=[]; mb=[]
        for D in common:
            ps = pairs[D]; n=len(ps); idx=rng.integers(0,n,n)
            ya=[ps[i][0][1] for i in idx]; sa=[ps[i][0][2] for i in idx]  # passive
            yb=[ps[i][0][1] for i in idx]; sb=[gated_score(ps[i][0], ps[i][1], tau) for i in idx]
            if len(set(ya))<2 or len(set(yb))<2: continue
            ma.append(roc_auc_score(ya,sa)); mb.append(roc_auc_score(yb,sb))
        if ma and mb: deltas.append(np.mean(mb)-np.mean(ma))
    d=np.array(deltas)
    return float(d.mean()*100), float(np.percentile(d,2.5)*100), float(np.percentile(d,97.5)*100), float((d>0).mean())


def main():
    passive_dev  = load(ROOT/"verbalized/v12_passive_dev")
    passive_test = load(ROOT/"v2/v12_passive_test")

    variants = {
        "+Anchor": (load(ROOT/"verbalized/v6_dev_anchor"),
                    load(ROOT/"verbalized/v6_test_anchor")),
        "+L2":     (load(ROOT/"verbalized/v6_dev_l2"),
                    load(ROOT/"verbalized/v6_test_l2")),
    }
    if (ROOT/"verbalized/v6_dev_l1").exists():
        variants["+L1"] = (load(ROOT/"verbalized/v6_dev_l1"),
                           load(ROOT/"verbalized/v6_test_l1"))

    taus = np.arange(0.0, 0.51, 0.05)

    print(f"\n=== Searching tau on dev (Direct confidence threshold) ===\n")
    for name, (dev_v, test_v) in variants.items():
        # Find best tau on dev
        best_tau, best_au = 0.0, -1
        for tau in taus:
            macro = macro_for(passive_dev, dev_v, tau)
            if macro is not None and macro > best_au:
                best_au = macro; best_tau = tau

        # Also report tau=0 (full inject) and tau=0.5 (never inject = passive)
        full_inject_test  = macro_for(passive_test, test_v, 0.0)
        gated_test        = macro_for(passive_test, test_v, best_tau)
        passive_test_macro = macro_for(passive_test, passive_test, 0.0)

        print(f"  {name}:")
        print(f"    tau=0.0 (full inject):    test macro = {full_inject_test:.4f}")
        print(f"    tau={best_tau:.2f} (best on dev): dev_macro = {best_au:.4f}, test macro = {gated_test:.4f}")
        # Bootstrap CI for tau* on test
        mu, lo, hi, p = boot(passive_test, test_v, best_tau)
        print(f"    Δ vs Passive: {mu:+.2f}pp [{lo:+.2f}, {hi:+.2f}]  P(Δ>0)={p:.3f}")

    print(f"\nPassive baseline macro = {macro_for(passive_test, passive_test, 0.0):.4f}")


if __name__ == "__main__":
    main()
