import glob
import logging
import time
from argparse import ArgumentParser
from pathlib import Path

from birdwatchpy.frames.FrameData import FrameData
from birdwatchpy.frames.frames_from_folder import load_from_darkhelp_format
from birdwatchpy.logger import get_logger
from birdwatchpy.sequences.SequenceData import SequenceData
from birdwatchpy.sequences.folder_structure import extract_info_from_sequence_pathname

logger = get_logger(log_name="sequence_from_folder", stream_logging_level=logging.DEBUG, file_handler=True,
                    filename='base.log')

def extend_sequence_with_frame_data(path: Path, sequence: SequenceData):
    # Warning! This function creates timestamps for frames based on the time of execution and not capture of the frame!
    frame_numbers = [int(Path(img_path).stem.split('-')[-1]) for img_path in
                     glob.glob(f'{path.as_posix()}/images/*.png')]
    sequence.frames = {num: FrameData(sequence.session_id, num, time.time()) for num in frame_numbers}

    return sequence


def extend_sequence_with_darknet_detection(path: Path, sequence: SequenceData) -> SequenceData:
    darknet_file = path / "yolov4_out" / "output.json"
    if not darknet_file.is_file():
        print(
            f"Warning: Darknet json detection (./yolov4_out/out.json) not found in '{path}'. Detections are not beeing loaded. ")  # ToDo: Logging or exception?
        return sequence

    for detection_frame in load_from_darkhelp_format(darknet_file, sequence.session_id):
        try:
            sequence.frames[detection_frame.frame_number].detection = detection_frame.detection
        except AttributeError as ae:
            logger.warning(f'Attribute Error: Frame Number: {detection_frame.frame_number}')

    return sequence


def create_new_sequence_from_path(path: Path, load_detections: bool = True) -> SequenceData:
    sequence_info = extract_info_from_sequence_pathname(path)
    new_sequence = SequenceData(session_id=sequence_info['session_id'],
                                from_frame_number=sequence_info['from_frame_number'],
                                to_frame_number=sequence_info['to_frame_number'])

    new_sequence = extend_sequence_with_frame_data(path, new_sequence)
    if load_detections:
        new_sequence = extend_sequence_with_darknet_detection(path, new_sequence)
    return new_sequence


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("path", help="Path to folder with sequence")
    parser.add_argument("-r", "--recursive", action='store_true', help="Recursively load from subfolders")
    parser.add_argument("-d", "--load_darknet", action='store_true', help="Load detections in darknet json format")

    args = parser.parse_args()

    if args.recursive:
        for path in Path(args.path).iterdir():
            if path.is_dir():
                create_new_sequence_from_path(path)

    else:
        create_new_sequence_from_path(Path(args.path))
