#!/usr/bin/env python3
"""
Tool-influence ablation experiment: how do the three most-used tools
(tool_side_by_side / tool_expert_score / tool_reference_profiler) change
qwen3-VL's anomaly judgment inside the real v12 agent loop?

Design
-------
For each manifest item, run agent_v12.run_v12_item (question=None ->
anomaly-detection mode) under 5 tool-availability conditions. The v8
dispatcher is gated per condition: a disabled tool returns an explicit
"disabled in this ablation condition" error observation, which the agent
sees and must adapt to. Everything is instrumented by wrapping
agent_v9.call_llm (captures the exact messages sent to the VLM each turn,
plus thinking / reasoning_content when the backend provides it) and
agent_tools_v8.dispatch_tool (captures args / observation / images).

    none               : {}                                  (pure-vision baseline)
    expert_score       : {tool_expert_score}
    side_by_side       : {tool_side_by_side}
    reference_profiler : {tool_reference_profiler}
    except_expert      : {tool_side_by_side, tool_reference_profiler}

Saved per item/<condition>/ :
    conversation.json     chronological transcript: llm calls (thinking +
                          response action JSON) interleaved with tool calls
    llm_calls/*.json      one file per VLM call: message delta (text parts +
                          image file refs), raw response, thinking, tokens
    tool_calls/*.json     one file per tool call: name, args, observation
                          summary, duration, emitted-image list
    images/*.png          every image that ever entered the VLM context or
                          was produced by a tool (deduplicated by md5)
    result.json           final v12 verdict: scores, rationale, confidence,
                          tools_used, denied attempts, refutation trace
Saved per item/:
    comparison.html       visual dashboard comparing the 5 conditions
    summary_item.json     machine-readable cross-condition table
Saved at outdir root:
    summary.json, index.html

Usage
-----
    set QWEN_API_KEY=...            (dashscope compatible-mode key)
    python exp_tool_influence.py --item_ids D1_0029
    python exp_tool_influence.py --item_ids D1_0029 D1_0003 --max_turns 4
    python exp_tool_influence.py --item_ids D1_0029 --no-thinking   # skip
                          reasoning_content capture (matches benchmark call)

Notes
-----
- The Direct (run_v0) branch of run_v12_item is called once per item and
  cached across conditions (temperature=0 makes it deterministic), so every
  condition gets the same direct_score anchor at 1x cost.
- With --thinking (default on) the agent-loop calls enable qwen thinking;
  the reasoning stream is stored in llm_calls/*.json as "thinking". If the
  backend rejects the parameter the call silently falls back to the
  benchmark default (thinking off) and the file records
  "thinking_captured": false.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import threading
import time
from base64 import b64decode
from io import BytesIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = REPO_ROOT / "benchmark" / "scripts"
os.environ.setdefault("ANOMALYCLAW_DATA", str(REPO_ROOT / "benchmark" / "data"))
sys.path.insert(0, str(SCRIPTS_DIR))

from PIL import Image  # noqa: E402


### only for checking ###
from benchmark.scripts import agent_tools_v8 as _t8
from benchmark.scripts import agent_v9 as _v9
from benchmark.scripts import agent_v12 as _v12
from benchmark.scripts.infer import (
    extract_json, get_client, get_model_name, resolve_data_path,
)

# import agent_tools_v8 as _t8
# import agent_v9 as _v9
# import agent_v12 as _v12
# from infer import extract_json, get_client, get_model_name, resolve_data_path

TOOL_IMG_KEYS = (
    "crop_b64", "diff_mask_b64", "aligned_diff_b64", "composite_b64",
    "heatmap_b64", "blob_layout_b64", "change_heatmap_b64", "spectrum_b64",
)

CONDITIONS: dict[str, set[str]] = {
    "none":               set(),
    "expert_score":       {"tool_expert_score"},
    "side_by_side":       {"tool_side_by_side"},
    "reference_profiler": {"tool_reference_profiler"},
    "except_expert":      {"tool_side_by_side", "tool_reference_profiler"},
}

TOOL_LABELS = {
    "tool_expert_score": "expert_score",
    "tool_side_by_side": "side_by_side",
    "tool_reference_profiler": "reference_profiler",
}


# ─── instrumentation ─────────────────────────────────────────────────────────

class RunRecorder:
    """Patches the v12 agent loop for one (item, condition) run.

    - agent_v9.call_llm       -> record messages delta + response + thinking
    - agent_tools_v8.dispatch_tool -> gate by allowed set + record calls
    - agent_v12._direct_blocking   -> cache per item across conditions

    Only the agent-loop LLM calls go through the patched path; tool-internal
    VLM calls (reference_profiler) use the stock infer.call_llm and appear
    here only through the tool observation + duration.
    """

    def __init__(self, condition: str, allowed: set[str], outdir: Path,
                 thinking: bool):
        self.condition = condition
        self.allowed = allowed
        self.outdir = outdir
        self.thinking = thinking
        self.img_dir = outdir / "images"
        self.llm_dir = outdir / "llm_calls"
        self.tool_dir = outdir / "tool_calls"
        for d in (self.img_dir, self.llm_dir, self.tool_dir):
            d.mkdir(parents=True, exist_ok=True)
        self.events: list[dict] = []
        self.llm_calls: list[dict] = []
        self.tool_calls: list[dict] = []
        self._prev_len = 0
        self._img_cache: dict[str, str] = {}
        self._lock = threading.Lock()
        self._t_start = time.perf_counter()
        self._n_thinking_captured = 0
        self.total_tokens_in = 0
        self.total_tokens_out = 0

    # -- image dedup ---------------------------------------------------------
    def save_image(self, b64: str) -> str:
        h = hashlib.md5(b64.encode()).hexdigest()[:12]
        with self._lock:
            if h in self._img_cache:
                return self._img_cache[h]
            rel = f"images/{h}.png"
            try:
                Image.open(BytesIO(b64decode(b64))).save(self.outdir / rel,
                                                         format="PNG")
            except Exception:
                rel = f"images/{h}.txt"
                (self.outdir / rel).write_text("<undecodable image>", encoding="utf-8")
            self._img_cache[h] = rel
            return rel

    # -- message serialization ----------------------------------------------
    def _serialize_content(self, content) -> list[dict]:
        parts = []
        if isinstance(content, str):
            return [{"type": "text", "text": content}]
        if not isinstance(content, list):
            return [{"type": "raw", "text": str(content)[:300]}]
        for p in content:
            pd = p if isinstance(p, dict) else {"raw": str(p)}
            if pd.get("type") == "text":
                parts.append({"type": "text", "text": pd.get("text", "")})
            elif pd.get("type") == "image_url":
                url = (pd.get("image_url") or {}).get("url", "")
                if url.startswith("data:image"):
                    parts.append({"type": "image",
                                  "ref": self.save_image(url.split(",", 1)[1])})
                else:
                    parts.append({"type": "image_url", "url": url[:120]})
            else:
                parts.append({"type": str(pd.get("type", "?")),
                              "text": str(pd)[:200]})
        return parts

    def _serialize_messages(self, messages: list) -> list[dict]:
        out = []
        for m in messages:
            if isinstance(m, dict):
                out.append({"role": m.get("role"),
                            "parts": self._serialize_content(m.get("content"))})
            else:
                out.append({"role": "?", "parts": [{"type": "raw",
                            "text": str(m)[:200]}]})
        return out

    # -- patched call_llm ----------------------------------------------------
    def _chat_thinking_variants(self, client, model, messages,
                                max_tokens, temperature):
        """Enable thinking with a fallback chain over extra_body variants."""
        variants = [
            {"enable_thinking": True,
             "chat_template_kwargs": {"enable_thinking": True}},
            {"chat_template_kwargs": {"enable_thinking": True}},
            {"enable_thinking": True},
        ]
        last_err = None
        for extra in variants:
            temp = temperature
            for _ in range(2):  # second pass bumps temperature if rejected
                try:
                    resp = client.chat.completions.create(
                        model=model, messages=messages,
                        max_tokens=max(32e3, max_tokens * 3),
                        temperature=temp, extra_body=extra)
                    return resp, True, temp
                except Exception as e:
                    last_err = e
                    if "temperature" in str(e).lower() and temp == 0.0:
                        temp = 0.6
                        continue
                    break
        # final fallback: benchmark default (thinking off)
        resp = client.chat.completions.create(
            model=model, messages=messages,
            max_tokens=max_tokens, temperature=temperature)
        return resp, False, temperature

    def make_patched_call_llm(self, orig_call_llm):
        def patched_call_llm(client, model, messages,
                             max_tokens=10e3, temperature=0.0):
            t0 = time.perf_counter()
            new_msgs = messages[self._prev_len:]
            self._prev_len = len(messages)
            snapshot = self._serialize_messages(new_msgs)
            reasoning = None
            thinking_ok = False
            is_qwen = "qwen" in str(model).lower()
            if self.thinking and is_qwen:
                try:
                    resp, thinking_ok, temp_used = self._chat_thinking_variants(
                        client, model, messages, max_tokens, temperature)
                    msg = resp.choices[0].message
                    text = msg.content or ""
                    reasoning = getattr(msg, "reasoning_content", None)
                    usage = resp.usage
                    inp = usage.prompt_tokens
                    outp = usage.completion_tokens
                except Exception:
                    text, inp, outp = orig_call_llm(client, model, messages,
                                                    max_tokens, temperature)
                    thinking_ok = False
            else:
                text, inp, outp = orig_call_llm(client, model, messages,
                                                max_tokens, temperature)
            dt = time.perf_counter() - t0
            if reasoning:
                self._n_thinking_captured += 1
            action = extract_json(text) if text else None
            rec = {
                "call_idx": len(self.llm_calls) + 1,
                "latency_s": round(dt, 2),
                "tokens_in": inp,
                "tokens_out": outp,
                "thinking_captured": thinking_ok,
                "temperature": temperature,
                "new_messages": snapshot,
                "thinking": reasoning,
                "response_text": text,
                "parsed_action": action,
            }
            with self._lock:
                self.llm_calls.append(rec)
                self.events.append({"event": "llm_call",
                                    "t": round(time.perf_counter()
                                               - self._t_start, 2),
                                    **{k: rec[k] for k in
                                       ("call_idx", "latency_s",
                                        "thinking_captured")}})
                self.total_tokens_in += inp
                self.total_tokens_out += outp
            (self.llm_dir / f"call_{rec['call_idx']:02d}.json").write_text(
                json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
            return text, inp, outp
        return patched_call_llm

    # -- patched dispatch_tool ------------------------------------------------
    def make_patched_dispatch(self, orig_dispatch):
        def patched_dispatch(name: str, args, ctx=None):
            t0 = time.perf_counter()
            if name not in self.allowed:
                obs = {"error": (
                    f"ablation gate: {name} is disabled in condition "
                    f"'{self.condition}' (allowed: {sorted(self.allowed) or 'none'})")}
            else:
                try:
                    obs = orig_dispatch(name, args, ctx)
                except Exception as exc:
                    obs = {"error": f"dispatcher raised {type(exc).__name__}: {exc}"}
            dt_ms = (time.perf_counter() - t0) * 1000.0

            imgs = []
            for key in TOOL_IMG_KEYS:
                b64 = obs.get(key)
                if isinstance(b64, str) and b64:
                    imgs.append(self.save_image(b64))
            for i, b64 in enumerate(obs.get("retrieved_images_b64") or []):
                if isinstance(b64, str) and b64:
                    imgs.append(self.save_image(b64))
            for t in (obs.get("tiles") or []):
                if isinstance(t, dict) and t.get("crop_b64"):
                    imgs.append(self.save_image(t["crop_b64"]))

            idx = len(self.tool_calls) + 1
            rec = {
                "call_idx": idx,
                "tool": name,
                "enabled": name in self.allowed,
                "args": _sanitize(args),
                "duration_ms": round(dt_ms, 1),
                "images": imgs,
                "observation": _summarize_obs(obs),
            }
            with self._lock:
                self.tool_calls.append(rec)
                self.events.append({"event": "tool_call", "t": round(
                    time.perf_counter() - self._t_start, 2),
                    "call_idx": idx, "tool": name,
                    "enabled": rec["enabled"],
                    "error": obs.get("error")})
            safe = name.replace("tool_", "")
            (self.tool_dir / f"call_{idx:02d}_{safe}.json").write_text(
                json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
            return obs
        return patched_dispatch

    # -- run wrapper -----------------------------------------------------------
    def run(self, client, model, item, split, max_turns):
        self._t_start = time.perf_counter()
        # Build the ablation-gate dispatch wrapper and pass it as dispatch_fn
        # directly into run_v12_item.  This is more reliable than monkey-
        # patching _t8.dispatch_tool because CPython's bytecode specialisation
        # cache can make module-attribute patches invisible inside already-
        # compiled functions.
        patched_dispatch = self.make_patched_dispatch(_t8.dispatch_tool)
        # call_llm is still patched via module attribute (best-effort recording).
        orig_call_llm = _v9.call_llm
        _v9.call_llm = self.make_patched_call_llm(orig_call_llm)
        try:
            result = _v12.run_v12_item(client, model, item, split, max_turns,
                                       dispatch_fn=patched_dispatch)
        finally:
            _v9.call_llm = orig_call_llm
        result["condition"] = self.condition
        result["allowed_tools"] = sorted(self.allowed)
        result["denied_tool_attempts"] = [c["tool"] for c in self.tool_calls
                                          if not c["enabled"]]
        # Override v9's tools_used (which appends even for gated calls) so
        # that only actually-executed tool calls are listed here.
        result["tools_used"] = [c["tool"] for c in self.tool_calls
                                 if c["enabled"]]
        result["tool_call_log"] = [
            {k: c[k] for k in ("call_idx", "tool", "enabled", "duration_ms",
                               "images")} for c in self.tool_calls]
        result["n_llm_calls"] = len(self.llm_calls)
        result["tokens_in"] = self.total_tokens_in
        result["tokens_out"] = self.total_tokens_out
        result["thinking_captured_calls"] = self._n_thinking_captured
        result["wall_time_s"] = round(time.perf_counter() - self._t_start, 1)
        return result


# Direct-branch cache: run_v0 once per item, replay across conditions.
_DIRECT_CACHE: dict[str, dict] = {}
_DIRECT_LOCK = threading.Lock()


def _make_cached_direct(orig_direct):
    def cached_direct(client, model, item, out):
        key = item.get("item_id") or item.get("query_path")
        with _DIRECT_LOCK:
            if key in _DIRECT_CACHE:
                out.update(_DIRECT_CACHE[key])
                return
        orig_direct(client, model, item, out)
        with _DIRECT_LOCK:
            _DIRECT_CACHE[key] = dict(out)
    return cached_direct


# ─── small helpers ────────────────────────────────────────────────────────────

def _sanitize(v, cap: int = 400):
    s = json.dumps(v, ensure_ascii=False, default=str)
    if len(s) > cap:
        s = s[:cap] + "..."
    try:
        return json.loads(s) if len(s) <= cap else s
    except Exception:
        return s


def _summarize_obs(obs: dict) -> dict:
    out = {}
    for k, v in obs.items():
        if k.endswith("_b64"):
            out[k] = f"<image {len(v)} chars>"
        elif k == "tiles":
            out[k] = f"<{len(v)} tiles>"
        elif isinstance(v, str) and len(v) > 500:
            out[k] = v[:500] + "..."
        elif isinstance(v, list) and len(json.dumps(v, default=str)) > 900:
            out[k] = f"<list, {len(v)} items>"
        else:
            out[k] = v
    return out


def _load_items(manifest_path: Path, item_ids: list[str]) -> list[dict]:
    items = json.loads(manifest_path.read_text(encoding="utf-8"))
    by_id = {it.get("item_id"): it for it in items}
    missing = [i for i in item_ids if i not in by_id]
    if missing:
        raise ValueError(f"item(s) {missing} not in {manifest_path}")
    out = []
    for i in item_ids:
        it = dict(by_id[i])
        it["query_path"] = resolve_data_path(it["query_path"])
        it["ref_paths"] = [resolve_data_path(p)
                           for p in (it.get("ref_paths") or [])]
        out.append(it)
    return out


# ─── per-item orchestration ──────────────────────────────────────────────────

def run_item(client, model, item, outdir: Path, max_turns: int,
             thinking: bool, conditions: dict[str, set[str]]) -> dict:
    item_id = item["item_id"]
    split = item.get("split", "test")
    cond_root = outdir / item_id
    cond_root.mkdir(parents=True, exist_ok=True)
    print(f"\n=== item {item_id}  domain={item.get('domain_code')}  "
          f"label_gt={item.get('label')} "
          f"({'ANOMALOUS' if item.get('label') == 1 else 'normal'}) ===")

    results = {}
    for cname, allowed in conditions.items():
        cdir = cond_root / cname
        rec = RunRecorder(cname, allowed, cdir, thinking)
        print(f"  [{cname:>18s}] tools={sorted(allowed) or ['-']} ...",
              end=" ", flush=True)
        try:
            res = rec.run(client, model, item, split, max_turns)
        except Exception as exc:
            res = {"condition": cname, "error": f"{type(exc).__name__}: {exc}",
                   "item_id": item_id}
        results[cname] = res
        # transcript + result
        (cdir / "conversation.json").write_text(
            json.dumps({"item_id": item_id, "condition": cname,
                        "events": rec.events,
                        "llm_calls": [{k: c[k] for k in
                                       ("call_idx", "latency_s", "tokens_in",
                                        "tokens_out", "thinking_captured",
                                        "thinking", "parsed_action")}
                                      for c in rec.llm_calls],
                        "tool_calls": rec.tool_calls},
                       ensure_ascii=False, indent=2), encoding="utf-8")
        (cdir / "result.json").write_text(
            json.dumps(res, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        print(f"v9_score={res.get('v9_score')}  tools={res.get('tools_used')} "
              f" denied={res.get('denied_tool_attempts')} "
              f"({res.get('wall_time_s', '?')}s)")
    return results


# ─── summary + html ──────────────────────────────────────────────────────────

def _score(v):
    try:
        return round(float(v), 3)
    except (TypeError, ValueError):
        return None


def build_summary(item, results: dict) -> dict:
    gt = item.get("label")
    base = results.get("none") or {}
    base_v9 = _score(base.get("v9_score"))
    rows = []
    for cname, res in results.items():
        v9 = _score(res.get("v9_score"))
        row = {
            "condition": cname,
            "allowed_tools": res.get("allowed_tools"),
            "gt_label": gt,
            "direct_score": _score(res.get("direct_score")),
            "v9_initial_score": _score(res.get("v9_initial_score")),
            "v9_updated_score": _score(res.get("v9_updated_score")),
            "v9_final_score": v9,
            "blended_score": _score(res.get("anomaly_score")),
            "pred_label": (1 if (v9 or 0) >= 0.5 else 0) if v9 is not None else None,
            "rationale": (res.get("rationale") or "")[:400],
            "confidence": res.get("confidence"),
            "n_turns": res.get("n_turns"),
            "tools_used": res.get("tools_used"),
            "denied_tool_attempts": res.get("denied_tool_attempts"),
            "n_llm_calls": res.get("n_llm_calls"),
            "tokens": [res.get("tokens_in"), res.get("tokens_out")],
            "thinking_captured_calls": res.get("thinking_captured_calls"),
            "wall_time_s": res.get("wall_time_s"),
            "error": res.get("error"),
        }
        row["correct"] = (row["pred_label"] == gt) if row["pred_label"] is not None and gt is not None else None
        if v9 is not None and base_v9 is not None and cname != "none":
            row["delta_vs_none"] = round(v9 - base_v9, 3)
        else:
            row["delta_vs_none"] = 0.0 if cname == "none" else None
        rows.append(row)
    return {"item_id": item["item_id"], "domain": item.get("domain_code"),
            "gt_label": gt, "conditions": rows}


def _bar(score, color):
    s = 0.0 if score is None else max(0.0, min(1.0, score))
    return (f"<div class='barwrap'><div class='bar' style='width:{s*100:.0f}%;"
            f"background:{color}'></div><span class='barval'>"
            f"{score if score is not None else 'n/a'}</span></div>")


def _badge(ok):
    if ok is None:
        return "<span class='chip gray'>n/a</span>"
    return ("<span class='chip green'>correct</span>" if ok
            else "<span class='chip red'>wrong</span>")


def render_item_html(item, summary: dict, results: dict, path: Path) -> None:
    rows = summary["conditions"]
    gt = summary["gt_label"]
    cards = []
    for row in rows:
        cname = row["condition"]
        res = results.get(cname) or {}
        tools_line = ", ".join(row.get("tools_used") or []) or "none used"
        denied = row.get("denied_tool_attempts") or []
        denied_line = (f"<div class='denied'>denied attempts: "
                       f"{', '.join(denied)}</div>") if denied else ""
        # images produced in this condition
        imgs = []
        for tc in res.get("tool_call_log") or []:
            for im in tc.get("images") or []:
                imgs.append(f"{cname}/{im}")
        img_html = "".join(
            f"<figure><img src='{p}' loading='lazy'><figcaption>{p.split('/')[-1][:18]}</figcaption></figure>"
            for p in imgs[:8])
        # turn timeline from conversation.json
        conv_path = path.parent / cname / "conversation.json"
        try:
            conv = json.loads(conv_path.read_text(encoding="utf-8"))
            timeline = _build_timeline_html(conv)
        except Exception:
            timeline = "<i>conversation.json unavailable</i>"

        cards.append(f"""
