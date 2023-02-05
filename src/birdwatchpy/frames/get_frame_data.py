from pathlib import Path

import cv2

from birdwatchpy.frames.FrameData import FrameData


def create_frame_data_obj_from_folder_gen(file_path_generator):
    for files in file_path_generator:
        session_id, frame_number = str(files.stem).split("_")

        yield FrameData(int(session_id), int(frame_number))


def create_frame_data_obj_from_video_file_gen(video_file_path: Path):  # ToDo: Remove in favour of Video Loaders
    cap = cv2.VideoCapture(str(video_file_path))
    session_id = str(video_file_path.stem)

    frame_number = 0
    while (cap.isOpened()):
        frame_number += 1
        ret, frame = cap.read()

        if ret == True:
            yield frame, FrameData(int(session_id), int(frame_number))

        else:
            break
    cap.release()
