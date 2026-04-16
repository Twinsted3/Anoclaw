import os
import json
import asyncio
from random import shuffle
import cv2
import re
import argparse
from tqdm import tqdm
from difflib import get_close_matches
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
from utils import load_visual_ctx, find_last_json

# 限制输入图像的最大长边，避免超大分辨率带来的显存/内存压力
MAX_IMAGE_DIM = 512


def _resize_if_needed(frame_rgb, max_dim=MAX_IMAGE_DIM):
    """
    如长边超过 max_dim，则按比例缩放到长边为 max_dim。
    """
    h, w = frame_rgb.shape[:2]
    long_side = max(h, w)
    if long_side <= max_dim:
        return frame_rgb
    scale = max_dim / long_side
    new_w = int(w * scale)
    new_h = int(h * scale)
    return cv2.resize(frame_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)


def extract_frames_from_image(image_path):
    """
    从单张图片文件路径加载图片，返回RGB格式的帧列表，并在必要时限制分辨率
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片文件不存在: {image_path}")
    
    # 使用cv2读取图片
    frame_bgr = cv2.imread(image_path)
    if frame_bgr is None:
        raise ValueError(f"无法读取图片: {image_path}")
    
    # 转换为RGB格式
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    frame_rgb = _resize_if_needed(frame_rgb)
    
    # 返回单帧列表（保持与extract_frames_forensics相同的格式）
    return [frame_rgb]


def merge_session_input(history_items, new_input_items):
    """与inference.py中相同的session输入合并函数"""
    if isinstance(new_input_items, list):
        return history_items + new_input_items
    else:
        return history_items + [{"role": "user", "content": new_input_items}]


def parse_conversation(text_gt):
    """
    解析text_gt中的conversation字段，提取问题和答案
    参考gpt4o.py中的parse_conversation方法
    """
    Question = []
    Answer = []
    # Keywords to match
    keyword = "conversation"

    # Iterate through all keys in the dictionary
    for key in text_gt.keys():
        # If the key starts with the keyword
        if key.startswith(keyword):
            # Get the corresponding value
            conversation = text_gt[key]
            for i, QA in enumerate(conversation):
                options_items = list(QA['Options'].items())
                options_text = ""
                for j, (key, value) in enumerate(options_items):
                    options_text += f"{key}. {value}\n"
                questions_text = QA['Question']
                Question.append({
                    "question_text": questions_text,
                    "options": QA['Options'],
                    "options_text": options_text,
                    "type": QA.get('type', 'Unknown')
                })
                Answer.append(QA['Answer'])

            break
    return Question, Answer


def extract_summary_from_skeptic_result(skeptic_result):
    """
    从Skeptic_agent的结果中提取总结文本（只提取一次，所有问题共用）
    
    Args:
        skeptic_result: Skeptic_agent.run()返回的结果列表
    
    Returns:
        summary_text: 总结文本
    """
    # 尝试提取最终的 assistant completed message 作为主要总结
    final_message_text = ""
    if isinstance(skeptic_result, list):
        for item in reversed(skeptic_result):
            if isinstance(item, dict) and item.get("role") == "assistant" and item.get("status") == "completed":
                content = item.get("content", [])
                texts = []
                if isinstance(content, list):
                    for c in content:
                        if isinstance(c, dict) and "text" in c:
                            texts.append(c.get("text", ""))
                elif isinstance(content, str):
                    texts.append(content)
                final_message_text = "\n".join([t for t in texts if t]).strip()
                if final_message_text:
                    break
    
    # 将整个推理过程转换为文本（用于兜底）
    reasoning_text = ""
    if isinstance(skeptic_result, list):
        for item in skeptic_result:
            if isinstance(item, dict):
                if item.get("type") == "message":
                    content = item.get("content", "")
                    if isinstance(content, list) and len(content) > 0:
                        if isinstance(content[0], dict):
                            reasoning_text += content[0].get("text", "") + "\n"
                        else:
                            reasoning_text += str(content[0]) + "\n"
                    elif isinstance(content, str):
                        reasoning_text += content + "\n"
                elif item.get("type") == "function_call_output":
                    reasoning_text += str(item.get("output", "")) + "\n"
                elif "role" in item and "content" in item:
                    reasoning_text += str(item.get("content", "")) + "\n"
            elif isinstance(item, str):
                reasoning_text += item + "\n"
    elif isinstance(skeptic_result, str):
        reasoning_text = skeptic_result
    reasoning_text_limited = reasoning_text[-2000:] if len(reasoning_text) > 2000 else reasoning_text

    summary = final_message_text if final_message_text else reasoning_text_limited
    return summary


def extract_answer_from_skeptic_result(skeptic_result, question_info, client, model_name, summary_text=None):
    """
    从Skeptic_agent的结果中提取答案
    
    Args:
        skeptic_result: Skeptic_agent.run()返回的结果列表
        question_info: 包含问题和选项的字典
        client: OpenAI客户端（用于额外的答案提取）
        model_name: 模型名称
        summary_text: 可选的总结文本（如果提供则复用，否则从skeptic_result中提取）
    
    Returns:
        answer_letter: 答案字母
    """
    # 如果没有提供summary_text，则提取一次
    if summary_text is None:
        summary_text = extract_summary_from_skeptic_result(skeptic_result)

    # 使用LLM从推理结果中提取答案
    prompt = f"""你是一个答案提取助手。你需要根据推理过程和问题选项，选择最匹配的答案。

            推理过程：
            {summary_text}

            问题：{question_info['question_text']}

            选项：
            {question_info['options_text']}

            请根据推理过程，选择最匹配的选项字母（A/B/C/D/E）。只返回字母，不要其他内容。
            """
    
    try:
        # 使用同步调用（因为这是在同步函数中）
        from openai import OpenAI
        sync_client = OpenAI(
            base_url=client.base_url,
            api_key=client.api_key
        )
        
        response = sync_client.chat.completions.create(
            model=model_name,
            messages=[
                # {"role": "system", "content": "你是一个答案提取助手，只返回选项字母。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10,
            temperature=0
        )
        
        answer_text = response.choices[0].message.content.strip()
        
        # 使用正则表达式提取字母
        pattern = re.compile(r'\b([A-E])\b')
        answers = pattern.findall(answer_text)
        
        if answers:
            return answers[-1]  # 返回最后一个匹配的字母
        
        # 如果正则匹配失败，尝试模糊匹配
        options_values = list(question_info['options'].values())
        closest_matches = get_close_matches(answer_text, options_values, n=1, cutoff=0.0)
        if closest_matches:
            closest_match = closest_matches[0]
            for key, value in question_info['options'].items():
                if value == closest_match:
                    return key
        
        # 如果都失败，返回空字符串
        return ''
        
    except Exception as e:
        print(f"提取答案时出错: {e}")
        return ''


def run_skeptic_on_image(image_path, text_gt, run_config, client, model_name, idx=0, 
                         few_shot_paths=None, data_path=""):
    """
    对单张图片运行Skeptic_agent流程
    
    Args:
        image_path: 图片文件路径
        text_gt: 包含问题和答案的字典
        run_config: RunConfig对象
        client: OpenAI客户端
        model_name: 模型名称
        idx: 测试序号
        few_shot_paths: few-shot参考图片路径列表（相对于data_path）
        data_path: 数据集根路径
    
    Returns:
        (questions, answers, skeptic_answers) 元组
    """
    try:
        # 1. 解析问题和答案
        questions, answers = parse_conversation(text_gt)
        if questions == [] or answers == []:
            return questions, answers, None, None, 0
        
        # 2. 初始化session和skeptic agent
        session = SQLiteSession(f"mmad_user_{idx}")
        skeptic_agent = Skeptic_agent(session, run_config, depth_quota=3)
        
        # 3. 提取查询图片帧
        rgb_frames = extract_frames_from_image(image_path)
        
        # 4. 加载few-shot参考图片（如果有）
        few_shot_frames = []
        if few_shot_paths:
            for few_shot_path in few_shot_paths:
                rel_few_shot_path = os.path.join(data_path, few_shot_path)
                if os.path.exists(rel_few_shot_path):
                    few_shot_rgb = extract_frames_from_image(rel_few_shot_path)
                    few_shot_frames.extend(few_shot_rgb)
                else:
                    print(f"⚠️ Few-shot图片不存在: {rel_few_shot_path}")
        
        # 5. 加载视觉上下文（包含few-shot图片）
        visual_ctx = load_visual_ctx(rgb_frames, few_shot_frames=few_shot_frames if few_shot_frames else None)
        
        # 6. 运行agent（对所有问题使用同一个推理结果）
        result, chat_length = skeptic_agent.run(visual_ctx)
        
        # 7. 先提取一次总结文本（所有问题共用）
        summary_text = extract_summary_from_skeptic_result(result)
        
        # 8. 从结果中提取每个问题的答案（复用同一个summary_text）
        skeptic_answers = []
        skeptic_summaries = []
        for question_info in questions:
            answer_letter = extract_answer_from_skeptic_result(
                result, question_info, client, model_name, summary_text=summary_text
            )
            skeptic_answers.append(answer_letter)
            skeptic_summaries.append(summary_text)  # 所有问题使用相同的summary_text
        
        return questions, answers, skeptic_answers, skeptic_summaries, result, chat_length
        
    except Exception as e:
        print(f"\n❌ 处理图片 {image_path} 时出错: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None, None, 0


def main():
    """
    主函数：运行MMAD测评
    """
    parser = argparse.ArgumentParser(description="使用Skeptic_agent进行MMAD测评")
    parser.add_argument("--data_path", type=str, default="MMAD/dataset/MMAD", 
                       help="MMAD数据集路径")
    parser.add_argument("--json_path", type=str, default="MMAD/dataset/MMAD/mmad.json",
                       help="mmad.json文件路径")
    parser.add_argument("--output_dir", type=str, default="./result",
                       help="结果输出目录")
    # parser.add_argument("--model", type=str, default="doubao-seed-1-6-vision-250815",
    parser.add_argument("--model", type=str, default="doubao-seed-1-6-251015",
                       help="模型名称")
    parser.add_argument("--max_samples", type=int, default=None,
                       help="最大处理样本数（用于测试）")
    parser.add_argument("--start_idx", type=int, default=0,
                       help="起始样本索引")
    parser.add_argument("--few_shot", type=int, default=1,
                       help="Few-shot数量（0表示不使用few-shot）")
    parser.add_argument("--similar_template", action="store_true",
                       help="使用similar_templates而不是random_templates")
    
    args = parser.parse_args()
    
    print("="*60)
    print("Skeptic_agent MMAD 测评脚本")
    print("="*60)
    
    # 显示few-shot配置
    if args.few_shot > 0:
        template_type = "similar_templates" if args.similar_template else "random_templates"
        print(f"Few-shot模式: {args.few_shot} shot ({template_type})")
    else:
        print("Few-shot模式: 关闭")
    
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)
    run_log_dir = os.path.join(args.output_dir, "skeptic_runs")
    os.makedirs(run_log_dir, exist_ok=True)
    
    # 结果文件路径（包含few-shot信息）
    model_name_safe = args.model.replace("/", "_")
    few_shot_suffix = ""
    if args.few_shot > 0:
        template_type = "similar" if args.similar_template else "random"
        few_shot_suffix = f"_{args.few_shot}shot_{template_type}"
    answers_json_path = os.path.join(args.output_dir, f"answers_skeptic_{model_name_safe}{few_shot_suffix}.json")
    
    # 加载已有结果
    if os.path.exists(answers_json_path):
        with open(answers_json_path, "r", encoding="utf-8") as file:
            all_answers_json = json.load(file)
        try:
            #（如果helper模块可用）计算准确率
            import sys
            sys.path.append("MMAD/evaluation/examples")
            from helper.summary import caculate_accuracy_mmad
            caculate_accuracy_mmad(answers_json_path)
        except Exception as e:
            print(f"计算准确率时出错: {e}")
    else:
        all_answers_json = []
    
    existing_images = [a["image"] for a in all_answers_json]
    
    # 加载MMAD数据集
    print(f"\n加载MMAD数据集: {args.json_path}")
    if not os.path.exists(args.json_path):
        print(f"❌ 文件不存在: {args.json_path}")
        return
    
    with open(args.json_path, "r", encoding="utf-8") as file:
        chat_ad = json.load(file)
    
    print(f"数据集包含 {len(chat_ad)} 张图片")
    
    # 初始化配置
    int_MODEL = args.model
    run_config = RunConfig(
        session_input_callback=merge_session_input,
        trace_include_sensitive_data=True,
        model=int_MODEL
    )
    
    # 获取OpenAI客户端（从环境变量中获取）
    client = AsyncOpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=os.environ.get("OPENAI_API_KEY", ""),
    )
    
    # 处理每张图片
    processed_count = 0
    skipped_count = 0
    
    # 获取所有图片路径并排序（保证可重复性）
    image_paths = sorted(chat_ad.keys())
    #shuffle
    image_paths = shuffle(image_paths)
    # 应用起始索引
    if args.start_idx > 0:
        image_paths = image_paths[args.start_idx:]
        print(f"从索引 {args.start_idx} 开始处理")
    
    # 应用最大样本数限制
    if args.max_samples:
        image_paths = image_paths[:args.max_samples]
        print(f"限制处理 {args.max_samples} 个样本")
    
    for data_id, image_path in enumerate(tqdm(image_paths, desc="处理图片")):
        # 跳过已处理的图片
        if image_path in existing_images:
            skipped_count += 1
            continue
        
        text_gt = chat_ad[image_path]
        
        # 构建完整图片路径
        rel_image_path = os.path.join(args.data_path, image_path)
        
        if not os.path.exists(rel_image_path):
            print(f"\n⚠️ 图片文件不存在: {rel_image_path}")
            continue
        
        # 获取few-shot图片路径
        few_shot_paths = []
        if args.few_shot > 0:
            if args.similar_template:
                few_shot_paths = text_gt.get("similar_templates", [])[:args.few_shot]
            else:
                few_shot_paths = text_gt.get("random_templates", [])[:args.few_shot]
        
        # 运行Skeptic_agent
        questions, answers, skeptic_answers, skeptic_summaries, skeptic_result, chat_length = run_skeptic_on_image(
            rel_image_path, text_gt, run_config, client, int_MODEL, data_id,
            few_shot_paths=few_shot_paths, data_path=args.data_path
        )
        
        if skeptic_answers is None or len(skeptic_answers) != len(answers):
            print(f"\n⚠️ 处理失败或答案数量不匹配: {image_path}")
            continue
        # 记录完整result
        log_filename = image_path.replace("/", "__")
        log_path = os.path.join(run_log_dir, f"{log_filename}.json")
        log_payload = {
            "image": image_path,
            "few_shot_paths": few_shot_paths,
            "chat_length": chat_length,
            "result": skeptic_result
        }
        with open(log_path, "w", encoding="utf-8") as log_file:
            json.dump(log_payload, log_file, indent=4, ensure_ascii=False)
        
        # 计算准确率
        correct = 0
        for i, answer in enumerate(answers):
            if skeptic_answers[i] == answer:
                correct += 1
        accuracy = correct / len(answers) if len(answers) > 0 else 0
        
        if data_id % 10 == 0:  # 每10张图片打印一次
            print(f"\n[进度] 图片 {data_id+1}/{len(image_paths)}, 准确率: {accuracy:.2f}")
        
        # 获取问题类型
        questions_type = [q.get('type', 'Unknown') for q in questions]
        
        # 保存答案记录
        for idx, (q, a, ga, gs, qt) in enumerate(zip(questions, answers, skeptic_answers, skeptic_summaries, questions_type)):
            question_full_text = f"{q['question_text']}\n{q['options_text']}"
            answer_entry = {
                "image": image_path,
                "question": question_full_text,
                # "question_text": q['question_text'],
                # "options_text": q['options_text'],
                # "options": q.get('options', {}),
                "question_type": qt,
                "correct_answer": a,
                "gpt_answer": ga
            }
            # 只给第一个问题保存gpt_summary
            if idx == 0:
                answer_entry["gpt_summary"] = gs
            all_answers_json.append(answer_entry)
        
        # 定期保存（每处理10张图片）
        if (data_id) % 10 == 0:
            with open(answers_json_path, "w", encoding="utf-8") as file:
                json.dump(all_answers_json, file, indent=4, ensure_ascii=False)
        
        processed_count += 1
    
    # 最终保存
    with open(answers_json_path, "w", encoding="utf-8") as file:
        json.dump(all_answers_json, file, indent=4, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("测评完成")
    print(f"{'='*60}")
    print(f"总共处理: {processed_count} 张图片")
    print(f"跳过: {skipped_count} 张图片（已处理）")
    print(f"结果保存在: {answers_json_path}")
    
    # 计算准确率（如果helper模块可用）
    try:
        import sys
        sys.path.append("MMAD/evaluation/examples")
        from helper.summary import caculate_accuracy_mmad  # type: ignore
        print(f"\n计算详细准确率...")
        caculate_accuracy_mmad(answers_json_path)
    except Exception as e:
        print(f"\n⚠️ 无法计算详细准确率: {e}")
        print("请手动运行 helper.summary.caculate_accuracy_mmad()")


if __name__ == "__main__":
    # 设置环境变量和客户端
    os.environ["OPENAI_API_KEY"] = "***REDACTED-SEED-KEY***"
    
    # 1. 切换 API 模式为标准对话模式
    set_default_openai_api("chat_completions")

    # 2. 创建火山引擎的异步客户端
    volcano_client = AsyncOpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=os.environ["OPENAI_API_KEY"],
    )

    # 3. 关闭 agents 内置的 tracing
    set_tracing_disabled(True)

    # 4. 将其注入为 SDK 的默认客户端
    set_default_openai_client(volcano_client)
    
    main()

