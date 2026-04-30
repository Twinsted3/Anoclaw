import os
import multiprocessing, traceback
from pprint import pprint as pp
import json

from agents import SQLiteSession, RunConfig

from load_dataset import get_dataset
from multi_round_skeptic import Skeptic_agent
from utils import load_visual_ctx, extract_frames_aegis, extract_frames_forensics



# os.environ["OPENAI_API_KEY"] = "***REDACTED-OPENAI-KEY***"
os.environ["OPENAI_API_KEY"] = "***REDACTED-SEED-KEY***"

def merge_session_input(history_items, new_input_items):
    if isinstance(new_input_items, list):
        return history_items + new_input_items
    else:
        return history_items + [{"role": "user", "content": new_input_items}]


def run_agent(vid_path_list, meta_data_list, run_config, args, idx):

    worker_loop_count = 0
    for vid_path, meta_data in zip(vid_path_list, meta_data_list):
        try:
            # remove repetition
            existing_files = os.listdir(args.save_dir)
            target_file = f"worker{idx}_{worker_loop_count}.json"
            if target_file in existing_files:
                print(f"[worker {idx}] Skipping existing file: {target_file}")
                worker_loop_count += 1
                continue

            #initialize session and skeptic agent
            session = SQLiteSession("user_42")  # any id
            skeptic_agent = Skeptic_agent(session, run_config)

            # prepare visual context
            if args.dataset == "aegis":
                printed_vid_id = vid_path 
            elif "forensics" in args.dataset:
                printed_vid_id = meta_data["index"] 

            print(f"=== Processing video: {printed_vid_id}. ===")

            if args.dataset == "aegis": # vid_path is video file path
                rgb_vid = extract_frames_aegis(vid_path)
            elif "forensics" in args.dataset: # vid_path is base64 str
                rgb_vid = extract_frames_forensics(vid_path)
            else:
                raise NotImplementedError(f"Dataset {args.dataset} not implemented for frame extraction.")
            
            visual_ctx = load_visual_ctx(rgb_vid)

            # run agent
            result, chat_length = skeptic_agent.run(visual_ctx)

            # save output
            output = {"result": result, "rounds": chat_length}
            output["meta_data"] = meta_data

            print(f"+++ Finished video {printed_vid_id}. +++")

            with open(os.path.join(args.save_dir, f"worker{idx}_{worker_loop_count}.json"), "w") as f:
                json.dump(output, f, indent=4)

            worker_loop_count += 1
    
        except Exception as e:
            print(f"[worker {idx}] ERROR: {e}\n{traceback.format_exc()}")



if __name__ == "__main__":

    # int_MODEL = "o3-mini-2025-01-31"
    int_MODEL = "doubao-seed-1-6-vision-250815"
    run_config = RunConfig(
        session_input_callback=merge_session_input,
        trace_include_sensitive_data=True,
        model= int_MODEL
        )
    
    # set up an argument parser to get dataset name
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="", help="Dataset name: aegis or inception")
    parser.add_argument("--save_dir", type=str, default="", help="Directory to save output files")
    parser.add_argument("--multithread_factor", type=int, default=100, help="Number of threads for multiprocessing")
    args = parser.parse_args()

    dataset = args.dataset

    vid_path_list, meta_data_list = get_dataset(dataset)

    print(f"Total data samples to process: {len(vid_path_list)}")

    # randomly sample videos for testing
    # import random
    # random.seed(42)
    # sampled_indices = random.sample(range(len(vid_path_list)), 20)
    # vid_path_list = [vid_path_list[i] for i in sampled_indices]
    # meta_data_list = [meta_data_list[i] for i in sampled_indices]


    # multi-thread for the vid_path_list and meta_data_list
    divider = args.multithread_factor
    total_vid = len(vid_path_list)
    step = total_vid // divider
    start_idxs = [i for i in range(0, total_vid, step)]
    end_idxs = [i for i in range(step, total_vid + step, step)]
    end_idxs[-1] = total_vid

    print(f"threads_num: {len(start_idxs)}")
    print(f"start_idxs: {start_idxs}")
    print(f"end_idxs: {end_idxs}")


    processes = []
    for idx in range(len(start_idxs)):
        vid_path_list_seg = vid_path_list[start_idxs[idx]:end_idxs[idx]]
        meta_data_list_seg = meta_data_list[start_idxs[idx]:end_idxs[idx]]
        p = multiprocessing.Process(target=run_agent, args=(vid_path_list_seg, meta_data_list_seg, run_config, args, idx))
        processes.append(p)
        p.start()
    
    for p in processes:
        p.join()
