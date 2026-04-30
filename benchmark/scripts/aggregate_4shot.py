"""Compare AD-Copilot 1-shot vs 4-shot per-domain AUROC."""
import json
from pathlib import Path
import numpy as np
from sklearn.metrics import roc_auc_score

DOMAINS = ["D1","D2","D3","D4","D5","D6","D7","D8","D9","D10","D11","D12"]


def per_dom(d):
    out = {}
    for D in DOMAINS:
        f = Path(d) / f"{D}.json"
        if not f.exists():
            out[D] = None
            continue
        r = json.load(open(f))
        ok = [x for x in r if x.get("error") is None and x.get("anomaly_score") is not None]
        if len(ok) < 5:
            out[D] = None; continue
        y = [x["label"] for x in ok]; s = [x["anomaly_score"] for x in ok]
        if len(set(y)) < 2:
            out[D] = None; continue
        out[D] = round(float(roc_auc_score(y, s)), 4)
    return out


root = Path("/hdd1/jiangxi/AD-Agent/benchmark/results/baselines")
one = per_dom(root / "ad_copilot")
four = per_dom(root / "ad_copilot_4shot")

print(f"{'D':6} {'1-shot':>8} {'4-shot':>8} {'Δ':>7}")
deltas = []
for D in DOMAINS:
    a = one.get(D); b = four.get(D)
    if a is None or b is None:
        print(f"{D:6} {'N/A':>8} {'N/A':>8}")
        continue
    d = b - a
    deltas.append(d)
    print(f"{D:6} {a:>8.4f} {b:>8.4f} {d:>+7.4f}")

# macros
o_vals = [v for v in one.values() if v is not None]
f_vals = [v for v in four.values() if v is not None]
print()
print(f"Macro 1-shot: {np.mean(o_vals):.4f}")
print(f"Macro 4-shot: {np.mean(f_vals):.4f}")
print(f"Macro delta : {np.mean(f_vals)-np.mean(o_vals):+.4f}")

# LaTeX row
cells = [f"{four[D]:.3f}" if four[D] is not None else "\\tbd" for D in DOMAINS]
macro4 = round(float(np.mean(f_vals)), 3)
print()
print(f"\\hspace{{1mm}}AD-Copilot (4-shot)~\\citep{{jiang2026adcopilot}}    & "
      + " & ".join(cells) + f" & {macro4:.3f} \\\\")
