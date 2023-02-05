from typing import Tuple

import cv2
import numpy as np

color = np.random.randint(0, 255, (300, 3))


def simple_lines_draw(good_old: Tuple, good_new: Tuple, frame) -> np.ndarray:
    # draw the tracks
    for i, (new, old) in enumerate(zip(good_new, good_old)):
        a, b = new
        c, d = old
        frame = cv2.line(frame, (a, b), (c, d), color[i].tolist(), 2)
        frame = cv2.circle(frame, (a, b), 5, color[i].tolist(), 2)

    return frame
