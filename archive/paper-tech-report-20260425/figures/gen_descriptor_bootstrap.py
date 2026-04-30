"""Stratified paired bootstrap for the 3-backbone descriptor ablation.

For each backbone, computes macro AUROC of:
  - v0_task (existing _v2 test files, task-anchored descriptor)
  - v0_generic (new runs with DESCRIPTOR_MODE=generic)

and the paired delta with 95% CI.

Output: paper/figures/descriptor_cis.json and a per-domain table.
"""
import json
import numpy as np
from collections import defaultdict
from pathlib import Path
from sklearn.metrics import roc_auc_score

RESULTS = Path("/hdd1/jiangxi/AD-Agent/benchmark/results")
OUT = Path("/hdd1/jiangxi/AD-Agent/paper/figures/descriptor_cis.json")
N_BOOT = 1000
SEED = 20260414

# domain_code -> paper D-label
DOMAIN_MAP = {
    "D1":  "D01", "D2":  "D02", "D4":  "D03", "D5":  "D04",
    "D5b": "D05", "D5c": "D06", "D5d": "D07", "D6":  "D08",
    "D7":  "D09", "D9":  "D10", "D10": "D11",
}
INCLUDE_CODES = set(DOMAIN_MAP.keys())  # exclude D8 surveillance

BACKBONES = {
    # (task_file, generic_file, name)
    "GPT-5.4":  ("gpt54_v0_direct_test_all_v2.json",
                 "gpt54_v0_direct_test_all.json"),          # pre-existing legacy generic
    "SeedVL":   ("seedvl_v0_direct_test_all_v2.json",
                 "seedvl_v0_direct_generic_test.json"),     # new
    "Qwen3.5":  ("qwen35_v0_direct_test_all_v2.json",
                 "qwen35_v0_direct_generic_test.json"),     # new
}


def load_score_map(fname):
    """Return {item_id: (score, label_gt, domain_code)}.

    Skips items whose domain_code is not in the paper's 11-domain set.
    """
    path = RESULTS / fname
    data = json.load(open(path))
    out = {}
    for x in data:
        if x.get("split") and x["split"] != "test":
            continue
        dc = x.get("domain_code")
        if dc not in INCLUDE_CODES:
            continue
        s = x.get("anomaly_score")
        if not isinstance(s, (int, float)):
            continue
        out[x["item_id"]] = (float(s), int(x["label_gt"]), dc)
    return out


def paired_bootstrap(scores_a, scores_b, labels, domains,
                     n_boot=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    labels = np.asarray(labels)
    domains = np.asarray(domains)
    sa = np.asarray(scores_a)
    sb = np.asarray(scores_b)
    dom_indices = {d: np.where(domains == d)[0] for d in set(domains)}

    def macro(sa_, sb_, idx):
        lbls = labels[idx]
        doms = domains[idx]
        aa, bb = [], []
        for d in set(doms):
            di = np.where(doms == d)[0]
            y = lbls[di]
            if len(set(y)) < 2:
                continue
            aa.append(roc_auc_score(y, sa_[idx][di]))
            bb.append(roc_auc_score(y, sb_[idx][di]))
        return float(np.mean(aa)), float(np.mean(bb))

    full_idx = np.arange(len(labels))
    auc_a_pt, auc_b_pt = macro(sa, sb, full_idx)
    delta_pt = auc_a_pt - auc_b_pt

    deltas = []
    for _ in range(n_boot):
        boot = np.concatenate([rng.choice(idx, len(idx), replace=True)
                               for idx in dom_indices.values()])
        aa, bb = macro(sa, sb, boot)
        deltas.append(aa - bb)
    deltas = np.array(deltas)
    lo, hi = np.percentile(deltas, [2.5, 97.5])
    p_pos = float(np.mean(deltas <= 0))
    return {
        "auc_task": auc_a_pt,
        "auc_generic": auc_b_pt,
        "delta": float(delta_pt),
        "ci_lo": float(lo),
        "ci_hi": float(hi),
        "p_delta_positive": p_pos,
        "sig_95": bool(lo > 0 or hi < 0),
    }


def per_domain_table(task_map, gen_map):
    """Per-domain generic vs task AUROC (items shared between both)."""
    rows = []
    for dc, d_label in sorted(DOMAIN_MAP.items(), key=lambda x: x[1]):
        items = [i for i in task_map if i in gen_map and task_map[i][2] == dc]
        if not items:
            continue
        y = [task_map[i][1] for i in items]
        if len(set(y)) < 2:
            continue
        t = [task_map[i][0] for i in items]
        g = [gen_map[i][0] for i in items]
        at = roc_auc_score(y, t)
        ag = roc_auc_score(y, g)
        rows.append((d_label, ag, at, at - ag, len(items)))
    return rows


def main():
    report = {}
    for bb, (task_f, gen_f) in BACKBONES.items():
        print(f"\n=== {bb} ===")
        if not (RESULTS / task_f).exists():
            print(f"  SKIP: missing {task_f}")
            continue
        if not (RESULTS / gen_f).exists():
            print(f"  SKIP: missing {gen_f}  (run still pending?)")
            continue
        task = load_score_map(task_f)
        gen = load_score_map(gen_f)
        common = sorted(set(task.keys()) & set(gen.keys()))
        print(f"  common items: {len(common)} (task: {len(task)}, generic: {len(gen)})")
        if len(common) < 100:
            print("  WARN: too few common items, skipping bootstrap")
            continue

        sa = [task[i][0] for i in common]
        sb = [gen[i][0] for i in common]
        labels = [task[i][1] for i in common]
        domains = [task[i][2] for i in common]

        res = paired_bootstrap(sa, sb, labels, domains)
        rows = per_domain_table(task, gen)
        report[bb] = {
            "task_file": task_f,
            "generic_file": gen_f,
            "n_items": len(common),
            "bootstrap": res,
            "per_domain": [
                {"domain": d, "generic": g, "task": t, "delta": dt, "n": n}
                for d, g, t, dt, n in rows
            ],
        }
        print(f"  auc_task={res['auc_task']:.4f}  auc_generic={res['auc_generic']:.4f}  "
              f"Δ={res['delta']:+.4f} CI=[{res['ci_lo']:+.4f},{res['ci_hi']:+.4f}]  "
              f"sig95={res['sig_95']}")

    OUT.write_text(json.dumps(report, indent=2))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
