import glob
import logging
import queue
import time
import traceback
from argparse import ArgumentParser
from pathlib import Path
from typing import Union
import ray
import cv2
from ray.util.queue import Queue

from birdwatchpy.Generators.ImageFolderLoader import ImageFolderLoader
from birdwatchpy.Generators.StreamLoader import StreamLoader
from birdwatchpy.Generators.VideoLoader import VideoLoader
from birdwatchpy.logger import get_logger
from birdwatchpy.worker.SOIFilterActor import SOIFilterActor
from birdwatchpy.worker.sparse_opt_flow_worker import sparse_lk_cpu_worker

logger = get_logger(log_name="StreamReceiver", stream_logging_level=logging.DEBUG, file_handler=True,
                    filename='base.log')

# Defines how long images are saved in the temporary folder
TEMP_STORAGE_DURATION = 3000

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

params_ref = ray.put(params)

opt_flow_processed_frames_q = queue.Queue()


class StreamHandler:

    def __init__(self, video_loader: Union[VideoLoader, ImageFolderLoader], gpus: int, params: dict):
        # Create thread save event. It signals threads to stop.
        self.event = video_loader.event
        # Queues
        self.sparse_opt_flow_q = Queue()
        # Threads and workers
        self.soi_filter_actor = SOIFilterActor.remote()
        self.sparse_opt_flow_workers= [sparse_lk_cpu_worker.remote((self.sparse_opt_flow_q, self.soi_filter_actor, params)) for i in range(18)]

        self.video_loader = video_loader

        # Wait for remote tasks and actors to start
        time.sleep(30)

        # Start getting frames from source
        self.video_loader.start()

    def run(self):
        try:
            previous_frame_w_img_ref = None
            logger.info("StreamHandler: efore Loop")
            while not (self.event.is_set() and opt_flow_processed_frames_q.empty()):
                logger.info("StreamHandler: In Loop")
                self.log_stats()

                if not self.event.is_set():
                    # Get mew frame and submit job
                    frame_number, current_frame_w_img_ref = self.video_loader.get_frame()
                    if frame_number==-1:
                        logger.info("StreamHandler: Received Exit Hint")
                        self.close()
                        return

                    self.soi_filter_actor.add_to_frame_buffer.remote((frame_number,current_frame_w_img_ref))

                    if current_frame_w_img_ref is None:
                        logger.info("StreamHandler: Frame Queue Empty")
                    elif current_frame_w_img_ref is not None:
                        if previous_frame_w_img_ref is None:
                            previous_frame_w_img_ref = current_frame_w_img_ref
                            continue

                        # Adjust workload to FPS
                        print(frame_number)
                        logger.info(f"StreamHandler: Opt Flow Queue: {self.sparse_opt_flow_q.size() }")
                        if frame_number % 4 ==0:
                            self.add_sparse_opt_flow_job(previous_frame_w_img_ref, current_frame_w_img_ref)
                        elif self.sparse_opt_flow_q.size() < 10 and frame_number % 2 == 0:
                            self.add_sparse_opt_flow_job(previous_frame_w_img_ref, current_frame_w_img_ref)

                        # The previous frame becomes the current frame
                        previous_frame_w_img_ref = current_frame_w_img_ref

                time.sleep(0.01)

            self.close()

        except Exception as e:
            logger.critical(
                f"Streameceiver: Unhandled exception in thread. Exception: {e} Traceback: {traceback.print_exc()}")

    def add_sparse_opt_flow_job(self, previous_frame_w_img_ref, current_frame_w_img_ref):
        logger.info("StreamHandler: Optical Flow Job Submitted")
        self.sparse_opt_flow_q.put((previous_frame_w_img_ref, current_frame_w_img_ref))


    def close(self, timeout=400):
        """
        Terminate running threads properly and handle remaining data
        """
        time.sleep(20) # ToDo: Remove and hanfle started processes
        logger.info(
            f"StreamHandler: Wait for running sparse optical flow workers to finish. Timeout set to {timeout} seconds")
        ray.wait(self.sparse_opt_flow_workers,timeout=1000)
        logger.info(f"StreamHandler: All workers successfully finished.")

        logger.info(f"StreamHandler: Wait for running SoiFilterActor to finish.")
        ray.get(self.soi_filter_actor.conclude.remote(), timeout=1500)
        logger.info(f"StreamHandler: SoiFilterActor finished.")

        # Process remaining queued results
        #self.proc_opt_flow_results()
        #self.soi_filter.conclude()

        # Process remaining filtered soi from filter
        #self.proc_filtered_soi()

        # Trigger events to stop e
        self.stop_export_event.set()
        self.stop_temp_storage_event.set()

        logger.info(f"StreamHandler: Wait for remaining worker to finish. Timeout set to {timeout} seconds")
        #futures.wait([self.export_worker, self.temp_storage_worker], timeout=timeout, return_when=ALL_COMPLETED)

        # To some checks in order to verify healthy termination of all threads and queues
        assert (self.priority_q.empty())
        assert (opt_flow_processed_frames_q.empty())
        assert (self.export_q.empty())

    def log_stats(self):
        """
        Log some basic statistics for monitoring purposes
        """
        pass
        #logger.info(f"StreamHandler: {'Stats:':20}  Sparse Optical Flow Jobs: {len(self.cpu_worker_pool._pending_work_items):02}")
        #logger.info(
        #    f"StreamHandler: {'Stats:':20}  {sum(1 for worker in self.gpu_worker if worker.running()):02} Running GPU Worker")
        #logger.info(f"StreamHandler: {'Stats:':20}  {self.priority_q.qsize()} priority_q size")
        #logger.info(
        #    f"StreamHandler: {'Stats:':20}  {opt_flow_processed_frames_q.qsize()} Sparse optical flow processed frames waiting for processing")
        #logger.info(f"StreamHandler: {'Stats:':20}  {self.export_q.qsize()} export_q size")
        #logger.info(f"StreamHandler: {'Stats:':20}  {self.temp_frames_q.qsize()} temp_frames_q size")
        #logger.info(f"StreamHandler: {'Stats:':20}  {len(self.soi_filter.results)}")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--src", help="Path or url to source file or directory")
    parser.add_argument("--type", choices=['video', 'video-folder', 'image-folder', 'stream'],
                        help="Input type. Can be one of the following: [video, video-folder, image-folder, stream] ")
    parser.add_argument("-r", "--recursive", action='store_true', help="Recursively load from subfolders")
    parser.add_argument("--feature_detector", choices=['fast', 'goodftt', ],
                        help="Feature detector to be used. Can be one of the following: [video, video-folder, image-folder, stream] ")
    args = parser.parse_args()

    if args.type == "video":
        if args.recursive:
            for video_path in glob.glob(f'{args.src}/*.avi'):
                StreamHandler(VideoLoader(Path(video_path)), gpus=10, params=params).run()
        else:
            StreamHandler(VideoLoader(Path(args.src)), gpus=10, params=params).run()
    elif args.type == "video-folder":
        pass  # ToDo: Implement
    elif args.type == "stream":
        StreamHandler(StreamLoader("rtsp://admin:q1w2e3r4@51.195.44.112:554/video1"), gpus=10, params=params).run()
    elif args.type == "image-folder":
        pass  # ToDo: Implement