<div class="card">
  <h3>{cname}</h3>
  <div class="meta">allowed: {', '.join(row.get('allowed_tools') or []) or 'none'}</div>
  <table class="mini">
    <tr><td>direct (no-agent)</td><td>{_bar(row['direct_score'], '#888')}</td></tr>
    <tr><td>v9 initial</td><td>{_bar(row['v9_initial_score'], '#b0b0d8')}</td></tr>
    <tr><td>v9 updated</td><td>{_bar(row['v9_updated_score'], '#7f77dd')}</td></tr>
    <tr><td>v9 final</td><td>{_bar(row['v9_final_score'], '#e24b4a' if (row['v9_final_score'] or 0) >= 0.5 else '#639922')}</td></tr>
  </table>
  <div class="chips">{_badge(row['correct'])}
    <span class="chip {'red' if gt == 1 else 'green'}">GT={'anomaly' if gt == 1 else 'normal'}</span>
    <span class="chip gray">Δ vs none: {row['delta_vs_none'] if row['delta_vs_none'] is not None else 'n/a'}</span>
    <span class="chip gray">turns: {row['n_turns']}</span>
    <span class="chip gray">tokens: {row['tokens'][0] or 0}/{row['tokens'][1] or 0}</span>
  </div>
  <div class="tools">tools used: {tools_line}</div>
  {denied_line}
  <div class="rationale"><b>rationale:</b> {row['rationale'] or res.get('error') or ''}</div>
  <div class="imgs">{img_html}</div>
  <details><summary>turn-by-turn (thinking + actions + tools)</summary>
    <div class="timeline">{timeline}</div>
  </details>
