"""Summarise a v12 result run: tool usage, AUROC per domain, and AUROC delta
vs a baseline (v11 passive_blend score or v10 file)."""
from __future__ import annotations
import argparse, collections, glob, json, os, sys, ast
from pathlib import Path
import numpy as np
from sklearn.metrics import roc_auc_score


def _parse_tools(t):
    if isinstance(t, list): return t
    if isinstance(t, str):
        try: return ast.literal_eval(t)
        except Exception: return [t] if t else []
    return []


def load_results(path: str) -> list:
    p = Path(path)
    if p.is_dir():
        out = []
        for f in sorted(p.glob('D*.json'), key=lambda x: int(x.stem[1:])):
            out.extend(json.load(open(f)))
        return out
    return json.load(open(path))


def tool_usage(rows):
    ad_ok = [x for x in rows if x.get('mode')=='anomaly_detection'
             and x.get('v9_score') is not None and not x.get('error')]
    per_tool = collections.Counter()
    total_invs = 0
    items_any = 0
    per_domain_per_tool = collections.defaultdict(collections.Counter)
    for x in ad_ok:
        tools = _parse_tools(x.get('tools_used'))
        if tools: items_any += 1
        for t in tools:
            per_tool[t] += 1
            total_invs += 1
            per_domain_per_tool[x['domain_code']][t] += 1
    return {'ad_ok': len(ad_ok),
            'items_any': items_any,
            'total_invs': total_invs,
            'per_tool': dict(per_tool),
            'per_domain_per_tool': {k: dict(v) for k,v in per_domain_per_tool.items()}}


def auroc_summary(rows):
    ok = [x for x in rows if x.get('mode')=='anomaly_detection'
          and x.get('anomaly_score') is not None and not x.get('error')
          and x.get('label_gt') is not None]
    y = np.array([x['label_gt'] for x in ok])
    s = np.array([x['anomaly_score'] for x in ok])
    v9 = np.array([x.get('v9_score') if x.get('v9_score') is not None else 0.5 for x in ok])
    d = np.array([x.get('direct_score') if x.get('direct_score') is not None else 0.5 for x in ok])
    blend = 0.5*d + 0.5*v9
    overall = {'n': len(ok),
               'AUROC': float(roc_auc_score(y,s)),
               'direct_AUROC': float(roc_auc_score(y,d)),
               'v9_AUROC': float(roc_auc_score(y,v9)),
               'blend_AUROC': float(roc_auc_score(y,blend))}
    per_dom = {}
    by_dom = collections.defaultdict(list)
    for x in ok:
        by_dom[x['domain_code']].append(x)
    for dc, items in by_dom.items():
        yy = np.array([i['label_gt'] for i in items])
        ss = np.array([i['anomaly_score'] for i in items])
        if len(set(yy)) < 2: continue
        per_dom[dc] = {'n': len(items), 'AUROC': float(roc_auc_score(yy,ss))}
    return {'overall': overall, 'per_domain': per_dom}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', required=True,
                    help='file or directory of result JSONs')
    ap.add_argument('--baseline', default='',
                    help='optional baseline file/dir for AUROC delta')
    args = ap.parse_args()

    rows = load_results(args.results)
    print(f'Loaded {len(rows)} rows from {args.results}')
    usage = tool_usage(rows)
    auroc = auroc_summary(rows)

    print()
    print('=== tool usage ===')
    total = max(1, usage['total_invs'])
    print(f'  ad_ok={usage["ad_ok"]}  items_using_any_tool={usage["items_any"]}  '
          f'total_invocations={usage["total_invs"]}')
    for t, c in sorted(usage['per_tool'].items(), key=lambda kv:-kv[1]):
        print(f'    {t:32s}  {c:5d}  ({c/total*100:5.1f}% invs, {c/usage["ad_ok"]*100:5.1f}% items)')

    print()
    print('=== AUROC ===')
    for k, v in auroc['overall'].items():
        if k == 'n': continue
        print(f'  {k}: {v:.4f}  (n={auroc["overall"]["n"]})')
    print()
    print('  per-domain:')
    for dc, d in sorted(auroc['per_domain'].items(), key=lambda kv: int(kv[0][1:])):
        print(f'    {dc:5s}  n={d["n"]:4d}  AUROC={d["AUROC"]:.3f}')

    if args.baseline:
        base_rows = load_results(args.baseline)
        base_au = auroc_summary(base_rows)
        print()
        print('=== AUROC delta vs baseline ===')
        print(f'  overall: {auroc["overall"]["AUROC"]:.4f} vs {base_au["overall"]["AUROC"]:.4f}   '
              f'Δ={auroc["overall"]["AUROC"]-base_au["overall"]["AUROC"]:+.4f}')
        for dc in sorted(set(auroc['per_domain']) & set(base_au['per_domain']),
                         key=lambda k: int(k[1:])):
            a = auroc['per_domain'][dc]['AUROC']
            b = base_au['per_domain'][dc]['AUROC']
            print(f'    {dc:5s}  {a:.3f} vs {b:.3f}   Δ={a-b:+.3f}')


if __name__ == '__main__':
    main()
