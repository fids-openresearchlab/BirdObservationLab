from dataclasses import dataclass, field
from typing import List

from birdwatchpy.detection.DetectionData import DetectionData


@dataclass
class DetectionResultsData:
    session_id: int
    frame_number: int
    object_detection_label: str

    detections: List[DetectionData] = field(default_factory=list)

#    def __init__(self, session_id: int, frame_number:int, object_detection_label: str, img: np.ndarray):
#        self.session_id = session_id
#        self.
