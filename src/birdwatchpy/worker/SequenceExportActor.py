import asyncio
import traceback
import uuid
from asyncio import ALL_COMPLETED
from queue import Queue

from shutil import move, rmtree
import logging
import ray

import cv2 as cv

from birdwatchpy.config import get_resolution, get_fps, get_local_data_path
from birdwatchpy.logger import get_logger
from birdwatchpy.sequences.SequenceData import SequenceData


CHECK_QUEUE_INTERVAL = 5

@ray.remote
class SequenceExportActor(object):
    def __init__(self):
        self.logger = get_logger(log_name="export_sequence_worker", stream_logging_level=logging.DEBUG, file_handler=True,
                            filename='SequenceExportActor.log')
        self.logger.debug(f"export_sequence_worker: Start")

        self.queue = Queue()
        self.tasks = []

        self.tmp_sequence_name = str(uuid.uuid4())
        self.frames: dict = {}

        self.resolution = get_resolution()
        self.fps = get_fps()
        local_data_path = get_local_data_path()
        self.logger.info(f"SequenceExportActor: local_data_path :{local_data_path}")

        self.tmp_sequence_dir_path = local_data_path / "sequences" /  self.tmp_sequence_name
        self.tmp_sequence_dir_path.mkdir(parents=True, exist_ok=True)
        self.image_dir = self.tmp_sequence_dir_path / "images"
        self.image_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"SequenceExportActor: tmp_sequence_dir_path :{self.tmp_sequence_dir_path}")

        #self.video_out = cv.VideoWriter(f"{(self.tmp_sequence_dir_path / 'video.mp4').as_posix()}",
        #                     cv.VideoWriter_fourcc('H', '2', '6', '5'), self.fps,
        #                     self.resolution)


    async def add_frame(self, frame_w_img):
        try:
            self.logger.info(f"SequenceExportActor:Add frame to SequenceExportActor :{self.tmp_sequence_dir_path}")
            frame, img = frame_w_img
            self.frames.update({frame.frame_number: frame})
            self.tasks.append(asyncio.create_task(self.write_image(frame.frame_number, img)))
        except Exception as e:
            self.logger.error(
                f"sparse_lk_cpu_task: Unhandled exception in thread. Exception: {e} Traceback: {traceback.print_exc()}")

    async def write_image(self, frame_number, img_rgb):
        cv.imwrite(f"{self.image_dir.as_posix()}/{self.tmp_sequence_name}-{frame_number}.png", img_rgb)

    async def close_and_rename(self, args):
        from birdwatchpy.worker.detection_and_tracking_task import detection_and_tracking_task
        try:
            await asyncio.wait(self.tasks, return_when=ALL_COMPLETED)

            first_sequence_frame, last_sequence_name = args
            session_id = (list(self.frames.values())[0]).session_id
            sequence=SequenceData(session_id, first_sequence_frame, last_sequence_name)
            sequence.frames = self.frames

            sequence_path = self.tmp_sequence_dir_path.parent / sequence.sequence_id
            sequence_path.mkdir(parents=True, exist_ok=True)

            new_image_folder = sequence_path / "images"
            new_image_folder.mkdir(parents=True, exist_ok=True)


            self.logger.info(f"SequenceExportActor: New Sequence path: {sequence_path} :{self.tmp_sequence_dir_path}")


            for frame_number in self.frames:
                old_path = self.image_dir / f"{self.tmp_sequence_name}-{frame_number}.png"
                new_path = new_image_folder / f"{sequence.sequence_id}-{frame_number}.png"
                move(old_path, new_path)

            #os.rename(f, new_name)
            rmtree(self.tmp_sequence_dir_path)

            ray.wait([detection_and_tracking_task.remote(ray.put((sequence_path, sequence)))])
        except Exception as e:
            self.logger.error(
                f"sparse_lk_cpu_task: Unhandled exception in thread. Exception: {e} Traceback: {traceback.print_exc()}")

        ray.actor.exit_actor()

