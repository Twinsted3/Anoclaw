import argparse
import json
import os
import re
from typing import Dict, List, Tuple

import cv2
from tqdm import tqdm

from openai import AsyncOpenAI
from agents import (
    RunConfig,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)

from utils import load_visual_ctx
from vad2_system import DualVADAgentSystem, DualVADConfig


MAX_IMAGE_DIM = 512


def _resize_if_needed(frame_rgb, max_dim=MAX_IMAGE_DIM):
    h, w = frame_rgb.shape[:2]
    long_side = max(h, w)
    if long_side <= max_dim:
        return frame_rgb
    scale = max_dim / long_side
    new_w = int(w * scale)
    new_h = int(h * scale)
    return cv2.resize(frame_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)


def _load_image_rgb(image_path: str):
    frame_bgr = cv2.imread(image_path)
    if frame_bgr is None:
        raise ValueError(f"无法读取图片: {image_path}")
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    return _resize_if_needed(frame_rgb)


def parse_conversation(text_gt: Dict) -> Tuple[List[Dict], List[str], str]:
    """
    返回：
    - questions: [{"question_text","options","options_text","type"}...]
    - answers:   ["A","B",...]
    - questions_text: 拼接好的题目文本（含选项），用于塞进 agent prompt
    """
    questions = []
    answers = []
    keyword = "conversation"

    for key in text_gt.keys():
        if key.startswith(keyword):
            conversation = text_gt[key]
            for qa in conversation:
                options_items = list(qa["Options"].items())
                options_text = ""
                for opt_k, opt_v in options_items:
                    options_text += f"{opt_k}. {opt_v}\n"
                q_text = qa["Question"]
                questions.append(
                    {
                        "question_text": q_text,
                        "options": qa["Options"],
                        "options_text": options_text,
                        "type": qa.get("type", "Unknown"),
                    }
                )
                answers.append(qa["Answer"])
            break

    questions_text = ""
    for i, q in enumerate(questions, start=1):
        questions_text += f"{i}. Question: {q['question_text']}\n{q['options_text']}\n"

    return questions, answers, questions_text.strip()


def _normalize_answer_list(ans_list, expected_n: int) -> List[str]:
    if not isinstance(ans_list, list):
        return []
    out = []
    for x in ans_list:
        if not isinstance(x, str):
            continue
        m = re.search(r"\b([A-E])\b", x.upper())
        if m:
            out.append(m.group(1))
    if len(out) != expected_n:
        return []
    return out


