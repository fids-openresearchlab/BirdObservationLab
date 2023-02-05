import time
from argparse import ArgumentParser
from glob import glob
from pathlib import Path
import cv2

import ray
from birdwatchpy.worker.sparse_opt_flow_worker import sparse_lk_cpu_test_task
from birdwatchpy.frames.FrameData import FrameData

ray.init(num_cpus=10)

params = {
    "feature_detector": {
        # Parameters for Shi-Tomasi corner detection
        "name": "goodFeaturesToTrack",
        "feature_params": {
            "maxCorners": 2000,
            "qualityLevel": 0.03,
            "minDistance": 30,
            "blockSize": 10
        },
    },
    # Parameters for Lucas-Kanade optical flow
    "lk_params": {
        "winSize": [50, 50],
        "maxLevel": 6,
        "criteria": (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)}
}

def Average(lst):
    return sum(lst) / len(lst)

def calc_result(results):
    if len(results) > 0:
        average = Average(results)
        print(f"avg {average}")
        print(f"max {max(results)}")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-r", "--recursive", action='store_true', help="Recursively load from subfolders")
    parser.add_argument("path", help="Input Path")

    args = parser.parse_args()

    if args.recursive:
        results = []
        for dir in glob(args.path + "/*/images", recursive=False):
            print(dir)
            all_images = list(Path(dir).glob('*.png'))
            all_images.sort()
            tasks=[]

            prev_img_ref = None
            for img_path in all_images:
                print(img_path)
                if len(tasks) > 50:
                    time.sleep(1)
                if prev_img_ref is None:
                    prev_img_ref = ray.put([FrameData("session_id", 0, time.time()), cv2.imread(img_path.as_posix())])
                    continue

                img_ref = ray.put([FrameData("session_id", 0, time.time()), cv2.imread(img_path.as_posix())])

                tasks.append(sparse_lk_cpu_test_task.remote((params, prev_img_ref, img_ref)))

                if len(tasks) > 7:
                    ready_refs, tasks = ray.wait(tasks, num_returns=3)

                    #time.sleep(200)
                    for ref in ready_refs:
                        print(ref)
                        results.append(ray.get(ref)[1])
                    calc_result(results)

    ready_refs, tasks = ray.wait(tasks, num_returns=len(tasks))
    for ref in ready_refs:
        print(ref)
        results.append(ray.get(ref)[1])
    calc_result(results)

