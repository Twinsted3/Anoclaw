import re
import cv2
import base64
import json
import numpy as np
from dataclasses import dataclass


@dataclass
class VisualContext:
    full_frames: list
    region_pixels: list
    tube: dict

# Function to encode image as base64
def encode_image(frame_rgb, fmt=".jpg", jpeg_quality=95):
    params = []
    if fmt.lower() in (".jpg", ".jpeg"):
        params = [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)]

    #? fix color: cv2.imencode will invert channel 0 and 2 
    frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
    ok, buf = cv2.imencode(fmt, frame_bgr, params)
    
    if not ok:
        raise ValueError("cv.imencode failed")
    return base64.b64encode(buf.tobytes()).decode("utf-8")


def extract_frames_aegis(video_path, interval=30)->list: # video_path: str, interval: int
    vid = cv2.VideoCapture(video_path)
    frames_rgb_list = []
    count = 0
    while vid.isOpened():
        ret, frame_bgr = vid.read()
        if not ret:
            break
        if count % interval == 0:
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            frames_rgb_list.append(frame_rgb)
        count += 1
    vid.release()
    return frames_rgb_list


def extract_frames_forensics(base64_str)->list:
    frames_rgb_list = []

    img_data = base64.b64decode(base64_str)
    np_arr = np.frombuffer(img_data, np.uint8)

    frame_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    #? fix color: cv2.imencode will invert channel 0 and 2 
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

    frames_rgb_list.append(frame_rgb)
    return frames_rgb_list


def load_visual_ctx(rgb_frames:list):
    return VisualContext(full_frames=rgb_frames, region_pixels=[], tube={"":[]})


def find_last_json(chat_history:list):
    # Iterate through the chat history in reverse order
    for entry in reversed(chat_history):
        if "type" in entry.keys():
            if entry["type"] == "message":
                text = entry["content"][0]["text"]

            elif entry["type"] == "function_call_output":
                text = entry["output"]
            else:
                continue
        else:
            continue
        
        # Use regex to find JSON-like substrings
        json_matches = re.findall(r'\{.*?\}', text, re.DOTALL)
        if json_matches:
            # Return the last JSON-like substring found
            return json_matches[-1]

    return None



def no_epoche_check(result:list) -> bool:
    criteria_met = False

    try:
        json_str = find_last_json(result)

        if json_str is None:
            return criteria_met
        
        json_data = json.loads(json_str)
        if json_data['TBD']==0:
            criteria_met = True
            
    except Exception as e:
        print(f"[no_epoche_check] ERROR: {e}")
        criteria_met = False

    return criteria_met



