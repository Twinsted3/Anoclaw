import json
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI

from agents import function_tool, RunContextWrapper

from utils import VisualContext, encode_image
from vad2_prompts import (
    PROPOSER_SYSTEM,
    REFUTER_SYSTEM,
    PROPOSER_COLD,
    refuter_prompt,
    proposer_iterative,
)


def _get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("未设置 OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_API_BASE") or None
    return OpenAI(base_url=base_url, api_key=api_key)


def _vision_messages_for_ctx(
    visual_ctx: VisualContext,
    *,
    prompt_text: str,
    system_text: str,
    max_query_frames: int = 1,
    max_normal_frames: int = 1,
) -> List[Dict[str, Any]]:
    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_text}]

    normal_frames = visual_ctx.few_shot_frames or []
    for i, f in enumerate(normal_frames[:max_normal_frames]):
        b64 = encode_image(f)
        messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    {"type": "text", "text": f"Normal sample {i+1}"},
                ],
            }
        )

    query_frames = visual_ctx.full_frames or []
    for i, f in enumerate(query_frames[:max_query_frames]):
        b64 = encode_image(f)
        messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    {"type": "text", "text": f"Query image {i+1}"},
                ],
            }
        )

    messages.append({"role": "user", "content": prompt_text})
    return messages


def propose_anomalies_mm(
    visual_ctx: VisualContext,
    *,
    model: str,
    temperature: float = 0.0,
    max_tokens: int = 600,
    max_query_frames: int = 1,
    max_normal_frames: int = 1,
    tbd_claims_json: Optional[str] = None,
) -> str:
    """
    直接调用多模态模型，输出严格 JSON 字符串：{"claims":[...]}。
    """
    client = _get_client()
    prompt = PROPOSER_COLD if not tbd_claims_json else proposer_iterative(tbd_claims_json)
    msgs = _vision_messages_for_ctx(
        visual_ctx,
        prompt_text=prompt,
        system_text=PROPOSER_SYSTEM,
        max_query_frames=max_query_frames,
        max_normal_frames=max_normal_frames,
    )
    resp = client.chat.completions.create(
        model=model,
        messages=msgs,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""


def refute_anomalies_mm(
    visual_ctx: VisualContext,
    *,
    model: str,
    claims_json: str,
    temperature: float = 0.0,
    max_tokens: int = 600,
    max_query_frames: int = 1,
    max_normal_frames: int = 1,
) -> str:
    """
    直接调用多模态模型，输出严格 JSON 字符串：{"reviews":[...]}。
    """
    client = _get_client()
    prompt = refuter_prompt(claims_json)
    msgs = _vision_messages_for_ctx(
        visual_ctx,
        prompt_text=prompt,
        system_text=REFUTER_SYSTEM,
        max_query_frames=max_query_frames,
        max_normal_frames=max_normal_frames,
    )
    resp = client.chat.completions.create(
        model=model,
        messages=msgs,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""


# ---------- Agents SDK tool wrappers（可选） ----------
# 注意：如果用 Agent 调这些 tool，会额外产生“Agent 决策一次 + tool 内再调用一次” => API 次数上升。
# 我们的新 orchestrator 会直接调用 propose_anomalies_mm / refute_anomalies_mm 来保持每轮 2 次。


@function_tool
def vad2_propose_tool(
    visual_ctx: RunContextWrapper[VisualContext],
    model: str,
    temperature: float = 0.0,
    max_tokens: int = 600,
    max_query_frames: int = 1,
    max_normal_frames: int = 1,
) -> str:
    return propose_anomalies_mm(
        visual_ctx.context,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        max_query_frames=max_query_frames,
        max_normal_frames=max_normal_frames,
    )


@function_tool
def vad2_refute_tool(
    visual_ctx: RunContextWrapper[VisualContext],
    claims_json: str,
    model: str,
    temperature: float = 0.0,
    max_tokens: int = 600,
    max_query_frames: int = 1,
    max_normal_frames: int = 1,
) -> str:
    return refute_anomalies_mm(
        visual_ctx.context,
        claims_json=claims_json,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        max_query_frames=max_query_frames,
        max_normal_frames=max_normal_frames,
    )


