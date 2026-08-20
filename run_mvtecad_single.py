#!/usr/bin/env python3
"""
Single-image MVTec-AD anomaly detection pipeline using AnomalyClaw v12.

Runs the identical v12 passive pipeline that produced
  benchmark/results/v2/v12_passive_test/D1.json
Output format matches that file exactly.

以 {DATA_ROOT} 开头的路径需要 export ANOMALYCLAW_DATA=/path/to/AnomalyClaw/benchmark/data

Two usage modes
───────────────
Mode A — pull an existing benchmark item from the D1 manifest
  (lets you reproduce D1.json results one item at a time):

    python run_mvtecad_single.py \
        --item_id D1_0145 \
        --manifest benchmark/manifests_v2/D1_industrial_manifest.json \
        --backend qwen3 \
        --output output/D1_0145.json

python run_mvtecad_single.py --item_id D1_0029 --backend qwen3 --output output/D1_0029.json 

Mode B — supply your own query + reference images:

    python run_mvtecad_single.py \
        --query /data/MVTec-AD/hazelnut/test/crack/001.png \
        --refs  /data/MVTec-AD/hazelnut/train/good/081.png \
                /data/MVTec-AD/hazelnut/train/good/380.png \
        --category hazelnut \
        --backend qwen3 \
        --output output/my_result.json

Backend environment variables
─────────────────────────────
  GPT backend  :  GPT_API_KEY (required)
                  GPT_API_BASE (optional, for proxies / custom endpoints)
                  GPT_MODEL   (optional, default: gpt-4o)

  Qwen3 backend:  QWEN_API_KEY (optional, default "EMPTY")
                  QWEN_API_BASE (optional, default http://localhost:8000/v1)
                  QWEN_MODEL  (optional, default: Qwen3-VL-8B-Instruct)

  SeedVL backend: SEED_API_KEY (required)
                  SEED_API_BASE (optional)
                  SEED_MODEL  (optional)

Data path resolution
────────────────────
  Manifest paths begin with {DATA_ROOT}/ and are expanded at runtime via
  the ANOMALYCLAW_DATA environment variable.  If the variable is not set
  the code falls back to <repo>/benchmark/data.

  Custom paths (Mode B) are used as-is; absolute paths are recommended.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# ── resolve benchmark/scripts so local imports work ──────────────────────────
REPO_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = REPO_ROOT / "benchmark" / "scripts"
os.environ["ANOMALYCLAW_DATA"] = str(REPO_ROOT / "benchmark" / "data")
sys.path.insert(0, str(SCRIPTS_DIR))  # prepend benchmark/scripts to sys.path so local imports work

import agent_v12 as _v12
import agent_v9 as _v9
import agent_v11 as _v11
import agent_tools_v8 as _t8
import infer as _infer
from infer import get_client, get_model_name, resolve_data_path
# from .benchmark.scripts import agent_v12 as _v12
# from .benchmark.scripts.infer import get_client, get_model_name


# ── visualization: capture tool-observation images & build a summary panel ────

from base64 import b64decode

from PIL import Image, ImageDraw, ImageFont

_VIS = {"dir": None, "count": 0}   # filled in by main() when --save_vis is on

_TOOL_IMG_KEYS = (
    "crop_b64", "diff_mask_b64", "aligned_diff_b64", "composite_b64",
    "heatmap_b64", "blob_layout_b64", "change_heatmap_b64", "spectrum_b64",
)

# keep the real dispatch around before main() patches _t8.dispatch_tool
_ORIG_DISPATCH = _t8.dispatch_tool

# ── conversation logging: capture every LLM call's inputs & raw output ────────

_CONV = {"calls": []}


def _sanitize_messages(messages: list) -> list:
    """Deep-copy a messages list with image b64 data-urls replaced by short
    placeholders, so the transcript JSON stays readable and small."""
    out = []
    for m in messages:
        content = m.get("content")
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("image_url"), dict):
                    url = part["image_url"].get("url")
                    parts.append({
                        "type": "image_url",
                        "image_url": {"url": f"<image data-url, {len(url or '')} chars>"},
                    })
                else:
                    parts.append(part)
            out.append({"role": m.get("role"), "content": parts})
        else:
            out.append({"role": m.get("role"), "content": content})
    return out


def _make_call_llm_hook(tag: str, orig):
    """Wrap one module's `call_llm` reference so each API call is recorded:
    full input messages (images placeholdered) + the model's raw text output."""
    def hook(client, model, messages, *args, **kwargs):
        entry = {
            "call": len(_CONV["calls"]) + 1,
            "branch": tag,                       # v9_agent | direct | tool
            "model": model,
            "params": {"args": list(args), **kwargs},
            "input_messages": _sanitize_messages(messages),
        }
        _CONV["calls"].append(entry)
        try:
            text, pin, pout = orig(client, model, messages, *args, **kwargs)
        except Exception as exc:
            entry["error"] = f"{type(exc).__name__}: {exc}"
            raise
        entry["raw_response"] = text
        entry["usage"] = {"prompt_tokens": pin, "completion_tokens": pout}
        return text, pin, pout
    return hook


