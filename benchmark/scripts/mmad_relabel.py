"""Post-process mmad_eval_v9 JSON output to correct label_gt.

Original bug: `'good' in key.lower()` flipped all GoodsAD items to label=0
because "good" is a substring of "GoodsAD". This rewrites label_gt using
the new path-parent + options[Answer] logic.

Usage:
  python benchmark/scripts/mmad_relabel.py input.json [--inplace]
"""
from __future__ import annotations
import argparse
import json
import sys


def path_label(key: str) -> int:
    parts = key.split("/")
    if len(parts) < 2:
        return 1
    parent = parts[-2].lower()
    return 0 if parent in {"good", "normal", "ok"} else 1


def ad_label_from_options(ans, opts) -> int | None:
    if not opts or ans not in opts:
        return None
    txt = str(opts[ans]).lower()
    if any(k in txt for k in ("yes", "defect", "there is", "anomal")):
        return 1
    if any(k in txt for k in ("no", "normal")):
        return 0
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--inplace", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    data = json.load(open(args.input))
    flipped = 0
    preserved = 0
    for r in data:
        key = r.get("image") or r.get("item_id", "")
        # "image" in v9 output = raw_key (relative). Strip any '#qN' suffix.
        if "#" in key:
            key = key.split("#", 1)[0]
        path_lab = path_label(key)
        if r.get("question_type") == "Anomaly Detection":
            ad_lab = ad_label_from_options(r.get("correct_answer"),
                                           r.get("options") or {})
            new_lab = ad_lab if ad_lab is not None else path_lab
        else:
            new_lab = path_lab
        old_lab = r.get("label_gt")
        if old_lab is not None and old_lab != new_lab:
            flipped += 1
            r["label_gt_original"] = old_lab
        else:
            preserved += 1
        r["label_gt"] = new_lab

    out_path = args.input if args.inplace else (args.out or
                                                args.input.replace(".json",
                                                                   "_relabeled.json"))
    with open(out_path, "w") as f:
        json.dump(data, f)
    print(f"Input:    {args.input} ({len(data)} items)")
    print(f"Output:   {out_path}")
    print(f"Flipped:  {flipped} items")
    print(f"Preserved:{preserved} items")


if __name__ == "__main__":
    main()
