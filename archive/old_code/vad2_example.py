import os
import json
import cv2

from utils import load_visual_ctx
from vad2_system import DualVADAgentSystem, DualVADConfig


def _load_single_image_rgb(image_path: str):
    if not os.path.exists(image_path):
        raise FileNotFoundError(image_path)
    bgr = cv2.imread(image_path)
    if bgr is None:
        raise ValueError(f"无法读取图片: {image_path}")
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def main():
    """
    用法示例（单张 query 图 + 可选单张 normal 图）：
    export OPENAI_API_KEY=...
    export OPENAI_API_BASE=https://ark.cn-beijing.volces.com/api/v3
    python vad2_example.py
    """
    query_path = "MMAD/dataset/MMAD/DS-MVTec/bottle/image/broken_small/000.png"
    normal_path = "MMAD/dataset/MMAD/DS-MVTec/bottle/image/good/000.png"  # 可填入一张正常样本路径（建议同类同视角）

    query_rgb = _load_single_image_rgb(query_path)
    few_shot = [_load_single_image_rgb(normal_path)] if normal_path else None
    visual_ctx = load_visual_ctx([query_rgb], few_shot_frames=few_shot)

    cfg = DualVADConfig(
        model=os.environ.get("VAD2_MODEL", "doubao-seed-1-6-vision-250815"),
        depth_quota=int(os.environ.get("VAD2_ROUNDS", "2")),
        max_query_frames=1,
        max_normal_frames=1,
        max_tokens=int(os.environ.get("VAD2_MAX_TOKENS", "600")),
    )
    system = DualVADAgentSystem(config=cfg)
    report = system.run(visual_ctx)

    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    with open("./test_output/vad2_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("已保存：./test_output/vad2_report.json")


if __name__ == "__main__":
    from agents import set_default_openai_api, set_default_openai_client, set_tracing_disabled
    from openai import AsyncOpenAI
    # configure volcano/ark client for agents
    set_default_openai_api('chat_completions')
    set_tracing_disabled(True)
    client = AsyncOpenAI(
        base_url=os.environ.get('OPENAI_API_BASE','https://ark.cn-beijing.volces.com/api/v3'),
        api_key=os.environ.get('OPENAI_API_KEY','***REDACTED-SEED-KEY***'),
    )
    set_default_openai_client(client)
    os.makedirs("./test_output", exist_ok=True)
    main()