</div>""")

    table_rows = "".join(
        f"<tr><td>{r['condition']}</td>"
        f"<td>{r['direct_score']}</td><td>{r['v9_initial_score']}</td>"
        f"<td>{r['v9_updated_score']}</td><td><b>{r['v9_final_score']}</b></td>"
        f"<td>{r['delta_vs_none'] if r['delta_vs_none'] is not None else ''}</td>"
        f"<td>{_badge(r['correct'])}</td>"
        f"<td>{', '.join(r.get('tools_used') or []) or '-'}</td>"
        f"<td>{len(r.get('denied_tool_attempts') or [])}</td>"
        f"<td>{r['wall_time_s']}s</td></tr>"
        for r in rows)

    html = f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<title>tool influence - {summary['item_id']}</title>
<style>
body{{font-family:system-ui,'Segoe UI',sans-serif;margin:20px;background:#fafafa;color:#222}}
h1{{font-size:20px}} h3{{margin:0 0 4px;font-size:15px}}
table{{border-collapse:collapse;font-size:12px;background:#fff}}
th,td{{border:1px solid #ddd;padding:4px 8px;text-align:left}}
th{{background:#f0efe9}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(430px,1fr));gap:14px;margin-top:16px}}
.card{{background:#fff;border:1px solid #ddd;border-radius:10px;padding:12px}}
.meta{{color:#777;font-size:11px;margin-bottom:6px}}
.mini td{{border:none;padding:1px 4px;font-size:11px}}
.barwrap{{position:relative;background:#eee;border-radius:4px;height:16px;width:180px;display:inline-block}}
.bar{{height:16px;border-radius:4px}}
.barval{{position:absolute;left:186px;top:0;font-size:11px;line-height:16px}}
.chips{{margin:6px 0}}
.chip{{display:inline-block;border-radius:9px;padding:1px 8px;font-size:11px;margin-right:4px;background:#eee}}
.chip.green{{background:#eaf3de;color:#27500a}}
.chip.red{{background:#fcebeb;color:#791f1f}}
.chip.gray{{background:#f1efe8;color:#555}}
.tools,.denied,.rationale{{font-size:12px;margin:3px 0}}
.denied{{color:#a32d2d}}
.imgs{{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}}
.imgs figure{{margin:0;text-align:center;font-size:10px;color:#777}}
.imgs img{{width:110px;border:1px solid #ccc;border-radius:6px;display:block}}
details{{margin-top:8px}} summary{{cursor:pointer;font-size:12px}}
.timeline{{max-height:420px;overflow-y:auto;font-size:11px;margin-top:6px}}
.step{{border-left:3px solid #d5d3ca;padding:4px 8px;margin:4px 0;background:#fafaf6}}
.step.tool{{border-left-color:#85b7eb}}
.think{{white-space:pre-wrap;background:#f6f4ee;padding:4px;margin:3px 0;max-height:140px;overflow-y:auto}}
.thought{{color:#534ab7}}
.kv{{color:#666}}
</style></head><body>
<h1>Tool influence on VLM judgment - {summary['item_id']}
 (domain {summary['domain']}, GT={'ANOMALOUS' if gt==1 else 'NORMAL'})</h1>
<table>
<tr><th>condition</th><th>direct</th><th>v9 initial</th><th>v9 updated</th>
<th>v9 final</th><th>Δ vs none</th><th>verdict</th><th>tools used</th>
<th>denied</th><th>time</th></tr>
{table_rows}
</table>
<div class="grid">{''.join(cards)}</div>
</body></html>"""
    path.write_text(html, encoding="utf-8")