def main():
    parser = argparse.ArgumentParser(description="使用 vad2 DualVADAgentSystem 进行 MMAD 测评")
    parser.add_argument("--data_path", type=str, default="MMAD/dataset/MMAD", help="MMAD 数据集根目录")
    parser.add_argument("--json_path", type=str, default="MMAD/dataset/MMAD/mmad.json", help="mmad.json 路径")
    parser.add_argument("--output_dir", type=str, default="./result", help="输出目录")
    parser.add_argument("--model", type=str, default="doubao-seed-1-6-vision-250815", help="视觉模型名称")
    parser.add_argument("--depth_quota", type=int, default=1, help="agent 最大轮数（建议 1~2）")
    parser.add_argument("--few_shot", type=int, default=1, help="few-shot 数量（0 关闭）")
    parser.add_argument("--similar_template", action="store_true", help="使用 similar_templates，否则 random_templates")
    parser.add_argument("--start_idx", type=int, default=0, help="起始索引")
    parser.add_argument("--max_samples", type=int, default=None, help="最大样本数（测试用）")
    parser.add_argument("--save_every", type=int, default=20, help="每 N 张保存一次")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    run_log_dir = os.path.join(args.output_dir, "vad2_runs")
    os.makedirs(run_log_dir, exist_ok=True)
    answers_json_path = os.path.join(
        args.output_dir,
        f"answers_vad2_{args.model.replace('/','_')}_{args.few_shot}shot_{'similar' if args.similar_template else 'random'}.json",
    )

    # load existing
    if os.path.exists(answers_json_path):
        with open(answers_json_path, "r", encoding="utf-8") as f:
            all_answers = json.load(f)
    else:
        all_answers = []
    existing_images = {a["image"] for a in all_answers}

    # load dataset
    if not os.path.exists(args.json_path):
        raise FileNotFoundError(args.json_path)
    with open(args.json_path, "r", encoding="utf-8") as f:
        chat_ad = json.load(f)

    image_paths = sorted(chat_ad.keys())
    if args.start_idx > 0:
        image_paths = image_paths[args.start_idx :]
    if args.max_samples is not None:
        image_paths = image_paths[: args.max_samples]

    # configure agents client for Volcano/Ark
    set_default_openai_api("chat_completions")
    set_tracing_disabled(True)
    api_key = '***REDACTED-SEED-KEY***'
    base_url = os.environ.get("OPENAI_API_BASE", "https://ark.cn-beijing.volces.com/api/v3")
    volcano_client = AsyncOpenAI(base_url=base_url, api_key=api_key)
    set_default_openai_client(volcano_client)

    cfg = DualVADConfig(model=args.model, depth_quota=args.depth_quota)
    system = DualVADAgentSystem(config=cfg)

    # 逐图处理
    for idx, image_rel in enumerate(tqdm(image_paths, desc="MMAD")):
        if image_rel in existing_images:
            continue

        text_gt = chat_ad[image_rel]
        questions, answers, questions_text = parse_conversation(text_gt)
        if not questions:
            continue

        query_path = os.path.join(args.data_path, image_rel)
        if not os.path.exists(query_path):
            continue

        few_shot_paths = []
        if args.few_shot > 0:
            key = "similar_templates" if args.similar_template else "random_templates"
            few_shot_paths = (text_gt.get(key, []) or [])[: args.few_shot]

        # load images
        query_rgb = _load_image_rgb(query_path)
        few_shot_frames = []
        for p in few_shot_paths:
            fp = os.path.join(args.data_path, p)
            if os.path.exists(fp):
                few_shot_frames.append(_load_image_rgb(fp))

        visual_ctx = load_visual_ctx([query_rgb], few_shot_frames=few_shot_frames if few_shot_frames else None)

        # run agent（内部 proposer+refuter 若干轮 + 最后 mmad_answerer）
        report = system.run(visual_ctx, mmad_questions_text=questions_text)
        pred = _normalize_answer_list(report.get("mmad_answers"), expected_n=len(answers))

        # fallback: 如果模型没按 schema 给数组，尝试从字符串里抓字母（保守）
        if not pred:
            raw = json.dumps(report.get("mmad_answers"), ensure_ascii=False)
            letters = re.findall(r"\b([A-E])\b", raw.upper())
            if len(letters) >= len(answers):
                pred = letters[: len(answers)]

        if len(pred) != len(answers):
            # 记录为空，避免中断
            pred = [""] * len(answers)

        for q, gt, pa in zip(questions, answers, pred):
            question_full_text = f"{q['question_text']}\n{q['options_text']}"
            entry = {
                "image": image_rel,
                "question": question_full_text,
                "question_type": q.get("type", "Unknown"),
                "correct_answer": gt,
                "gpt_answer": pa,
            }
            all_answers.append(entry)

        # 每张图：单独落盘保存完整聚合/推理报告（避免 answers 文件过大）
        log_filename = image_rel.replace("/", "__")
        log_path = os.path.join(run_log_dir, f"{log_filename}.json")
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "image": image_rel,
                    "few_shot_paths": few_shot_paths,
                    "report": report,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        # 在第一条答案里记录报告文件路径，便于追溯
        all_answers[-len(answers)]["vad2_report_path"] = os.path.relpath(log_path, args.output_dir)

        if (idx + 1) % args.save_every == 0:
            with open(answers_json_path, "w", encoding="utf-8") as f:
                json.dump(all_answers, f, ensure_ascii=False, indent=2)

    with open(answers_json_path, "w", encoding="utf-8") as f:
        json.dump(all_answers, f, ensure_ascii=False, indent=2)

    print("Saved:", answers_json_path)


if __name__ == "__main__":
    main()


