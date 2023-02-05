from argparse import ArgumentParser
from pathlib import Path

from scripts.yolo_detection_controller import detection_on_img_dir
from birdwatchpy.sequences import SequenceData
from birdwatchpy.sequences import extract_info_from_filestem
from birdwatchpy.sequences import extend_sequence_with_frame_data, extend_sequence_with_darknet_detection


def processs_sequence(sequence_folder_path, detect: bool, load_sequence_json: str):
    print(sequence_folder_path)
    # Run Detection
    if detect:
        detection_on_img_dir(img_dir=sequence_folder_path / "images", engine="darknet")

    info = extract_info_from_filestem(sequence_folder_path.stem)

    if load_sequence_json:
        pass
        # ToDo: Implement
        # sequence = load_sequence_json(Path(args.from_sequence_json))
    else:
        sequence = SequenceData(info["session_id"], info["sequence_id"])

    if len(sequence.frames) == 0:
        sequence = extend_sequence_with_frame_data(sequence_folder_path, sequence)

    # Always extend the sequence with detection data
    sequence = extend_sequence_with_darknet_detection(sequence_folder_path, sequence)

    return sequence


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("input", help="Path to sequence folder")
    parser.add_argument("--detect", action='store_true', help="Run detection.")
    parser.add_argument("--load_sequence_json", help="Optionallyaction='store_true', load from sequence json")
    parser.add_argument("--save_sequence_json", help="Optionally save changes to sequence json")
    parser.add_argument("-r", "--recursive", action='store_true', help="Recursively load from subfolders")

    args = parser.parse_args()

    if args.recursive:
        for path in Path(args.input).iterdir():
            if path.is_dir():
                processs_sequence(Path(path))

    else:
        processs_sequence(Path(args.input))
