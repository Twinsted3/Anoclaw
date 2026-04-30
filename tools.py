import os
from openai import OpenAI
from utils import encode_image, VisualContext
from agents import function_tool, RunContextWrapper
from prompts import external_trigger


# os.environ["OPENAI_API_KEY"] = "***REDACTED-OPENAI-KEY***"
os.environ["OPENAI_API_KEY"] = "***REDACTED-SEED-KEY***"

client = OpenAI(base_url="https://ark.cn-beijing.volces.com/api/v3", api_key=os.environ["OPENAI_API_KEY"])
ext_MODEL = "doubao-seed-1-6-vision-250815"
int_MODEL = "doubao-seed-1-6-vision-250815"
temperature = 0
max_tokens = 700


#? receives a question about certain logic and produces reasoning about it
@function_tool
def initial_skeptical_logic(visual_ctx: RunContextWrapper[VisualContext]) -> str:

    # prepare the external skeptic input
    frames = visual_ctx.context.full_frames # a list of cv2 RGB images
    few_shot_frames = visual_ctx.context.few_shot_frames if visual_ctx.context.few_shot_frames else []
    
    # convert the frames to Base64
    frames_b64 = [encode_image(f) for f in frames]
    few_shot_b64 = [encode_image(f) for f in few_shot_frames]

    # Step 2: Prepare messages with frames
    messages_ext = [
        {"role": "system", "content": "You are a video QA assistant."},
    ]
    
    # 先添加few-shot参考图片（正常样本）
    if few_shot_b64:
        incontext_text = f"The first {len(few_shot_b64)} image(s) are normal sample(s), which can be used as a template to compare."
        for i, img_b64 in enumerate(few_shot_b64):
            messages_ext.append({
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {
                            "url": f"data:image/jpeg;base64,{img_b64}"
                    }},
                    {"type": "text", "text": f"Normal sample {i+1}"}
                ]
            })
        # 添加说明文本
        messages_ext.append({
            "role": "user",
            "content": incontext_text
        })
    
    # 然后添加查询图片
    for i, img_b64 in enumerate(frames_b64):
        messages_ext.append({
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{img_b64}"
                }},
                {"type": "text", "text": f"Query image - Frame {i//1 + 1}"}
            ]
        })
    
    messages_ext.append({"role": "user", "content": external_trigger})

    # Step 3: Query GPT-4o
    response_ext = client.chat.completions.create(
        model=int_MODEL,
        messages=messages_ext,
        temperature=temperature,
        max_tokens=max_tokens
    )

    skeptic_reasoning = response_ext.choices[0].message.content

   
    return skeptic_reasoning




#? receives a question about certain logic and produces reasoning about it
@function_tool
def external_skeptic(visual_ctx: RunContextWrapper[VisualContext], question:str) -> str:

    # prepare the external skeptic input
    frames = visual_ctx.context.full_frames # a list of cv2 RGB images
    few_shot_frames = visual_ctx.context.few_shot_frames if visual_ctx.context.few_shot_frames else []
    
    # convert the frames to Base64
    frames_b64 = [encode_image(f) for f in frames]
    few_shot_b64 = [encode_image(f) for f in few_shot_frames]

    # Step 2: Prepare messages with frames
    messages_ext = [
        {"role": "system", "content": "You are a video QA assistant."},
    ]
    
    # 先添加few-shot参考图片（正常样本）
    if few_shot_b64:
        incontext_text = f"The first {len(few_shot_b64)} image(s) are normal sample(s), which can be used as a template to compare."
        for i, img_b64 in enumerate(few_shot_b64):
            messages_ext.append({
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {
                            "url": f"data:image/jpeg;base64,{img_b64}"
                    }},
                    {"type": "text", "text": f"Normal sample {i+1}"}
                ]
            })
        # 添加说明文本
        messages_ext.append({
            "role": "user",
            "content": incontext_text
        })
    
    # 然后添加查询图片
    for i, img_b64 in enumerate(frames_b64):
        messages_ext.append({
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{img_b64}"
                }},
                {"type": "text", "text": f"Query image - Frame {i//1 + 1}"}
            ]
        })
    
    messages_ext.append({"role": "user", "content": external_trigger})

    reflective_trigger = f'''
        Now please conduct reasoning specifically about this question:
        <Start of Question> {question} <End of Question>. 
    '''
    
    messages_ext.append({"role": "user", "content": reflective_trigger})

    # Step 3: Query GPT-4o
    response_ext = client.chat.completions.create(
        model=ext_MODEL,
        messages=messages_ext,
        temperature=temperature,
        max_tokens=max_tokens
    )

    skeptic_reasoning = response_ext.choices[0].message.content

   
    return skeptic_reasoning


