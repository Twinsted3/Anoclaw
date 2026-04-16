import os
import json
import asyncio
import cv2
import numpy as np
from pprint import pprint as pp

from agents import (
    SQLiteSession,
    RunConfig,
    set_default_openai_client,
    set_default_openai_api,
    set_tracing_disabled,
)
from openai import AsyncOpenAI
from multi_round_skeptic import Skeptic_agent
from utils import load_visual_ctx


def extract_frames_from_image(image_path):
    """
    从单张图片文件路径加载图片，返回RGB格式的帧列表
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片文件不存在: {image_path}")
    
    # 使用cv2读取图片
    frame_bgr = cv2.imread(image_path)
    if frame_bgr is None:
        raise ValueError(f"无法读取图片: {image_path}")
    
    # 转换为RGB格式
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    
    # 返回单帧列表（保持与extract_frames_forensics相同的格式）
    return [frame_rgb]


def merge_session_input(history_items, new_input_items):
    """与inference.py中相同的session输入合并函数"""
    if isinstance(new_input_items, list):
        return history_items + new_input_items
    else:
        return history_items + [{"role": "user", "content": new_input_items}]


def print_chat_history(session, title="聊天历史"):
    """打印session中的聊天历史，便于调试"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    try:
        # 尝试获取session的历史记录
        # 注意：这取决于agents库的实现，可能需要调整
        if hasattr(session, 'get_messages'):
            messages = session.get_messages()
            for i, msg in enumerate(messages):
                print(f"\n[消息 {i+1}]")
                pp(msg)
        else:
            print("无法直接访问session历史，请查看agents库的文档")
    except Exception as e:
        print(f"获取聊天历史时出错: {e}")


