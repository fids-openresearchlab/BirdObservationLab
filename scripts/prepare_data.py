import glob
from argparse import ArgumentParser
from pathlib import Path

import cv2

from birdwatchpy.sequences import SequenceData
from birdwatchpy.sequences import extract_info_from_filestem
from birdwatchpy.sequences import extend_sequence_with_frame_data


def prepare_folder_structure(sequence_id: str, output_path: Path) -> dict:
    sequence_folder = output_path / sequence_id
    sequence_folder.mkdir(parents=True, exist_ok=True)

    yolov4_out_folder = sequence_folder / "yolov4_out"
    yolov4_out_folder.mkdir(parents=True, exist_ok=True)

    images_folder = sequence_folder / "images"
    images_folder.mkdir(parents=True, exist_ok=True)

    return {"sequence_folder": sequence_folder, "yolov4_out_folder": yolov4_out_folder, "images_folder": images_folder}


def prepare_img_files(video_path: Path, img_folder: Path, sequence_id: str, first_frame: int, last_frame: int):
    vid_capture = cv2.VideoCapture(video_path.as_posix())

    if (vid_capture.isOpened() == False):
        print("Error opening the video file")  # ToDo: Logging

    frame_counter = first_frame
    while (vid_capture.isOpened()):
        # vid_capture.read() methods returns a tuple, first element is a bool
        # and the second is frame
        ret, frame = vid_capture.read()
        if ret == True:
            cv2.imwrite((img_folder / f"{sequence_id}-{frame_counter:07}.png").as_posix(), frame)
            frame_counter += 1

        else:
            assert (frame_counter - 1 == last_frame)
            break

    # Release the video capture object
    vid_capture.release()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("input", help="Path to folder with sequence")
    parser.add_argument("output", help="Path to folder with sequence")
    parser.add_argument("--load_sequence_json", help="Optionally load from sequence json")
    parser.add_argument("--save_sequence_json", action='store_true', help="Optionally save changes to sequence json")

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if input_path.is_dir():
        for video_path in glob.glob(f'{input_path.as_posix()}/*.avi'):  # ToDo: More formats
            video_path = Path(video_path)
            info = extract_info_from_filestem(video_path.stem)
            folder_structure = prepare_folder_structure(info["sequence_id"], output_path)
            prepare_img_files(video_path, folder_structure["images_folder"], info["sequence_id"], info["first_frame"],
                              info["last_frame"])
            if args.load_sequence_json:
                pass
                # ToDo: Implement
                # sequence = load_sequence_json(Path(args.from_sequence_json))
            else:
                sequence = SequenceData(info["session_id"], info["sequence_id"])

            if len(sequence.frames) == 0:
                extend_sequence_with_frame_data(folder_structure["sequence_folder"], sequence)