def _build_timeline_html(conv: dict) -> str:
    """Render a saved conversation.json into timeline HTML (shared by
    render_item_html and render_index)."""
    steps = []
    for c in conv.get("llm_calls") or []:
        act = c.get("parsed_action") or {}
        thought = str(act.get("thought") or "")[:300]
        think = str(c.get("thinking") or "")
        think_head = (think[:400] + "...") if len(think) > 400 else think
        inner = (f"<div class='step'><b>VLM call {c['call_idx']}</b> "
                 f"({c.get('latency_s', '?')}s"
                 f"{', thinking' if c.get('thinking_captured') else ''})")
        if think_head:
            inner += f"<pre class='think'>{think_head}</pre>"
        if thought:
            inner += f"<div class='thought'>thought: {thought}</div>"
        if act:
            inner += (f"<div class='kv'>action={act.get('action')} "
                      f"tool={act.get('tool')} "
                      f"score={act.get('anomaly_score') or act.get('updated_score') or ''}</div>")
        inner += "</div>"
        steps.append(inner)
    for t in conv.get("tool_calls") or []:
        err = (t.get("observation") or {}).get("error")
        gated = err and "ablation gate" in str(err)
        steps.append(
            f"<div class='step tool'><b>tool {t['call_idx']}: {t['tool']}</b>"
            f" ({t['duration_ms']}ms)"
            f"{' <i>— ablation gate</i>' if gated else ''}"
            f"<div class='kv'>args: {json.dumps(t.get('args'), ensure_ascii=False)[:200]}"
            f"</div></div>")
    return "".join(steps) or "<i style='color:#999'>no calls recorded</i>"