#? verifies if anomaly descriptions appear in normal sample images (batch verification)
@function_tool
def verify_anomaly(visual_ctx: RunContextWrapper[VisualContext], anomaly_descriptions: str) -> str:
    """
    验证异常描述是否是异常的
    
    Args:
        visual_ctx: 只使用 few_shot_frames（正常样本）
        anomaly_descriptions: 所有异常描述的文本（可以包含多个异常，用编号或分隔符区分）
    
    Returns:
        验证结果文本，对每个异常说明是否在正常样本中出现过
    """
    # 只使用正常样本（few_shot_frames）
    normal_frames = visual_ctx.context.few_shot_frames if visual_ctx.context.few_shot_frames else []
    
    if not normal_frames:
        return "No normal samples provided for verification."
    
    # convert the normal frames to Base64
    normal_frames_b64 = [encode_image(f) for f in normal_frames]

    # Prepare messages with only normal sample images
    messages_ext = [
        {"role": "system", "content": "You are an anomaly verification assistant. You examine normal sample images to verify if described anomalies actually appear in them."},
    ]
    
    # 添加正常样本图片
    for i, img_b64 in enumerate(normal_frames_b64):
        messages_ext.append({
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{img_b64}"
                }},
                {"type": "text", "text": f"Normal sample {i+1}"}
            ]
        })
    
    verification_prompt = f"""
        Now please verify ALL the following anomaly descriptions:
        <Start of Anomaly Descriptions>
        {anomaly_descriptions}
        <End of Anomaly Descriptions>

        Please examine the normal sample images above and for EACH anomaly description, determine:
        1. Does this anomaly or similar pattern appear in any of the normal samples?
        2. If yes, provide evidence (which sample, where in the image).
        3. If no, confirm that this is a genuine anomaly not present in normal samples.

        Please provide verification results for ALL anomalies in a structured format, clearly indicating which anomalies appear in normal samples and which do not.
        """
            
    messages_ext.append({"role": "user", "content": verification_prompt})

    # Query the model
    response_ext = client.chat.completions.create(
        model=ext_MODEL,
        messages=messages_ext,
        temperature=temperature,
        max_tokens=max_tokens
    )

    verification_result = response_ext.choices[0].message.content

    return verification_result


#? checks if anomaly claims actually appear in the query image (batch checking)
@function_tool
def check_anomaly_in_query(visual_ctx: RunContextWrapper[VisualContext], anomaly_claims: str) -> str:
    """
    检查异常声明是否真的在被测图像中出现
    
    Args:
        visual_ctx: 使用 full_frames（被测图像）
        anomaly_claims: 所有异常声明的文本（可以包含多个异常，用编号或分隔符区分）
    
    Returns:
        检查结果文本，对每个异常说明是否真的在被测图像中出现
    """
    # 使用被测图像（full_frames）
    query_frames = visual_ctx.context.full_frames
    
    if not query_frames:
        return "No query images provided for checking."
    
    # convert the query frames to Base64
    query_frames_b64 = [encode_image(f) for f in query_frames]

    # Prepare messages with query images
    messages_ext = [
        {"role": "system", "content": "You are an anomaly verification assistant. You examine query images to verify if described anomalies actually appear in them."},
    ]
    
    # 添加被测图像
    for i, img_b64 in enumerate(query_frames_b64):
        messages_ext.append({
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{img_b64}"
                }},
                {"type": "text", "text": f"Query image - Frame {i+1}"}
            ]
        })
    
    # 添加检查任务说明
    check_prompt = f"""
        You need to verify if ALL the following anomaly claims actually appear in the query image(s) shown above.

        <Start of Anomaly Claims>
        {anomaly_claims}
        <End of Anomaly Claims>

        Please carefully examine the query image(s) and for EACH anomaly claim, determine:
        1. Does this anomaly claim actually appear in the query image(s)?
        2. If yes, provide evidence (which frame/image, where in the image, what you see).
        3. If no, explain why the claim does not match what you see in the query image(s).
        4. If the description is ambiguous, incomplete, or does not match what you can observe, explicitly flag it as "description unclear / needs refinement".

        Be specific about the location and characteristics of each anomaly if it exists.
        Please provide check results for ALL anomalies in a structured format, clearly indicating which anomalies appear in the query images, which do not, and which have unclear descriptions.
        """
    
    messages_ext.append({"role": "user", "content": check_prompt})

    # Query the model
    response_ext = client.chat.completions.create(
        model=ext_MODEL,
        messages=messages_ext,
        temperature=temperature,
        max_tokens=max_tokens
    )

    check_result = response_ext.choices[0].message.content

    return check_result


