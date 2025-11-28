import os
import json
import pandas as pd


def get_dataset(dataset, sampling_interval=30):

    if dataset == "aegis":

        #? meta data paths
        files_paths = ["/data/yinjie/ai_vid_detect/data/AEGIS/data/hard_test_set-00000-of-00004.parquet",\
                        "/data/yinjie/ai_vid_detect/data/AEGIS/data/hard_test_set-00001-of-00004.parquet",\
                        "/data/yinjie/ai_vid_detect/data/AEGIS/data/hard_test_set-00002-of-00004.parquet",\
                        "/data/yinjie/ai_vid_detect/data/AEGIS/data/hard_test_set-00003-of-00004.parquet"]

        df = pd.concat([pd.read_parquet(file_path) for file_path in files_paths], ignore_index=True)

        print(f"Loaded AEGIS hard test, size: {df.shape}")

        #? video dirs
        dvf_dir = "/data/yinjie/ai_vid_detect/data/AEGIS-dataset/data/test_data/real/dvf"
        yt_dir = "/data/yinjie/ai_vid_detect/data/AEGIS-dataset/data/test_data/real/youtube"
        sora_dir = "/data/yinjie/ai_vid_detect/data/AEGIS-dataset/data/test_data/ai_gen/sora"
        kling_dir = "/data/yinjie/ai_vid_detect/data/AEGIS-dataset/data/test_data/ai_gen/kling"

        vid_path_list = []
        meta_data_list = []

        # take df between start_idx and end_idx
        for rows in df.itertuples():
            # meta_data, GT_reason
            meta_data = rows.meta_data
            GT_reason = rows.reason

            meta_data = json.loads(meta_data)
            if meta_data['ground_truth'] == 'ai':
                if meta_data['generator'] == 'sora':
                    vid_dir = sora_dir
                elif meta_data['generator'] == 'kling':
                    vid_dir = kling_dir

            if meta_data['ground_truth'] == 'real':
                if meta_data['data_source'] == 'DVF':
                    vid_dir = dvf_dir
                else:
                    vid_dir = yt_dir

            video_path = os.path.join(vid_dir, meta_data['original_id'] + ".mp4")

            vid_path_list.append(video_path)
            meta_data_list.append({"meta_data": meta_data, "GT_reason": GT_reason, "video_path": video_path})
        
        return vid_path_list, meta_data_list
    
    elif dataset == "forensics_vid":

        file_path = "/data/yinjie/ai_vid_detect/data/Forensics_bench/ForensicsBench.tsv"
        df_whole = pd.read_csv(file_path, sep="\t")

        #? get binary classification samples
        rows = df_whole[df_whole["question"]=="What is the authenticity of the video?"] 
        #? only keep entrie synthesis and real media, no face swap etc
        rows = rows[rows["Forgery Types"].isin(["Entire Synthesis", "Real media without being forged"])] 

        vid_path_list = []
        meta_data_list = []

        for idx in range(rows.shape[0]):
            row = rows.iloc[idx]
            # get image
            img_base64 = row["image"]
            gt = row["Forgery Types"]
            index = row["index"]

            meta_data = {
                "index": str(index),
                "GT": gt
            }
            vid_path_list.append(img_base64)
            meta_data_list.append(meta_data)
        
        return vid_path_list, meta_data_list


    elif dataset == "forensics_img":
        file_path = "/data/yinjie/ai_vid_detect/data/Forensics_bench/ForensicsBench.tsv"
        df_whole = pd.read_csv(file_path, sep="\t")
        
        #? get binary classification samples
        img_rows = df_whole[df_whole["question"]=="What is the authenticity of the image?"] 

        #? only keep entrie synthesis and real media, no face swap etc
        rows = img_rows[img_rows["Forgery Types"].isin(["Entire Synthesis", "Real media without being forged"])] 

        rows_sub = rows.sample(n=2500, random_state=42).reset_index(drop=True) # sample 2000 rows (too large to run all)
        

        vid_path_list = []
        meta_data_list = []

        for idx in range(rows_sub.shape[0]):
            row = rows_sub.iloc[idx]
            # get image
            img_base64 = row["image"]
            gt = row["Forgery Types"]
            index = row["index"]

            meta_data = {
                "index": str(index),
                "GT": gt
            }
            vid_path_list.append(img_base64)
            meta_data_list.append(meta_data)
        
        return vid_path_list, meta_data_list


    else:
        raise NotImplementedError(f"Dataset {dataset} not implemented.")
