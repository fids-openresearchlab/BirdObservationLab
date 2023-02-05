import logging
import queue
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Queue
from threading import Event

import ray

from birdwatchpy.frames.FrameData import FrameData
from birdwatchpy.logger import get_logger

logger = get_logger(log_name="ImageFolderLoader", stream_logging_level=logging.DEBUG, file_handler=True,
                    filename='base.log')

fps = 29.97


class ImageFolderLoader:
    def __init__(self, img_path: Path, session_id: str):
        self.frame_q = Queue(10)
        self.event = Event()

        logger.info(f"ImageFolderLoader: Start thread getting frames from {img_path}.")

        # Creating threaded executor
        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(read_video_worker, img_path, session_id, self.frame_q, self.event)
        executor.shutdown(wait=False)

    def get_frame(self):
        queued_frames_count = self.frame_q.qsize()
        logger.info(f"ImageFolderLoader: Queued Frames: {queued_frames_count}.")

        try:
            logger.info("ImageFolderLoader: Got frame from queue")
            return self.frame_q.get(block=True, timeout=30)
        except queue.Empty:
            logger.critical("ImageFolderLoader: Timeout. Frame queue empty.")
            return -1, 'Exit Event'


def read_video_worker(video_path: Path, session_id: str, frame_q: Queue, event: Event):
    try:
        session_id = str(video_path.stem)

        start_timestamp = int(session_id.split('_')[1])
        time_multiplicator = 1 / fps

        all_images = list(Path(dir).glob('.png'))
        all_images.sort()
        tasks = []

        prev_img = None
        for img in all_images:
            if prev_img is None:
                prev_img = img
                continue

            # Sleep
            time.sleep(0.03)  # ToDo: hardcoded. Change

            # if time.time()-timestamp < 1/FPS:
            #     continue

            ret, frame_img = cap.read()
            timestamp = time.time()
            if ret is True:
                if frame_img is None:
                    continue

                try:
                    logger.info("ImageFolderLoader: New frame added to queue")
                    start = time.time()
                    frame_ref = ray.put([FrameData(session_id, int(frame_number),
                                                   start_timestamp + int(time_multiplicator * frame_number)),
                                         frame_img])
                    print(f"Ray put took: {time.time() - start}")
                    frame_q.put((frame_number, frame_ref), block=True, timeout=60)

                except queue.Full:
                    logger.critical("ImageFolderLoader: Timeout. Frame queue full. Exiting")
                    event.set()
                except Exception as e:
                    logger.exception(
                        f"ImageFolderLoader: Unknown Error.  Exception: {e} Traceback: {traceback.print_exc()}")
            else:
                break

            frame_number += 1

        cap.release()
        logger.info("ImageFolderLoader: Exit event received or video file out of frames. Exiting")

    except Exception as e:
        logger.critical(
            f"ImageFolderLoader: Unhandled exception in thread. Exception: {e} Traceback: {traceback.print_exc()}")
