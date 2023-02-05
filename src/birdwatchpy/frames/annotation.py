from typing import Tuple, Set, List

import cv2 as cv
import numpy as np

from birdwatchpy.detection.DetectionData import DetectionData
from birdwatchpy.frames.FrameData import FrameData

default_parameter = {
    "show_detections": True,
    "show_detection_score": True,
    "show_opt_flow": False,
    "add_frame_number_text": True,
    "add_session_id_text": True,
    "add_has_birds_text": True,
    "add_is_ambiguous_text": True,
}


def annotatate_frame(frame_data: FrameData, frame_img: np.ndarray, show_detections=False, show_detection_score=False,
                     show_opt_flow=False, add_session_id_text=False,
                     add_frame_number_text=False, add_has_birds_text=False, add_is_ambiguous_text=False) -> Tuple[
    Set[str], np.ndarray]:
    text_set = set()
    ann_img = frame_img.copy()

    if show_detections:
        if frame_data.detection:
            ann_img = draw_detections_in_image(ann_img, frame_data.detection["first yolo run"], show_detection_score)
    if add_session_id_text:
        text_set.add(f"Session ID: {frame_data.session_id}")
    if add_frame_number_text:
        text_set.add(f"#{frame_data.frame_number}")
    if add_has_birds_text:
        text_set.add(f"Has birds: {frame_data.has_birds}")
    if add_is_ambiguous_text:
        if frame_data.is_ambiguous:
            text_set.add(f"Ambiguous: {frame_data.is_ambiguous}")

    return text_set, ann_img


def draw_detections_in_image(img: np.ndarray, detections: List[DetectionData], draw_score: bool = True):
    img = img.copy()

    print(detections)
    for detection in detections:
        tl, br = detection.bb.to_xyxy()
        tl_x, tl_y = tl
        cv.rectangle(img, tl, br, (255, 255, 255), 1)

        if draw_score:
            text = "{}: {:.4f}".format("bird", detection.confidence)
            cv.putText(img, text, (tl_x, tl_y - 5), cv.FONT_HERSHEY_SIMPLEX,
                       0.5, (255, 255, 255), 2)

    return img
