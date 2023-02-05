from dataclasses import dataclass

import numpy as np


@dataclass
class SparseOpticalFlowData:
    session_id: int
    frame_number: int
    parames: dict

    img: np.ndarray = None
