import logging
import queue
import time
import traceback
from argparse import ArgumentParser
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor, ALL_COMPLETED
from glob import glob
from multiprocessing import Event, Queue
from pathlib import Path

import docker
from birdwatchpy.logger import get_logger
from birdwatchpy.utils import get_project_root

logger = get_logger(log_name="DetectionController", stream_logging_level=logging.DEBUG, file_handler=True,
                    log_file_path=(get_project_root() / "logs" / "base.log").as_posix())

client = docker.from_env()

# The Tiles Edge value controls how close to the edge of a tile an object must be to be considered for re-combining when
# both tiling and recombining have been enabled. The smaller the value, the closer the object must be to the edge of a
# tile. The factor is multiplied by the width and height of the detected object. Possible range to consider would be
# 0.01 to 0.5. If set to zero, then the detected object must be right on the tile boundary to be considered.
# More Info: https://www.ccoderun.ca/darkhelp/api/classDarkHelp_1_1Config.html#add15d57a384c7eb827078b4b3a279b79
TILES_EDGE_FACTOR = 0.4

# This value controls how close the rectangles needs to line up on two tiles before the predictions are combined.

# This is only used when both tiling and recombining have been enabled. As the value approaches 1.0, the closer the
# rectangles have to be "perfect" to be combined. Values below 1.0 are impossible, and predictions will never be
# combined. Possible range to consider might be 1.10 to 1.50 or even higher; this also depends on the nature/shape of
# the objects detected and how the tiles are split up. For example, if the objects are pear-shaped, where the smaller
# end is on one tile and the larger end on another tile, you may need to increase this value as the object on the
# different tiles will be of different sizes. The default is 1.20.
# More Info: https://www.ccoderun.ca/darkhelp/api/classDarkHelp_1_1Config.html#add15d57a384c7eb827078b4b3a279b79
TILES_RECT_FACTOR = 2.7

#The non-maximal suppression threshold to use when predicting.
NM_SUPRRESSION_THRESHOLD = 0.2

def detection_on_img_dir(gpu, img_dir: Path, save_out_img=True, engine="darknet"):
    (img_dir.parent / "yolov4_out").mkdir(parents=False, exist_ok=True)
    img_list_string = ""
    for img_name in map(lambda path: path.name, sorted(list(img_dir.glob("*.png")))):
        img_list_string += " " + "/workspace/" + str(img_dir.parent.name) + "/images/" + str(img_name) + " "
    container = client.containers.run('daisukekobayashi/darknet:gpu-cv-cc61',
                                      # "/bin/sh -c cd /detection/yolov4/; /bin/sh -c ls -l",
                                      f'/DarkHelp/build/src-tool/DarkHelp --json --driver {engine} --autohide off  --tiles on --tile-edge {TILES_EDGE_FACTOR} --tile-rect {TILES_RECT_FACTOR} --duration off --nms {NM_SUPRRESSION_THRESHOLD} --threshold 0.05 /detection/yolov4/bird_detector.names /detection/yolov4/bird_detector.cfg /detection/yolov4/bird_detector_final.weights --outdir /workspace/{img_dir.parent.name}/yolov4_out {"--keep" if save_out_img else ""} {img_list_string}',
                                      name=f"darkhelp_inference_{img_dir.parent.name}",
                                      volumes=[f'{img_dir.parents[1]}:/workspace',
                                               '/mnt/kubus/kubus_data/workspace/yolov5_playground/yolo_data/960_1088:/detection/yolov4/'],
                                      working_dir="/workspace",
                                      runtime="nvidia",
                                      device_requests=[
                                          docker.types.DeviceRequest(device_ids=[str(gpu)], capabilities=[['gpu']])],
                                      remove=True)  # ToDo: Alwys show output. Especially if failed

    print(container)

    # container.exec_run(
    #    f'/DarkHelp/build/src-tool/DarkHelp --json --driver opencvcpu --tiles on --autohide off --duration off --threshold 0.1 /detection/yolov4/bird_detector.names /detection/yolov4/bird_detector.cfg /detection/yolov4/bird_detector_final.weights --outdir /workspace/yolov4/ -keep  {img_list_string}', )


def start_container(src_dir, gpu):
    return client.containers.run('daisukekobayashi/darknet:gpu-cv-cc61',
                                 # "/bin/sh -c cd /detection/yolov4/; /bin/sh -c ls -l",
                                 name="darkhelp_inference",
                                 volumes=[f'{src_dir}:/workspace',
                                          '/mnt/kubus/kubus_data/workspace/yolov5_playground/yolo_data/960_1088:/detection/yolov4/'],
                                 working_dir="/workspace",
                                 runtime="nvidia",
                                 detach=True)

def detection_controller_gpu_worker(gpu: int, detection_task_q: Queue, event: Event):
    logger.info(f"gpu_worker: started")


    while not (event.is_set() and detection_task_q.empty()):
        try:
            if detection_task_q.qsize() > 0:
                try:
                    image_dir = detection_task_q.get()
                    logger.info(f"gpu_worker: Detection Task received. GPU: {gpu}")
                except queue.Empty:
                    continue  # Detection task already fetched by other thread

                detection_on_img_dir(gpu, image_dir, save_out_img=True)
                logger.info(f"gpu_worker: Successfully ran detections on folder")

                continue

            time.sleep(10)

        except Exception as e:
            logger.exception(f"Unknown Error.  Exception: {e} Traceback: {traceback.print_exc()}")


if __name__ == "__main__":
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--img_dir",
                       help="Path to directory with image files or the parent directory if recursive is set to true")
    parser.add_argument("--gpus", help="Number of GPUs to use",
                        type=int)
    parser.add_argument("--recursive", action='store_true',
                        help="Recursively create image lists for directories within path")
    parser.add_argument("--save_out_img", dest='save_out_img', action='store_true')

    args = parser.parse_args()

    if args.recursive:
        if args.img_dir:
            gpu_worker = []
            gpu_worker_pool = ThreadPoolExecutor(max_workers=args.gpus)
            detection_task_q = Queue()
            event = Event()

            for gpu in range(args.gpus):
                gpu_worker.append(gpu_worker_pool.submit(detection_controller_gpu_worker, gpu, detection_task_q,event))
            print(args.img_dir)
            for dir in glob(args.img_dir + "/*/images", recursive=False):
                sequence_path = Path(dir)
                print(dir)
                detection_task_q.put(Path(dir))

        timeout = None
        logger.info(
            f"Wait for running worker to finish. Timeout set to {timeout} seconds")
        futures.wait(gpu_worker, timeout=timeout, return_when=ALL_COMPLETED)
        logger.info(f"workers successfully finished.")

    else:
        if args.img_dir:
            container = None  # start_container(src_dir=args.img_dir)
            # detection_img_dir(Path(args.img_dir), args.save_out_img)
