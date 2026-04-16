import os
from typing import Optional

from agents import (
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)
from openai import AsyncOpenAI


def init_agents_sdk(
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    disable_tracing: bool = True,
) -> None:
    """
    初始化 Agents SDK 的默认 OpenAI 客户端（支持火山方舟等 OpenAI-compatible 网关）。

    环境变量约定：
    - OPENAI_API_KEY
    - OPENAI_API_BASE (可选)
    """
    if api_key is None:
        api_key = os.environ.get("OPENAI_API_KEY")
    if base_url is None:
        base_url = os.environ.get("OPENAI_API_BASE")

    if not api_key:
        raise EnvironmentError(
            "未设置 OPENAI_API_KEY。请先 export OPENAI_API_KEY=...，或调用 init_agents_sdk(api_key=...)."
        )

    # 关键：在部分网关/兼容实现下，需要切到 chat_completions
    set_default_openai_api("chat_completions")

    client = AsyncOpenAI(
        base_url=base_url,
        api_key=api_key,
    )
    set_default_openai_client(client)

    if disable_tracing:
        set_tracing_disabled(True)


