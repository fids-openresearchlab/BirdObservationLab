import logging
import queue
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Queue
from threading import Event
import ray
import cv2 as cv

from birdwatchpy.frames.FrameData import FrameData
from birdwatchpy.logger import get_logger

logger = get_logger(log_name="VideoLoder", stream_logging_level=logging.DEBUG, file_handler=True,
                   filename='base.log')

fps = 29.97

class VideoLoader:
    def __init__(self, video_path: Path):
        self.frame_q = Queue(70)
        self.event = Event()
        self.time_last_received_frame = time.time()
        self.video_path = video_path
        self.executor = None


    def start(self):
        logger.info(f"VideoLoader: Start thread getting frames from {self.video_path}.")

        # Creating threaded executor
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.executor.submit(read_video_worker, self.video_path, self.frame_q, self.event)
        self.executor.shutdown(wait=False)

    def get_frame(self):
        queued_frames_count = self.frame_q.qsize()

        try:
            logger.info("VideoLoader: Got frame from queue")
            return self.frame_q.get(block=True, timeout = 30)
        except queue.Empty:
            logger.critical("VideoLoader: Timeout. Frame queue empty.")
            return -1, 'Exit Event'



def read_video_worker(video_path: Path, frame_q: Queue, event: Event):
    try:
        logger.info("VideoLoader: In thread.")

        cap = cv.VideoCapture(str(video_path),  cv.CAP_FFMPEG)
        cap.set(cv.CAP_PROP_BUFFERSIZE, 2)
        print(cap.get(cv.CAP_PROP_BUFFERSIZE))
        session_id = str(video_path.stem)

        start_timestamp = int(session_id.split('_')[1])
        time_multiplicator=1/fps

        frame_number = 0
        while cap.isOpened() and not event.is_set():
            # Sleep
            time.sleep(0.023)  # ToDo: hardcoded. Change

           # if time.time()-timestamp < 1/FPS:
           #     continue

            ret, frame_img = cap.read()
            timestamp = time.time()
            if ret is True:
                if frame_img is None:
                    continue

                try:
                    start = time.time()
                    frame_ref = ray.put([FrameData(session_id, int(frame_number), start_timestamp+int(time_multiplicator*frame_number)), frame_img])
                    print(f"Ray put took: {time.time()-start}")
                    frame_q.put((frame_number, frame_ref), block=True, timeout=60)

                except queue.Full:
                    logger.critical("VideoLoader: Timeout. Frame queue full. Exiting")
                    event.set()
                except Exception as e:
                    logger.exception(
                        f"VideoLoader: Unknown Error.  Exception: {e} Traceback: {traceback.print_exc()}")
            else:
                break

            frame_number += 1



        cap.release()
        logger.info("VideoLoader: Exit event received or video file out of frames. Exiting")

    except Exception as e:
        logger.critical(
            f"VideoLoader: Unhandled exception in thread. Exception: {e} Traceback: {traceback.print_exc()}")
