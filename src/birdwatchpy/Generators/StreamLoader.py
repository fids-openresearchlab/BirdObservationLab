import logging
import queue
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Event
import os

from birdwatchpy.config import get_network_latency, get_fps

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"]="rtsp_transport;udp|max_delay;60000000|buffer_size;2147479999|OPENCV_FFMPEG_DEBUG=1|OPENCV_VIDEOIO_DEBUG=1|OPENCV_LOG_LEVEL=DEBUG"
import ray

import cv2 as cv

from birdwatchpy.frames.FrameData import FrameData
from birdwatchpy.logger import get_logger

logger = get_logger(log_name="StreamLoader", stream_logging_level=logging.DEBUG, file_handler=True,
                    filename='base.log')




class StreamLoader:
    def __init__(self, video_src: str):
        self.video_src = video_src
        self.frame_q = Queue(100)
        self.event = Event()
        self.time_last_received_frame = time.time()


    def start(self):
        logger.info(f"VideoLoader: Start thread getting frames from {self.video_src}.")

        # Creating threaded executor
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.executor.submit(read_video_worker, self.video_src, self.frame_q, self.event)
        self.executor.shutdown(wait=False)

    def get_frame(self):
        try:
            logger.info("VideoLoader: Got frame from queue")
            return self.frame_q.get(block=True, timeout = 200)
        except queue.Empty:
            logger.critical("VideoLoader: Timeout. Frame queue empty.")
            return -1, 'Exit Event'

def read_video_worker(video_src: str, frame_q: Queue, event: Event):
    try:
        logger.info("VideoLoader: In thread.")

        latency = get_network_latency()
        fps = get_fps()

        cap = cv.VideoCapture(video_src,apiPreference=cv.CAP_FFMPEG)
        #cap.set(cv.CAP_PROP_BUFFERSIZE, 3)
        #print(cap.get(cv.CAP_PROP_BUFFERSIZE))

        session_id = f"{int(time.time())}_zoex"

        frame_number = 0
        while cap.isOpened() and not event.is_set():
            # Sleep
            time.sleep(1/fps)  # ToDo: hardcoded. Change

           # if time.time()-timestamp < 1/FPS:
           #     continue

            ret, frame_img = cap.read()
            timestamp = time.time() + latency
            if ret is True:
                if frame_img is None:
                    continue

                try:

                    start = time.time()
                    frame_ref = ray.put([FrameData(session_id, int(frame_number),timestamp), frame_img])
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

if __name__ == "__main__":
    stream_loader = StreamLoader("rtsp://admin:q1w2e3r4@51.195.44.112:554/video1")
    while True:
        frame = stream_loader.get_frame()
        if frame is not None:
            # show image
            cv.imshow('Example - Show image in window', frame.img_rgb)

            cv.waitKey(30)  # waits until a key is pressed
    cv.destroyAllWindows()  # destroys the window showing image