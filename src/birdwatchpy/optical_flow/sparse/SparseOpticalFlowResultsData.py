from dataclasses import dataclass, field
from typing import List

from birdwatchpy.optical_flow.sparse.SparseOpticalFlowData import SparseOpticalFlowData


@dataclass
class FrameData:
    session_id: int
    frame_number: int
    sparse_optical_flow_label: str

    flow: List[SparseOpticalFlowData] = field(default_factory=list)