def run_test_single_image(image_path, output_dir="./test_output", idx=0):
    """
    对单张图片运行Skeptic_agent流程
    
    Args:
        image_path: 图片文件路径
        output_dir: 输出目录
        idx: 测试序号
    """
    print(f"\n{'#'*60}")
    print(f"开始处理图片 {idx+1}: {image_path}")
    print(f"{'#'*60}")
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 1. 初始化session和skeptic agent
        print("\n[步骤1] 初始化session和agent...")
        session = SQLiteSession(f"test_user_{idx}")
        int_MODEL = "doubao-seed-1-6-vision-250815"  # 与inference.py中相同
        run_config = RunConfig(
            session_input_callback=merge_session_input,
            trace_include_sensitive_data=True,
            model=int_MODEL
        )
        skeptic_agent = Skeptic_agent(session, run_config, depth_quota=3)
        print(f"✓ Session和Agent初始化完成 (模型: {int_MODEL})")
        
        # 2. 提取图片帧
        print(f"\n[步骤2] 从图片文件提取帧...")
        rgb_frames = extract_frames_from_image(image_path)
        print(f"✓ 成功提取 {len(rgb_frames)} 帧")
        print(f"  图片尺寸: {rgb_frames[0].shape if rgb_frames else 'N/A'}")
        
        # 3. 加载视觉上下文
        print(f"\n[步骤3] 加载视觉上下文...")
        visual_ctx = load_visual_ctx(rgb_frames)
        print(f"✓ VisualContext创建完成")
        
        # 4. 运行agent
        print(f"\n[步骤4] 运行Skeptic_agent...")
        print(f"  最大轮数: {skeptic_agent.depth_quota}")
        print(f"  开始推理...")
        
        result, chat_length = skeptic_agent.run(visual_ctx)
        
        print(f"\n✓ Agent运行完成!")
        print(f"  实际轮数: {chat_length}")
        print(f"  结果类型: {type(result)}")
        print(f"  结果长度: {len(result) if isinstance(result, list) else 'N/A'}")
        
        # 5. 打印部分结果（便于调试）
        print(f"\n[步骤5] 结果预览...")
        if isinstance(result, list):
            print(f"  前3条消息:")
            for i, item in enumerate(result[:3]):
                print(f"    [{i+1}] {type(item).__name__}: {str(item)[:100]}...")
        else:
            print(f"  结果: {str(result)[:200]}...")
        
        # 6. 保存输出
        print(f"\n[步骤6] 保存结果到文件...")
        output = {
            "result": result,
            "rounds": chat_length,
            "image_path": image_path,
            "meta_data": {
                "test_idx": idx,
                "image_path": image_path
            }
        }
        
        output_file = os.path.join(output_dir, f"test_{idx}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4, ensure_ascii=False)
        print(f"✓ 结果已保存到: {output_file}")
        
        # 7. 尝试打印聊天历史（如果可能）
        print(f"\n[步骤7] 尝试获取聊天历史...")
        print_chat_history(session, f"图片 {idx+1} 的聊天历史")
        
        return output
        
    except Exception as e:
        print(f"\n❌ 处理图片时出错: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """
    主函数：运行测试
    """
    print("="*60)
    print("Skeptic_agent 测试和调试脚本")
    print("="*60)
    
    # ========== 配置区域 ==========
    # 在这里添加你的测试图片路径
    test_images = [
        # 示例：添加你的图片路径
        "MMAD/dataset/MMAD/DS-MVTec/bottle/image/broken_small/000.png",
        # "/path/to/your/test_image2.png",
        # "/path/to/your/test_image3.jpg",
    ]
    
    # 如果test_images为空，尝试从当前目录查找图片
    if len(test_images) == 0:
        print("\n未指定测试图片，尝试从当前目录查找...")
        current_dir = os.getcwd()
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        for file in os.listdir(current_dir):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                full_path = os.path.join(current_dir, file)
                test_images.append(full_path)
                print(f"  找到图片: {full_path}")
    
    if len(test_images) == 0:
        print("\n❌ 未找到任何测试图片!")
        print("请使用以下方式之一:")
        print("1. 在main()函数中的test_images列表中添加图片路径")
        print("2. 将图片放在当前工作目录中")
        return
    
    print(f"\n找到 {len(test_images)} 张测试图片")
    
    # 输出目录
    output_dir = "./test_output"
    os.makedirs(output_dir, exist_ok=True)
    print(f"输出目录: {output_dir}")
    
    # ========== 运行测试 ==========
    results = []
    for idx, image_path in enumerate(test_images):
        result = run_test_single_image(image_path, output_dir, idx)
        if result:
            results.append(result)
    
    # ========== 总结 ==========
    print(f"\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")
    print(f"总共处理: {len(test_images)} 张图片")
    print(f"成功处理: {len(results)} 张图片")
    print(f"失败: {len(test_images) - len(results)} 张图片")
    
    if results:
        print(f"\n结果文件保存在: {output_dir}")
        avg_rounds = sum(r['rounds'] for r in results) / len(results)
        print(f"平均轮数: {avg_rounds:.2f}")


if __name__ == "__main__":
    # os.environ["OPENAI_API_BASE"] = "https://ark.cn-beijing.volces.com/api/v3"
    os.environ["OPENAI_API_KEY"] = "***REDACTED-SEED-KEY***"
    # 1. 切换 API 模式为标准对话模式 (否则会默认调用火山引擎不支持的 Responses API)
    set_default_openai_api("chat_completions")

    # 2. 创建火山引擎的异步客户端
    volcano_client = AsyncOpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=os.environ["OPENAI_API_KEY"],  # 确保环境变量已设置
    )

    # 2.1 简单测试：调用一次 chat.completions 检查客户端是否可用
    async def _test_volcano_client():
        try:
            resp = await volcano_client.chat.completions.create(
                model="doubao-seed-1-6-vision-250815",  # 请确认此模型在你的账号下可用
                messages=[{"role": "user", "content": "你好，只需回复“OK”两个字。"}],
                max_tokens=10,
            )
            print("\n[火山异步客户端连通性测试] 调用成功")
            try:
                content = resp.choices[0].message.content
            except Exception:
                content = resp
            print("返回内容:", str(content)[:200])
        except Exception as e:
            print("\n[火山异步客户端连通性测试] 调用失败")
            print("错误信息:", e)

    asyncio.run(_test_volcano_client())

    # 3. 关闭 agents 内置的 tracing，上报到 OpenAI 的网络在当前环境不可用
    set_tracing_disabled(True)

    # 4. 将其注入为 SDK 的默认客户端
    set_default_openai_client(volcano_client)
    main()

