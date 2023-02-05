import json
import pickle
from pathlib import Path

from birdwatchpy.sequences.SequenceData import SequenceData


def sequence_to_dict(sequence: SequenceData):
    pass


def save_sequence_as_pickle(path: Path, sequence: SequenceData):
    """
    Saves SequenceData as pickle. Be aware of security risks using pickle!
    """
    for key, frame_data in sequence.frames.items():  # ToDo: Ugly. Is it really necessary to save img data in frame?
        if hasattr(frame_data, 'img_rgb') and frame_data.img_rgb is not None:
            frame_data.img_rgb = None
        if hasattr(frame_data, 'img_grex') and  frame_data.img_grey is not None:
            frame_data.img_grey = None

    with open(f"{path}/{sequence.sequence_id}.sequence", 'wb') as fh:
        pickle.dump(sequence, fh)


def load_sequence_from_pickle(path: Path) -> SequenceData:
    """
    Load SequenceData from pickle. Be aware of security risks using pickle!
    """
    sequence_pickle = open(path.as_posix(), "rb")
    return pickle.load(sequence_pickle)


def save_sequence(sequence: SequenceData, path: Path):
    with open(f'{path.as_posix()}.json', 'w', encoding='utf-8') as f:
        try:
            json.dump(sequence_to_dict(sequence), f, ensure_ascii=False)
        except ValueError:
            print("FlightData rejected because of ValueError")


def SequenceDataFactory(d: dict):
    d.pop("_id", None)
    return SequenceData(**d)

#    tracks: List[TrackData] = field(default_factory=list)