# Shared CSS blocks injected into both comparison.html and index.html.
_SHARED_CSS = """
.step{border-left:3px solid #d5d3ca;padding:4px 8px;margin:4px 0;background:#fafaf6}
.step.tool{border-left-color:#85b7eb}
.think{white-space:pre-wrap;background:#f6f4ee;padding:4px;margin:3px 0;
       max-height:120px;overflow-y:auto;font-family:monospace;font-size:10px}
.thought{color:#534ab7;font-size:11px}
.kv{color:#666;font-size:10px}
.timeline{max-height:400px;overflow-y:auto;font-size:11px;margin-top:4px;
          border:1px solid #e8e6e0;border-radius:6px;padding:4px;background:#fafafa}
.barwrap{position:relative;background:#eee;border-radius:4px;height:16px;
         width:180px;display:inline-block}
.bar{height:16px;border-radius:4px}
.barval{position:absolute;left:186px;top:0;font-size:11px;line-height:16px}
.chip{display:inline-block;border-radius:9px;padding:1px 8px;font-size:11px;
      margin-right:4px;background:#eee}
.chip.green{background:#eaf3de;color:#27500a}
.chip.red{background:#fcebeb;color:#791f1f}
.chip.gray{background:#f1efe8;color:#555}
.mini td{border:none;padding:1px 4px;font-size:11px}
"""


