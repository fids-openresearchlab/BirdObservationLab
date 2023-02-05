from typing import List

import numpy as np


def calculate_distances(points: List[List[int]]) -> np.ndarray:
    # ToDo: Faster numpy calc instead of for loop
    distances = []
    for old_point, new_point in points:
        distances.append(np.linalg.norm(np.array(old_point) - np.array(new_point)))
    return np.array(distances)
