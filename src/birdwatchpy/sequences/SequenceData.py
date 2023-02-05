from copy import deepcopy
from dataclasses import dataclass, field
from typing import List

from birdwatchpy.bird_flight_analysis.BirdFlightData import BirdFlightData


@dataclass
class SequenceData:
    session_id: int
    from_frame_number: int
    to_frame_number: int
    has_birds: bool = None
    is_ambiguous: bool = None

    # frame_numbers: List[int] = field(default_factory=list) # ToDo: Remove as it is depricated?
    frames: dict = field(default_factory=dict)
    birds: List[BirdFlightData] = field(default_factory=list)

    def __post_init__(self):
        self.sequence_id = f"{self.session_id}_{self.from_frame_number:07d}_{self.to_frame_number:07d}"

    def as_dict(self) -> dict:
        sequence_data_dict = deepcopy(self)
        sequence_data_dict.frames = {str(frame_num): frame_data.as_dict() for frame_num, frame_data in sequence_data_dict.frames.items()}
        sequence_data_dict.birds= list(map(lambda flight_data: flight_data.as_dict(), self.birds ))
        return sequence_data_dict.__dict__