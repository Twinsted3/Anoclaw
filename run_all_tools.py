#!/usr/bin/env python3
"""
Run every tool in the AnomalyClaw v8 13-tool catalog on one manifest item,
WITHOUT any LLM calls, and produce a tool-use evaluation report.

Usage:
    python run_all_tools.py --item_id D1_0029
    python run_all_tools.py --item_id D1_0029 --outdir output/D1_0029_tools

Outputs (under --outdir):
    images/                 one PNG per image the tools emitted
    tool_run_report.json    machine-readable record: args / status / latency /
                            output summary / error reason for every call
    tool_run_report.html    visual dashboard: success rate, latency chart,
                            per-tool cards with images and failure reasons

Two tools (tool_reference_profiler, tool_domain_knowledge) are LLM-backed by
design; they are still invoked so the report records their dependency error
("vlm_client / llm_client required") instead of silently skipping them.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from base64 import b64decode
from io import BytesIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = REPO_ROOT / "benchmark" / "scripts"
os.environ["ANOMALYCLAW_DATA"] = str(REPO_ROOT / "benchmark" / "data")
sys.path.insert(0, str(SCRIPTS_DIR))

# import agent_tools_v8 as _t8
# from infer import resolve_data_path
from PIL import Image

### only for checking ###
from benchmark.scripts.infer import resolve_data_path
from benchmark.scripts import agent_tools_v8 as _t8

_TOOL_IMG_KEYS = (
    "crop_b64", "diff_mask_b64", "aligned_diff_b64", "composite_b64",
    "heatmap_b64", "blob_layout_b64", "change_heatmap_b64", "spectrum_b64",
)

# tool family grouping (for the report)
_TOOL_FAMILY = {
    "tool_expert_score":        "expert probe",
    "tool_hotspot_cropper":     "visual inspection",
    "tool_zoom_bbox":           "visual inspection",
    "tool_patch_grid":          "visual inspection",
    "tool_image_diff":          "reference understanding",
    "tool_rotate_align":        "reference understanding",
    "tool_side_by_side":        "visual inspection",
    "tool_reference_profiler":  "reference understanding (LLM)",
    "tool_reference_retriever": "reference understanding",
    "tool_component_counter":   "structure / texture",
    "tool_segment_and_count":   "structure / texture",
    "tool_texture_fft":         "structure / texture",
    "tool_domain_knowledge":    "semantic knowledge (LLM)",
}


def _patch_retriever_local_weights() -> bool:
    """If a local DINOv2 checkpoint exists (weights/dinov2/model.safetensors),
    swap in a loader that builds the retrieval model from it — avoids the
    HuggingFace download entirely (benchmark code itself is untouched)."""
    wpath = os.environ.get(
        "ANOMALYCLAW_DINOV2_WEIGHTS",
        str(REPO_ROOT / "weights" / "dinov2" / "model.safetensors"))
    if not os.path.exists(wpath):
        return False

    def _load_local(device: str = "cuda"):
        if "model" in _t8._RETRIEVAL_CACHE:
            return _t8._RETRIEVAL_CACHE["model"], _t8._RETRIEVAL_CACHE["transform"]
        import torch
        import timm
        model = timm.create_model("vit_small_patch14_dinov2.lvd142m",
                                  pretrained=False, num_classes=0)
        from safetensors.torch import load_file
        model.load_state_dict(load_file(wpath), strict=False)
        model = model.to(device).eval()
        try:
            cfg = timm.data.resolve_data_config(model.pretrained_cfg)
        except Exception:
            cfg = {"input_size": (3, 518, 518),
                   "mean": (0.485, 0.456, 0.406),
                   "std": (0.229, 0.224, 0.225),
                   "interpolation": "bicubic", "crop_pct": 1.0}
        transform = timm.data.create_transform(**cfg, is_training=False)
        _t8._RETRIEVAL_CACHE["model"] = model
        _t8._RETRIEVAL_CACHE["transform"] = transform
        return model, transform

    _t8._load_retrieval_model_v6 = _load_local
    return True


def _load_item(manifest_path: str, item_id: str) -> dict:
    items = json.load(open(manifest_path, encoding="utf-8"))
    for it in items:
        if it.get("item_id") == item_id:
            return it
    raise ValueError(f"{item_id!r} not found in {manifest_path}")


def _save_b64(b64: str, path: Path) -> None:
    Image.open(BytesIO(b64decode(b64))).save(path, format="PNG")


def _summarize_observation(obs: dict) -> dict:
    """Keep only JSON-safe scalar / short-structure fields (no b64 images)."""
    out = {}
    for k, v in obs.items():
        if k.endswith("_b64") or k == "tiles":
            continue
        if isinstance(v, str) and len(v) > 400:
            v = v[:400] + "…"
        if isinstance(v, list) and len(json.dumps(v, default=str)) > 800:
            v = f"<list, {len(v)} items>"
        if isinstance(v, dict) and len(json.dumps(v, default=str)) > 800:
            v = f"<dict, {len(v)} keys: {sorted(v)[:8]}>"
        out[k] = v
    return out


def _default_args(name: str, img_size: tuple[int, int]) -> dict:
    """Sensible default args per tool (same spirit as what the agent would send)."""
    W, H = img_size
    if name == "tool_zoom_bbox":
        # centre crop in ORIGINAL pixel coords (this tool's documented convention)
        return {"bbox": [W // 4, H // 4, 3 * W // 4, 3 * H // 4]}
    if name == "tool_side_by_side":
        # full image in 256x256 normalised coords (this tool's convention)
        return {"bbox": [0, 0, 256, 256]}
    if name == "tool_patch_grid":
        return {"rows": 3, "cols": 3}
    if name in ("tool_image_diff", "tool_rotate_align"):
        return {"ref_idx": 0}
    if name == "tool_reference_retriever":
        device = "cuda"
        try:
            import torch
            if not torch.cuda.is_available():
                device = "cpu"
        except Exception:
            device = "cpu"
        return {"k": 4, "device": device}
    if name == "tool_domain_knowledge":
        return {"question": "In MVTec-AD metal_nut inspection, is a slightly "
                            "different lobe curvature typically a benign "
                            "manufacturing variation or a defect indicator?"}
    return {}


def run_all(item: dict, outdir: Path) -> dict:
    img_dir = outdir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    ctx = {
        "query_path": item["query_path"],
        "ref_paths": item.get("ref_paths") or [],
        "item_id": item.get("item_id"),
        "split": item.get("split", "test"),
        "_manifest_domain": item.get("domain_code"),
        # vlm_client / vlm_model / llm_client / llm_model intentionally absent:
        # the two LLM-backed tools must report their dependency error.
    }
    with Image.open(item["query_path"]) as im:
        img_size = im.size  # (W, H)

    records = []

    def _invoke(name: str, args: dict, note: str = "") -> dict:
        print(f"  ▶ {name}  args={json.dumps(args, ensure_ascii=False)}")
        t0 = time.perf_counter()
        try:
            obs = _t8.dispatch_tool(name, dict(args), ctx)
        except Exception as exc:  # dispatch_tool already guards, but be safe
            obs = {"error": f"dispatcher raised {type(exc).__name__}: {exc}"}
        dt_ms = (time.perf_counter() - t0) * 1000.0

        err = obs.get("error")
        unavailable = (err is None) and (
            obs.get("available") is False or obs.get("not_applicable") is True)
        status = "failed" if err else ("not_applicable" if unavailable else "success")

        # dump every image the tool produced
        saved = []
        tag = f"{len(records):02d}_{name}"
        try:
            for key in _TOOL_IMG_KEYS:
                if b64 := obs.get(key):
                    p = img_dir / f"{tag}_{key[:-4]}.png"
                    _save_b64(b64, p)
                    saved.append(p.name)
            for i, tile in enumerate(obs.get("tiles", [])[:9]):
                if b64 := tile.get("crop_b64"):
                    p = img_dir / f"{tag}_tile{i}.png"
                    _save_b64(b64, p)
                    saved.append(p.name)
            for i, b64 in enumerate(obs.get("retrieved_images_b64", [])[:4]):
                p = img_dir / f"{tag}_ref{i}.png"
                _save_b64(b64, p)
                saved.append(p.name)
            # retrieval index was built on a Linux server: its stored paths
            # (/hdd1/...) don't exist locally. Remap the "MMAD/..." tail onto
            # the local data root so the retrieved refs can still be shown.
            if name == "tool_reference_retriever" and not obs.get("error"):
                data_root = Path(os.environ["ANOMALYCLAW_DATA"])
                remapped = []
                for i, r in enumerate(obs.get("results", [])[:4]):
                    p_str = r.get("path", "")
                    local = p_str if os.path.exists(p_str) else None
                    if local is None and "MMAD/" in p_str.replace("\\", "/"):
                        tail = p_str.replace("\\", "/").rsplit("MMAD/", 1)[1]
                        cand = data_root / "MMAD" / tail
                        local = str(cand) if cand.exists() else None
                    if local:
                        dst = img_dir / f"{tag}_ref{i}.png"
                        Image.open(local).convert("RGB").save(dst, format="PNG")
                        saved.append(dst.name)
                        remapped.append(local)
                if remapped:
                    note = ("索引内为 Linux 服务器绝对路径，已映射到本地 "
                            f"MMAD 数据根目录显示（{len(remapped)} 张）")
                    print(f"     [note] {note}")
        except Exception as exc:
            print(f"     [warn] image dump failed: {exc}")

        rec = {
            "tool": name,
            "family": _TOOL_FAMILY.get(name, "?"),
            "note": note,
            "args": args,
            "status": status,
            "duration_ms": round(dt_ms, 1),
            "error": err,
            "decline_reason": (obs.get("reason") or
                               (obs.get("interpretation") or "").split("\n")[0]
                               if unavailable else None),
            "observation": _summarize_observation(obs),
            "images": saved,
        }
        records.append(rec)
        flag = {"success": "OK ", "not_applicable": "N/A", "failed": "FAIL"}[status]
        print(f"     [{flag}] {dt_ms:8.1f} ms   images={len(saved)}"
              + (f"   error={err}" if err else ""))
        return obs

    # ── phase 0: expert probe first — its top_patches feed two other tools ──
    obs = _invoke("tool_expert_score", {}, note="先跑：top_patches 供 hotspot_cropper / component_counter 使用")
    patches = obs.get("top_patches") or []
    if patches:
        ctx["_expert_patches"] = patches
        print(f"     → seeded ctx['_expert_patches'] with {len(patches)} patches")

    # ── phase 1: the remaining 12 tools in registry order ───────────────────
    for name in _t8.TOOL_REGISTRY:
        if name == "tool_expert_score":
            continue
        _invoke(name, _default_args(name, img_size))

    n_ok = sum(1 for r in records if r["status"] == "success")
    n_na = sum(1 for r in records if r["status"] == "not_applicable")
    n_fail = sum(1 for r in records if r["status"] == "failed")
    report = {
        "item_id": item.get("item_id"),
        "category": item.get("category"),
        "domain_code": item.get("domain_code"),
        "label": item.get("label"),
        "query_path": item["query_path"],
        "n_refs": len(ctx["ref_paths"]),
        "image_size": list(img_size),
        "llm_used": False,
        "n_tools": len(records),
        "n_success": n_ok,
        "n_not_applicable": n_na,
        "n_failed": n_fail,
        "success_rate": round(n_ok / max(1, len(records)), 3),
        "total_duration_ms": round(sum(r["duration_ms"] for r in records), 1),
        "records": records,
    }
    with open(outdir / "tool_run_report.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False, default=str)
    return report


# ── HTML dashboard ────────────────────────────────────────────────────────────

def _esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def render_html(report: dict, outdir: Path) -> Path:
    recs = report["records"]
    n = report["n_tools"]
    ok, na, fail = report["n_success"], report["n_not_applicable"], report["n_failed"]
    rate = report["success_rate"] * 100
    tmax = max((r["duration_ms"] for r in recs), default=1) or 1

    status_meta = {
        "success":        ("#16a34a", "#f0fdf4", "成功"),
        "not_applicable": ("#d97706", "#fffbeb", "不适用"),
        "failed":         ("#dc2626", "#fef2f2", "失败"),
    }

    # duration bar rows (sorted desc)
    bars = ""
    for r in sorted(recs, key=lambda x: -x["duration_ms"]):
        color, _, label = status_meta[r["status"]]
        w = max(1.5, r["duration_ms"] / tmax * 100)
        d = (f"{r['duration_ms']:.0f} ms" if r["duration_ms"] < 1000
             else f"{r['duration_ms']/1000:.2f} s")
        bars += (f'<div class="brow"><span class="bname">{_esc(r["tool"])}</span>'
                 f'<span class="btrack"><span class="bbar" style="width:{w:.1f}%;'
                 f'background:{color}"></span></span>'
                 f'<span class="bval">{d}</span></div>')

    # summary table rows
    rows = ""
    for r in recs:
        color, bg, label = status_meta[r["status"]]
        obs = r["observation"]
        keys = [k for k in obs if k not in ("error", "interpretation")]
        kv = " · ".join(f"{k}={_esc(obs[k])}" for k in keys[:6])
        if len(kv) > 260:
            kv = kv[:260] + "…"
        reason = ""
        if r["status"] == "failed":
            reason = f'<div class="reason">⚠ {_esc(r["error"])}</div>'
        elif r["status"] == "not_applicable":
            reason = f'<div class="reason na">○ {_esc(r.get("decline_reason") or "")}</div>'
        rows += (f"<tr><td class='mono'>{_esc(r['tool'])}</td>"
                 f"<td>{_esc(r['family'])}</td>"
                 f"<td class='mono small'>{_esc(json.dumps(r['args'], ensure_ascii=False))}</td>"
                 f"<td><span class='pill' style='color:{color};background:{bg};"
                 f"border-color:{color}'>{label}</span>{reason}</td>"
                 f"<td class='num'>{r['duration_ms']:.0f}</td>"
                 f"<td class='small'>{kv or '—'}</td>"
                 f"<td class='num'>{len(r['images'])}</td></tr>")

    # per-tool cards with images
    cards = ""
    for r in recs:
        color, bg, label = status_meta[r["status"]]
        imgs = "".join(
            f'<figure><img src="images/{_esc(p)}" loading="lazy">'
            f'<figcaption>{_esc(p)}</figcaption></figure>'
            for p in r["images"])
        interp = _esc((r["observation"].get("interpretation") or "")[:500])
        err_html = (f'<div class="reason">⚠ 失败原因：{_esc(r["error"])}</div>'
                    if r["status"] == "failed" else "")
        cards += (f"<div class='card'><div class='chead'>"
                  f"<span class='mono'>{_esc(r['tool'])}</span>"
                  f"<span class='pill' style='color:{color};background:{bg};"
                  f"border-color:{color}'>{label}</span>"
                  f"<span class='muted'>{r['duration_ms']:.0f} ms · "
                  f"{_esc(r['family'])}</span></div>"
                  f"<div class='muted small'>args: {_esc(json.dumps(r['args'], ensure_ascii=False))}</div>"
                  f"{err_html}"
                  f"{f'<div class=interp>{interp}</div>' if interp else ''}"
                  f"<div class='imgs'>{imgs}</div></div>")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>Tool-Use 评估报告 — {_esc(report['item_id'])}</title>
<style>
 body{{font-family:"Segoe UI","Microsoft YaHei",sans-serif;background:#f8fafc;
      color:#1e293b;margin:0;padding:28px}}
 h1{{font-size:22px;margin:0 0 4px}} h2{{font-size:16px;margin:26px 0 10px;
      border-left:4px solid #2563eb;padding-left:8px}}
 .muted{{color:#64748b;font-size:12px}} .small{{font-size:12px}}
 .mono{{font-family:Consolas,monospace;font-size:13px}}
 .stats{{display:flex;gap:14px;flex-wrap:wrap;margin:14px 0}}
 .stat{{background:#fff;border:1px solid #e2e8f0;border-radius:10px;
        padding:12px 20px;min-width:120px}}
 .stat b{{font-size:24px;display:block}}
 table{{border-collapse:collapse;width:100%;background:#fff;font-size:13px}}
 th,td{{border:1px solid #e2e8f0;padding:7px 9px;text-align:left;vertical-align:top}}
 th{{background:#f1f5f9}} td.num{{text-align:right;font-family:Consolas,monospace}}
 .pill{{border:1px solid;border-radius:999px;padding:1px 10px;font-size:12px;
        white-space:nowrap}}
 .reason{{color:#dc2626;font-size:12px;margin-top:4px}}
 .reason.na{{color:#d97706}}
 .brow{{display:flex;align-items:center;gap:10px;margin:4px 0;font-size:12px}}
 .bname{{width:230px;font-family:Consolas,monospace;text-align:right}}
 .btrack{{flex:1;background:#e2e8f0;border-radius:4px;height:14px;overflow:hidden}}
 .bbar{{display:block;height:100%}}
 .bval{{width:70px;font-family:Consolas,monospace}}
 .card{{background:#fff;border:1px solid #e2e8f0;border-radius:10px;
        padding:14px 16px;margin:12px 0}}
 .chead{{display:flex;gap:12px;align-items:center;margin-bottom:6px}}
 .interp{{font-size:12px;color:#334155;background:#f1f5f9;border-radius:6px;
          padding:8px 10px;margin:8px 0;white-space:pre-wrap}}
 .imgs{{display:flex;gap:10px;flex-wrap:wrap;margin-top:8px}}
 figure{{margin:0}} figure img{{max-width:220px;max-height:220px;
        border:1px solid #e2e8f0;border-radius:6px;display:block}}
 figcaption{{font-size:11px;color:#64748b;max-width:220px;word-break:break-all}}
</style></head><body>
<h1>AnomalyClaw 工具批量评估报告（无 LLM）</h1>
<div class="muted">item <b>{_esc(report['item_id'])}</b> ·
 {_esc(report.get('category'))} · {_esc(report.get('domain_code'))} ·
 query={_esc(Path(report['query_path']).name)} ·
 refs={report['n_refs']} · 原图 {report['image_size'][0]}×{report['image_size'][1]}</div>

<div class="stats">
 <div class="stat"><b>{n}</b>工具总数</div>
 <div class="stat"><b style="color:#16a34a">{ok}</b>成功</div>
 <div class="stat"><b style="color:#d97706">{na}</b>不适用</div>
 <div class="stat"><b style="color:#dc2626">{fail}</b>失败</div>
 <div class="stat"><b>{rate:.0f}%</b>成功率</div>
 <div class="stat"><b>{report['total_duration_ms']/1000:.2f}s</b>总耗时</div>
</div>

<h2>执行耗时（毫秒，降序）</h2>
{bars}

<h2>调用明细表</h2>
<table><thead><tr><th>工具</th><th>类别</th><th>输入参数</th><th>状态 / 原因</th>
<th>耗时 ms</th><th>输出摘要</th><th>图像数</th></tr></thead>
<tbody>{rows}</tbody></table>

<h2>逐工具输出卡片（含中间图像）</h2>
{cards}
</body></html>"""
    path = outdir / "tool_run_report.html"
    path.write_text(html, encoding="utf-8")
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--item_id", default="D1_0029")
    ap.add_argument("--manifest",
                    default="benchmark/manifests_v2/D1_industrial_manifest.json")
    ap.add_argument("--outdir", default=None,
                    help="default: output/<item_id>_tools")
    args = ap.parse_args()

    manifest = args.manifest
    if not os.path.isabs(manifest):
        manifest = str(REPO_ROOT / manifest)
    item = _load_item(manifest, args.item_id)
    item["query_path"] = resolve_data_path(item["query_path"])
    item["ref_paths"] = [resolve_data_path(p) for p in (item.get("ref_paths") or [])]

    outdir = Path(args.outdir) if args.outdir else REPO_ROOT / "output" / f"{args.item_id}_tools"
    if not outdir.is_absolute():
        outdir = REPO_ROOT / outdir
    outdir.mkdir(parents=True, exist_ok=True)

    if _patch_retriever_local_weights():
        print("DINOv2 retrieval: using local weights (weights/dinov2/model.safetensors)")
    print(f"Item {args.item_id}: query={item['query_path']}")
    print(f"Running {len(_t8.TOOL_REGISTRY)} tools (no LLM) → {outdir}\n")
    report = run_all(item, outdir)
    html = render_html(report, outdir)

    print(f"\n{'─' * 60}")
    print(f"success {report['n_success']} / not_applicable {report['n_not_applicable']}"
          f" / failed {report['n_failed']}   (total {report['n_tools']})")
    print(f"JSON  → {outdir / 'tool_run_report.json'}")
    print(f"HTML  → {html}")


if __name__ == "__main__":
    main()
