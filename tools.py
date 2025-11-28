import os
from openai import OpenAI
from utils import encode_image, VisualContext
from agents import function_tool, RunContextWrapper
from prompts import external_trigger


os.environ["OPENAI_API_KEY"] = "***REDACTED-OPENAI-KEY***"

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
ext_MODEL = "gpt-4o-2024-08-06"
int_MODEL = "o3-mini-2025-01-31"
temperature = 0
max_tokens = 700


#? receives a question about certain logic and produces reasoning about it
@function_tool
def initial_skeptical_logic(visual_ctx: RunContextWrapper[VisualContext]) -> str:

    # prepare the external skeptic input
    frames = visual_ctx.context.full_frames # a list of cv2 RGB images
    # convert the frames to Base64
    frames_b64 = [encode_image(f) for f in frames]

    # Step 2: Prepare messages with frames
    messages_ext = [
        {"role": "system", "content": "You are a video QA assistant."},
    ]
    for i, img_b64 in enumerate(frames_b64):
        messages_ext.append({
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{img_b64}"
                }},
                {"type": "text", "text": f"Frame {i//1 + 1}"}
            ]
        })
    
    messages_ext.append({"role": "user", "content": external_trigger})

    # Step 3: Query GPT-4o
    response_ext = client.chat.completions.create(
        model=ext_MODEL,
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
    # convert the frames to Base64
    frames_b64 = [encode_image(f) for f in frames]

    # Step 2: Prepare messages with frames
    messages_ext = [
        {"role": "system", "content": "You are a video QA assistant."},
    ]
    for i, img_b64 in enumerate(frames_b64):
        messages_ext.append({
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{img_b64}"
                }},
                {"type": "text", "text": f"Frame {i//1 + 1}"}
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