def render_index(outdir: Path, all_summaries: list[dict]) -> None:
    # ── overview table ─────────────────────────────────────────────────────────
    head_cells = "".join(f"<th>{c}</th>" for c in CONDITIONS)
    overview_rows = "".join(
        f"<tr><td><a href='#{s['item_id']}'>{s['item_id']}</a>"
        f" <a href='{s['item_id']}/comparison.html' style='font-size:10px'>↗</a></td>"
        f"<td>{s['domain']}</td>"
        f"<td>{'anomaly' if s['gt_label']==1 else 'normal'}</td>"
        + "".join(
            f"<td>{_score(next((r['v9_final_score'] for r in s['conditions'] if r['condition']==c), None))}</td>"
            for c in CONDITIONS)
        + "</tr>"
        for s in all_summaries)

    # ── per-item expandable sections with per-condition timelines ──────────────
    item_sections = ""
    for s in all_summaries:
        item_id = s["item_id"]
        gt = s["gt_label"]
        domain = s["domain"]
        gt_label = ('<span style="color:#c00;font-weight:bold">ANOMALOUS</span>'
                    if gt == 1 else "NORMAL")

        # compact score table
        score_rows = "".join(
            f"<tr><td>{r['condition']}</td>"
            f"<td>{r.get('v9_final_score')}</td>"
            f"<td>{r.get('delta_vs_none') if r.get('delta_vs_none') is not None else '—'}</td>"
            f"<td>{', '.join(r.get('tools_used') or []) or '—'}</td>"
            f"<td>{len(r.get('denied_tool_attempts') or [])}</td>"
            f"<td>{_badge(r.get('correct'))}</td></tr>"
            for r in s["conditions"])

        # per-condition cards
        cond_cards = ""
        for row in s["conditions"]:
            cname = row["condition"]
            conv_path = outdir / item_id / cname / "conversation.json"
            conv: dict = {}
            try:
                conv = json.loads(conv_path.read_text(encoding="utf-8"))
                timeline_html = _build_timeline_html(conv)
            except Exception:
                timeline_html = "<i>conversation.json not found</i>"
            n_llm = len(conv.get("llm_calls") or [])
            n_tool = len(conv.get("tool_calls") or [])
            allowed_str = ", ".join(row.get("allowed_tools") or []) or "none"
            denied = row.get("denied_tool_attempts") or []
            denied_html = (f"<div style='color:#a32d2d;font-size:11px'>"
                           f"denied: {', '.join(denied)}</div>"
                           if denied else "")
            score_color = ('#e24b4a' if (row.get('v9_final_score') or 0) >= 0.5
                           else '#639922')
            rationale = (row.get("rationale") or "")[:200]
            cond_cards += f"""
<div class="card" style="border:1px solid #ddd;border-radius:8px;padding:10px">
  <b style="font-size:13px">{cname}</b>
  <span style="font-size:10px;color:#888;margin-left:6px">allowed: {allowed_str}</span>
  <table class="mini"><tr><td>v9 initial</td><td>{_bar(row.get('v9_initial_score'), '#b0b0d8')}</td></tr>
  <tr><td>v9 final</td><td>{_bar(row.get('v9_final_score'), score_color)}</td></tr></table>
  <div style="margin:4px 0">{_badge(row.get('correct'))}
    <span class="chip gray">Δ {row.get('delta_vs_none') if row.get('delta_vs_none') is not None else 'n/a'}</span>
    <span class="chip gray">turns {row.get('n_turns')}</span>
    <span class="chip gray">tok {(row.get('tokens') or [0,0])[0]}/{(row.get('tokens') or [0,0])[1]}</span>
  </div>
  {denied_html}
  <div style="font-size:11px;color:#444;margin:4px 0">{rationale}</div>
  <details>
    <summary style="cursor:pointer;font-size:11px;color:#2563eb">
      turn-by-turn ({n_llm} VLM calls · {n_tool} tool calls)
    </summary>
    <div class="timeline">{timeline_html}</div>
  </details>
</div>"""

        item_sections += f"""
<details id="{item_id}" style="margin:12px 0;border:1px solid #ccc;
  border-radius:8px;padding:10px 14px;background:#fff">
  <summary style="cursor:pointer;font-size:14px;font-weight:600;list-style:none">
    ▶ {item_id} &nbsp;·&nbsp; domain {domain} &nbsp;·&nbsp; GT: {gt_label}
    &nbsp;<a href="{item_id}/comparison.html"
             style="font-size:11px;font-weight:normal">comparison.html →</a>
  </summary>
  <table style="margin:8px 0;font-size:12px;border-collapse:collapse">
    <tr><th>condition</th><th>v9 final</th><th>Δ vs none</th>
        <th>tools used</th><th>denied</th><th>verdict</th></tr>
    {score_rows}
  </table>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:10px;margin-top:8px">
    {cond_cards}
  </div>
</details>"""

    html = f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<title>Tool-influence ablation — index</title>