def _install_conversation_hooks() -> None:
    """Each module did `from infer import call_llm`, holding its own reference,
    and infer.run_v0 (direct branch) uses infer's own global — so every
    reference must be patched individually to catch all API calls."""
    _v9.call_llm = _make_call_llm_hook("v9_agent", _v9.call_llm)
    _v11.call_llm = _make_call_llm_hook("direct", _v11.call_llm)
    _t8.call_llm = _make_call_llm_hook("tool", _t8.call_llm)
    _v12.call_llm = _make_call_llm_hook("v12", _v12.call_llm)
    _infer.call_llm = _make_call_llm_hook("direct", _infer.call_llm)


def _save_conversation(item: dict, model: str, backend: str, path: Path) -> None:
    transcript = {
        "item_id": item.get("item_id"),
        "backend": backend,
        "model": model,
        "note": "每一个 call 是一次独立的 LLM API 调用：input_messages 是发送给模型的"
                "完整对话（图像以占位符表示），raw_response 是模型的原始输出文本。"
                "branch 标记来源：v9_agent=多轮agent循环, direct=直接判别分支, "
                "tool=工具内部的 LLM 调用。",
        "n_calls": len(_CONV["calls"]),
        "calls": _CONV["calls"],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(transcript, fh, indent=2, ensure_ascii=False, default=str)


def _save_b64(b64: str, path: Path) -> None:
    """Decode a b64 image (tools emit JPEG bytes) and re-save as a real PNG,
    so file content matches the .png extension."""
    import io
    Image.open(io.BytesIO(b64decode(b64))).save(path, format="PNG")


def _vis_dispatch_tool(name: str, args: dict, ctx: dict | None = None) -> dict:
    """Wrapper around agent_tools_v8.dispatch_tool that dumps every image the
    tool produced (heatmaps, diff masks, FFT spectra, tiles, retrieved refs)
    into the visualization directory, then returns the observation unchanged."""
    observation = _ORIG_DISPATCH(name, args, ctx)
    vis_dir = _VIS["dir"]
    if vis_dir is None:
        return observation
    try:
        _VIS["count"] += 1
        tag = f"{_VIS['count']:02d}_{name}"
        # bbox-using tools expect 256x256 normalized coords; a model that sends
        # original-image pixel coords gets its bbox clamped to a ~1px strip and
        # the crop/composite images come out degenerate.  Warn, don't fix —
        # the saved image must stay faithful to what the model actually saw.
        bbox = (args or {}).get("bbox") if isinstance(args, dict) else None
        if bbox and any(not (0 <= float(v) <= 255) for v in bbox):
            print(f"  [vis] note: {name} bbox {bbox} outside 0-255 normalized "
                  f"range — tool clamped it, image may be degenerate")
        for key in _TOOL_IMG_KEYS:
            if b64 := observation.get(key):
                _save_b64(b64, vis_dir / f"{tag}_{key[:-4]}.png")
        for i, tile in enumerate(observation.get("tiles", [])[:9]):
            if b64 := tile.get("crop_b64"):
                _save_b64(b64, vis_dir / f"{tag}_tile{i}.png")
        for i, b64 in enumerate(observation.get("retrieved_images_b64", [])[:4]):
            _save_b64(b64, vis_dir / f"{tag}_ref{i}.png")
        # keep the text observation in a sidecar json for traceability
        text_obs = {k: v for k, v in observation.items()
                    if isinstance(v, (str, int, float, list, dict))
                    and not k.endswith("_b64")
                    and k != "tiles"}
        (vis_dir / f"{tag}_observation.json").write_text(
            json.dumps({"tool": name, "args": args, "observation_text": text_obs},
                       indent=2, ensure_ascii=False, default=str),
            encoding="utf-8")
    except Exception as exc:   # visualization must never break the pipeline
        print(f"  [vis] failed to save images for {name}: {exc}")
    return observation


def _find_gt_mask(query_path: str) -> str | None:
    """MVTec-AD layout: <cat>/test/<defect>/000.png  →
    <cat>/ground_truth/<defect>/000_mask.png"""
    p = Path(resolve_data_path(query_path))
    try:
        mask = p.parent.parent / "ground_truth" / p.parent.name / (p.stem + "_mask.png")
        return str(mask) if mask.exists() else None
    except Exception:
        return None


def _load_image(path: str, max_side: int = 400) -> Image.Image:
    img = Image.open(resolve_data_path(path)).convert("RGB")
    img.thumbnail((max_side, max_side))
    return img


def _label(img: Image.Image, text: str) -> Image.Image:
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
    draw.rectangle([0, 0, img.width, 22], fill=(0, 0, 0))
    draw.text((6, 3), text, fill=(255, 255, 0), font=font)
    return img


def _save_summary_panel(result: dict, item: dict, vis_dir: Path) -> None:
    """One overview PNG: query / first refs / GT-mask overlay / score banner."""
    cells = []
    cells.append(_label(_load_image(item["query_path"]), "QUERY"))
    for i, ref in enumerate((item.get("ref_paths") or [])[:3]):
        cells.append(_label(_load_image(ref), f"REF{i + 1}"))

    mask_path = _find_gt_mask(item["query_path"])
    if mask_path:
        q = _load_image(item["query_path"]).convert("RGB")
        m = Image.open(mask_path).convert("L").resize(q.size)
        overlay = q.copy()
        red = Image.new("RGB", q.size, (255, 0, 0))
        overlay.paste(red, (0, 0), m)
        cells.append(_label(Image.blend(q, overlay, 0.4), "GT MASK"))

    h = max(c.height for c in cells)
    w = sum(c.width for c in cells) + 10 * (len(cells) + 1)
    panel = Image.new("RGB", (w, h + 70), (24, 24, 24))
    x = 10
    for c in cells:
        panel.paste(c, (x, 10))
        x += c.width + 10

    draw = ImageDraw.Draw(panel)
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
    score = result.get("anomaly_score")
    verdict = "N/A" if score is None else ("ANOMALOUS" if score > 0.5 else "NORMAL")
    gt = result.get("label_gt")
    gt_str = "—" if gt is None else ("anomalous" if gt == 1 else "normal")
    mark = ""
    if score is not None and gt is not None:
        mark = "  [CORRECT]" if (score > 0.5) == (gt == 1) else "  [WRONG]"
    lines = [
        f"{result['item_id']}  ({item.get('category', '?')} / {result.get('domain_code', 'D1')})",
        f"anomaly_score={score:.4f} → {verdict}   "
        f"(direct={result.get('direct_score')}, v9={result.get('v9_score')})",
        f"ground_truth={gt_str}{mark}   tools_used={result.get('tools_used') or '(none)'}",
    ]
    y = h + 25
    for line in lines:
        draw.text((12, y), line, fill=(0, 255, 128), font=font)
        y += 22
    panel.save(vis_dir / "summary_panel.png")


def _run_probe_tools(item: dict, vis_dir: Path) -> int:
    """Run a few read-only pure-CV tools directly (no LLM involved) so there is
    always some intermediate visualization, even when the agent went straight
    to `final` without calling any tool.  Files are prefixed p01_/p02_/… to
    distinguish them from real agent calls (01_/02_/…)."""
    ctx = {
        "query_path": item["query_path"],
        "ref_paths": item.get("ref_paths") or [],
        "item_id": item.get("item_id"),
        "split": item.get("split", "test"),
        "_manifest_domain": item.get("domain_code"),
    }
    probes = [
        ("tool_side_by_side", {"bbox": [0, 0, 256, 256]}),  # query | refs 拼图
        ("tool_image_diff",   {"threshold": 30.0}),        # 像素级 diff mask
        ("tool_texture_fft",  {}),                         # FFT 频谱
    ]
    n_saved = 0
    for i, (name, args) in enumerate(probes, 1):
        observation = _ORIG_DISPATCH(name, dict(args), ctx)
        tag = f"p{i:02d}_{name}"
        try:
            for key in _TOOL_IMG_KEYS:
                if b64 := observation.get(key):
                    _save_b64(b64, vis_dir / f"{tag}_{key[:-4]}.png")
                    n_saved += 1
            for j, tile in enumerate(observation.get("tiles", [])[:9]):
                if b64 := tile.get("crop_b64"):
                    _save_b64(b64, vis_dir / f"{tag}_tile{j}.png")
                    n_saved += 1
            if observation.get("error"):
                print(f"  [vis] probe {name}: {observation['error']}")
        except Exception as exc:
            print(f"  [vis] probe {name} failed: {exc}")
    return n_saved


# ── helpers ───────────────────────────────────────────────────────────────────

def _load_item_from_manifest(manifest_path: str, item_id: str) -> dict:
    with open(manifest_path, encoding="utf-8") as fh:
        items = json.load(fh)
    for item in items:
        if item.get("item_id") == item_id:
            return item
    sample_ids = [x.get("item_id") for x in items[:10]]
    raise ValueError(
        f"item_id {item_id!r} not found in {manifest_path}.\n"
        f"First 10 available IDs: {sample_ids}"
    )


def _build_item_from_paths(query: str, refs: list[str],
                            category: str, item_id: str = "custom_001") -> dict:
    return {
        "item_id":        item_id,
        "domain":         "industrial",
        "domain_code":    "D1",
        "query_path":     query,
        "ref_paths":      refs,
        "label":          None,
        "anomaly_type":   None,
        "source_dataset": "MVTec-AD",
        "category":       category,
        "split":          "test",
    }


def _print_summary(result: dict) -> None:
    sep = "─" * 62
    print(f"\n{'═' * 62}")
    print(f"  AnomalyClaw v12 Passive — Result")
    print(f"{'═' * 62}")
    print(f"  item_id   : {result['item_id']}")
    print(f"  domain    : {result.get('domain_code', 'D1')}  (MVTec-AD industrial)")
    print(f"  category  : {result.get('category', '—')}")

    score = result.get("anomaly_score")
    if score is not None:
        verdict = "ANOMALOUS" if score > 0.5 else "NORMAL"
        print(f"\n  anomaly_score : {score:.4f}  →  {verdict}")
    else:
        print(f"\n  anomaly_score : N/A")

    print(f"  direct_score  : {result.get('direct_score')}")
    print(f"  v9_score      : {result.get('v9_score')}")

    gt = result.get("label_gt")
    if gt is not None:
        gt_str = "anomalous" if gt == 1 else "normal"
        correct = (score is not None) and ((score > 0.5) == (gt == 1))
        mark = "CORRECT" if correct else "WRONG"
        print(f"  ground_truth  : {gt_str}  ({mark})")

    print(f"\n  agent_turns   : {result.get('n_turns', 0)}")
    tools = result.get("tools_used") or []
    print(f"  tools_used    : {tools if tools else '(none)'}")
    print(f"  confidence    : {result.get('confidence', 0)}")

    rationale = (result.get("rationale") or "").strip()
    if rationale:
        snippet = rationale[:300] + ("…" if len(rationale) > 300 else "")
        print(f"\n  agent rationale:\n    {snippet}")

    dr_raw = result.get("direct_rationale") or ""
    if isinstance(dr_raw, str) and dr_raw.strip():
        try:
            dr = json.loads(dr_raw)
            evidence = (dr.get("evidence") or "").strip()
            if evidence:
                snippet = evidence[:200] + ("…" if len(evidence) > 200 else "")
                print(f"\n  direct evidence:\n    {snippet}")
        except Exception:
            pass

    errors = [e for e in [result.get("error"), result.get("direct_error")] if e]
    if errors:
        print(f"\n  errors: {errors}")

    print(f"{'═' * 62}\n")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Run AnomalyClaw v12 passive pipeline on one MVTec-AD image.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Mode A
    ap.add_argument(
        "--item_id", default=None, metavar="D1_XXXX",
        help="Item ID from the D1 manifest, e.g. D1_0077  (Mode A)"
    )
    ap.add_argument(
        "--manifest",
        default="benchmark/manifests_v2/D1_industrial_manifest.json",
        help="Path to the D1 manifest JSON  (default: benchmark/manifests_v2/D1_industrial_manifest.json)"
    )

    # Mode B
    ap.add_argument("--query", default=None,
                    help="Path to the query image  (Mode B)")
    ap.add_argument("--refs", nargs="+", default=None,
                    help="Paths to reference normal images  (Mode B)")
    ap.add_argument("--category", default="unknown",
                    help="MVTec-AD category name, e.g. hazelnut  (Mode B)")

    # Shared
    ap.add_argument("--backend", choices=["gpt", "seedvl", "qwen3"], default="qwen3",
                    help="LLM backend  (default: qwen3)")
    ap.add_argument("--output", default="output/single_result.json",
                    help="Output JSON path  (default: output/single_result.json)")
    ap.add_argument("--max_turns", type=int, default=4,
                    help="Maximum agent turns  (default: 4)")
    ap.add_argument("--w_direct", type=float, default=0.5,
                    help="Weight for direct-branch score  (default: 0.5)")
    ap.add_argument("--w_v9", type=float, default=0.5,
                    help="Weight for v9-agent score  (default: 0.5)")

    ap.add_argument("--save_vis", action="store_true", default=True,
                    help="Save intermediate tool images + summary panel  (default: on)")
    ap.add_argument("--no_vis", dest="save_vis", action="store_false",
                    help="Disable visualization output")

    args = ap.parse_args()

    # ── resolve item ─────────────────────────────────────────────────────────
    if args.item_id is not None:
        manifest_path = args.manifest
        if not os.path.isabs(manifest_path):
            manifest_path = str(REPO_ROOT / manifest_path)
        print(f"[Mode A] Loading {args.item_id!r} from {manifest_path}")
        item = _load_item_from_manifest(manifest_path, args.item_id)
        n_refs = len(item.get("ref_paths") or [])
        gt_str = {0: "normal", 1: "anomalous"}.get(item.get("label"), "unknown")
        print(f"         query   : {item['query_path']}")
        print(f"         refs    : {n_refs} reference images")
        print(f"         label   : {gt_str}  (split: {item.get('split', '?')})")

    elif args.query is not None:
        if not args.refs:
            ap.error("--refs is required in Mode B (provide at least one reference image)")
        item = _build_item_from_paths(args.query, args.refs, args.category)
        print(f"[Mode B] Custom image")
        print(f"         query    : {args.query}")
        print(f"         refs     : {args.refs}")
        print(f"         category : {args.category}")

    else:
        ap.error(
            "Specify either --item_id (Mode A: manifest item)\n"
            "or --query + --refs (Mode B: custom image)."
        )

    # Expand {DATA_ROOT} placeholders to real paths BEFORE the run: the agent
    # tool ctx carries item["query_path"] verbatim, and tools Image.open() it
    # directly, so placeholder paths would make every tool call fail.
    item["query_path"] = resolve_data_path(item["query_path"])
    item["ref_paths"] = [resolve_data_path(p) for p in (item.get("ref_paths") or [])]
    print(f"\n         resolved query: {item['query_path']}")

    # ── init backend ─────────────────────────────────────────────────────────
    vis_dir = None
    if args.save_vis:
        out_path_pre = Path(args.output)
        if not out_path_pre.is_absolute():
            out_path_pre = REPO_ROOT / out_path_pre
        vis_dir = out_path_pre.parent / (out_path_pre.stem + "_vis")
        vis_dir.mkdir(parents=True, exist_ok=True)
        _VIS["dir"] = vis_dir
        _t8.dispatch_tool = _vis_dispatch_tool      # hook the v8 tool dispatch
        _install_conversation_hooks()               # hook every LLM call
        print(f"Visualization → {vis_dir}")
    print(f"\nInitialising {args.backend!r} backend …")
    client = get_client(args.backend)
    model  = get_model_name(args.backend)
    print(f"Model : {model}")

    # ── run pipeline ─────────────────────────────────────────────────────────
    print(
        f"\nRunning v12 passive pipeline  "
        f"(max_turns={args.max_turns}, "
        f"w_direct={args.w_direct}, w_v9={args.w_v9}) …"
    )
    t0 = time.time()

    result = _v12.run_v12_item(
        client=client,
        model=model,
        item=item,
        split=item.get("split", "test"),
        max_turns=args.max_turns,
        w_direct=args.w_direct,
        w_v9=args.w_v9,
        learning_enabled=False,   # passive mode — same settings as D1.json
    )

    elapsed = time.time() - t0
    print(f"Completed in {elapsed:.1f}s")

    # Attach the human-readable category field (not in the agent output)
    result["category"] = item.get("category", args.category)

    # ── save ─────────────────────────────────────────────────────────────────
    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = REPO_ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
    print(f"Result saved → {out_path}")

    if vis_dir is not None:
        conv_path = out_path.parent / (out_path.stem + "_conversation.json")
        try:
            _save_conversation(item, model, args.backend, conv_path)
            print(f"Conversation transcript ({len(_CONV['calls'])} LLM calls) "
                  f"→ {conv_path}")
        except Exception as exc:
            print(f"[vis] conversation transcript failed: {exc}")

    if vis_dir is not None:
        try:
            _save_summary_panel(result, item, vis_dir)
            print(f"Summary panel → {vis_dir / 'summary_panel.png'}")
        except Exception as exc:
            print(f"[vis] summary panel failed: {exc}")
        try:
            if not (result.get("tools_used") or []):
                print("Agent made no tool calls — running probe tools "
                      "(pure CV, no LLM) for visualization …")
            n = _run_probe_tools(item, vis_dir)
            print(f"Probe visualizations saved: {n} image(s) → {vis_dir}")
            print(f"Agent tool calls with images: {_VIS['count']} → {vis_dir}")
        except Exception as exc:
            print(f"[vis] probe tools failed: {exc}")

    _print_summary(result)


if __name__ == "__main__":
    main()
