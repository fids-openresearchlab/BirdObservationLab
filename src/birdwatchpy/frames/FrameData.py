from dataclasses import dataclass, field
from functools import total_ordering
from typing import List, Optional

import numpy as np

from birdwatchpy.detection.DetectionData import DetectionData
from birdwatchpy.optical_flow.sparse.SparseOpticalFlowData import SparseOpticalFlowData


@total_ordering
@dataclass()
class FrameData:
    session_id: str
    frame_number: int
    timestamp: float
    gt_bboxes: List[DetectionData] = field(default_factory=list)
    detection: List[DetectionData] = field(default_factory=list)
    sparse_opt_flow: List[SparseOpticalFlowData] = field(default_factory=list)
    has_birds: bool = None
    is_ambiguous: bool = None

    img_rgb: Optional[np.ndarray] = None
    img_grey: Optional[np.ndarray] = None

    def __lt__(self, other):
        return self.frame_number < other.frame_number

    def as_dict(self) -> dict:
        frame_dict = self.__dict__
        frame_dict["detection"] = list(map(lambda detection: detection.as_dict(), frame_dict["detection"]))
        frame_dict["sparse_opt_flow"] = list(
            map(lambda sparse_opt_flow: sparse_opt_flow.as_dict(), frame_dict["sparse_opt_flow"]))
        frame_dict['img_rgb'] = None
        frame_dict['img_grey'] = None

        print(frame_dict)

        return frame_dict