<style>
body{{font-family:system-ui,'Segoe UI',sans-serif;margin:24px;background:#f8f8f5;color:#222}}
h2{{font-size:17px;margin:0 0 10px}}
table{{border-collapse:collapse;font-size:12px;background:#fff}}
th,td{{border:1px solid #ddd;padding:4px 8px;text-align:left}}
th{{background:#f0efe9}}
a{{color:#2563eb;text-decoration:none}}
details>summary{{list-style:none}}
details>summary::-webkit-details-marker{{display:none}}
details[open]>summary{{margin-bottom:8px}}
{_SHARED_CSS}
</style></head><body>
<h2>Tool-influence ablation — overview (v9 final score per condition)</h2>
<table>
<tr><th>item</th><th>domain</th><th>GT</th>{head_cells}</tr>
{overview_rows}
</table>
<p style="font-size:12px;color:#666;margin:10px 0 4px">
  点击下方条目展开逐 condition 详情与 turn-by-turn 对话记录（含 ablation gate 信息）。
</p>
{item_sections}
</body></html>"""
    (outdir / "index.html").write_text(html, encoding="utf-8")


# ─── main ────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--item_ids", nargs="+", default=["D1_0146", "D1_0103", "D1_0105"])
    ap.add_argument("--manifest",
                    default="benchmark/manifests_v2/D1_industrial_manifest.json")
    ap.add_argument("--outdir", default="top3_tool_testing/")
    ap.add_argument("--max_turns", type=int, default=4)
    ap.add_argument("--backend", default="qwen3",
                    choices=["qwen3", "gpt", "seedvl"])
    ap.add_argument("--conditions", nargs="+", default=list(CONDITIONS.keys()),
                    choices=list(CONDITIONS.keys()))
    # ap.add_argument("--conditions", nargs="+", default=["all_three"],
    #                     choices=list(CONDITIONS.keys()))
    ap.add_argument("--no-thinking", action="store_true",
                    help="disable thinking capture (match benchmark call_llm)")
    args = ap.parse_args()

    manifest = Path(args.manifest)
    if not manifest.is_absolute():
        manifest = REPO_ROOT / manifest
    outdir = Path(args.outdir)
    if not outdir.is_absolute():
        outdir = REPO_ROOT / outdir
    outdir.mkdir(parents=True, exist_ok=True)

    if args.backend == "qwen3" and not (os.environ.get("QWEN_API_KEY")):
        print("ERROR: qwen3 backend needs QWEN_API_KEY "
              "(dashscope compatible-mode). Optionally set QWEN_API_BASE / "
              "QWEN_MODEL.", file=sys.stderr)
        sys.exit(2)

    client = get_client(args.backend)
    model = get_model_name(args.backend)
    conds = {c: CONDITIONS[c] for c in args.conditions}

    print(f"backend={args.backend} model={model} "
          f"base_url={getattr(client, 'base_url', '?')}")
    print(f"items={args.item_ids}  conditions={list(conds)}  "
          f"max_turns={args.max_turns}  thinking={'off' if args.no_thinking else 'on'}")
    n_est = len(args.item_ids) * len(conds)
    print(f"~{n_est} agent runs (~{n_est} x {args.max_turns + 1} VLM calls "
          f"+ 1 direct per item) -> {outdir}")

    items = _load_items(manifest, args.item_ids)
    all_summaries = []
    for item in items:
        results = run_item(client, model, item, outdir, args.max_turns,
                           thinking=not args.no_thinking, conditions=conds)
        summary = build_summary(item, results)
        all_summaries.append(summary)
        (outdir / item["item_id"]).mkdir(parents=True, exist_ok=True)
        (outdir / item["item_id"] / "summary_item.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        render_item_html(item, summary, results,
                         outdir / item["item_id"] / "comparison.html")
        print(f"  -> {outdir / item['item_id'] / 'comparison.html'}")

    (outdir / "summary.json").write_text(
        json.dumps(all_summaries, ensure_ascii=False, indent=2), encoding="utf-8")
    render_index(outdir, all_summaries)
    print(f"\nsummary -> {outdir / 'summary.json'}")
    print(f"index   -> {outdir / 'index.html'}")


if __name__ == "__main__":
    main()
