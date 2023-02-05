import functools
import os
import time
from pathlib import Path
from typing import List

import cv2
import numpy as np
from numpy import ndarray


@functools.lru_cache(maxsize=None)
def find_path_to_video(session_id: int, footage_path: Path) -> Path:
    return list(footage_path.glob(f"**/{session_id}.*"))[0]


def extract_frame_from_video(session_id: int, frame_number: int) -> ndarray:
    path = find_path_to_video(session_id, Path(os.environ["FIDS_FOOTAGE_PATH"]))
    start = time.time()
    cap = cv2.VideoCapture(path.as_posix())
    cap.set(1, int(frame_number))
    ret, img = cap.read()
    print(f"Frame extraction took {time.time() - start} Session ID: {session_id} Frame Number: {frame_number}")
    return img

def extract_frames_from_sequence_folder(sequence_path: Path) -> np.ndarray:
    """

    Args:
        sequence_id (str): Id of the sequence

    Yields:
        frame_img (numpy.ndarray): The next image of the sequence

    """
    sequence_img_path = sequence_path / 'images'
    print(sequence_img_path)
    for frame_path in sorted(list(sequence_img_path.glob('*.png')) + list(sequence_img_path.glob('*.jpg'))):
        print(frame_path)
        yield cv2.imread(frame_path.as_posix())


def extract_consecutive_frames(from_num: int, to_num: int, session_id: int):
    path = find_path_to_video(session_id, Path(os.environ["FIDS_FOOTAGE_PATH"]))
    start = time.time()
    cap = cv2.VideoCapture(path.as_posix())
    cap.set(1, int(from_num))
    # frame_number= from_num
    for i in range(from_num, to_num):
        ret, img = cap.read()
        if img is None:
            return
        print(f"Frame extraction took {time.time() - start} Session ID: {session_id} Frame Number: ")
        yield img


def extract_multiple_frames_from_video_as_dict(session_id: int, frame_numbers: List[int]) -> dict:
    return {frame_number: extract_frame_from_video(session_id, frame_number) for frame_number in frame_numbers}
