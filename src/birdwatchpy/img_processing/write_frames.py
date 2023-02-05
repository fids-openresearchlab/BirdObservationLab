from pathlib import Path

import cv2
import numpy as np

from birdwatchpy.frames.FrameData import FrameData


def write_frame_image(img: np.ndarray, frame: FrameData, folder: str, show_detections=True):
    Path(folder).mkdir(parents=True, exist_ok=True)
    img = img.copy()
    if show_detections:
        img = draw_detections_in_image(
            img=img,
            detections=frame.detections
        )
    cv2.imwrite(f'{folder}/{frame.session_id}_{frame.frame_number}.png', img)
