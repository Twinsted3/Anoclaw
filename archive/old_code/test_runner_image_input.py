import asyncio
import base64
import os

from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    RunConfig,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)


def image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


async def main():
    # 1) 初始化 Agents SDK：使用 chat_completions + 方舟 OpenAI-compatible 网关
    #    （你们仓库 test_debug.py 就是这么配的）
    set_default_openai_api("chat_completions")
    set_tracing_disabled(True)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("未设置 OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_API_BASE", "https://ark.cn-beijing.volces.com/api/v3")

    volcano_client = AsyncOpenAI(base_url=base_url, api_key=api_key)
    set_default_openai_client(volcano_client)

    # 2) 配置模型（关键：否则 SDK 默认模型可能是 gpt-4.1，在方舟会 404）
    model = os.environ.get("VAD2_MODEL", "doubao-seed-1-6-vision-250815")
    run_config = RunConfig(model=model, trace_include_sensitive_data=False)

    # 3) 测试图片
    filepath = os.environ.get(
        "TEST_IMAGE",
        os.path.join(
            os.path.dirname(__file__),
            "MMAD/dataset/MMAD/DS-MVTec/bottle/image/good/000.png",
        ),
    )
    b64_image = image_to_base64(filepath)

    agent = Agent(name="Assistant", instructions="You are a helpful assistant.")

    # 4) 注意：这里用的是 Agents SDK 识别的 schema：type=input_image（而不是 image_url）
    result = await Runner.run(
        agent,
        [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "detail": "auto",
                        "image_url": f"data:image/png;base64,{b64_image}",
                    }
                ],
            },
            {"role": "user", "content": "What do you see in this image?"},
        ],
        run_config=run_config,
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())


