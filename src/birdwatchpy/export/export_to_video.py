"""Export Sequences as video files

This module exports sequence as videos

Example:
        $  python -m birdwatchpy.export.export_to_video --sequence-folder-path /mnt/fids_data/local_data/sequences --fps 29.97 /home/jo/fids/local_data/exported_sequence_videos  /mnt/fids_data/many_birds_sequence_id_list.csv

"""

from argparse import ArgumentParser
from pathlib import Path
import cv2

from birdwatchpy.export.export import read_sequence_id_csv
from birdwatchpy.frames import extract_frames_from_sequence_folder
from birdwatchpy.config import get_local_data_path


def export_video(sequence_id: str, sequence_path: Path, out_path: Path, fps: float = 30):
    """
    Creates a video for a sequence

    Args:
        sequence_id (str): Id of the sequence
        sequence_path (Path): Path to the sequence folder
        out_path: Path where to save the created videos
        fps: Frames per second of the output video

    Returns:

    """
    print(out_path.as_posix())
    format = "mp4"
    out = None
    for frame_img in extract_frames_from_sequence_folder(sequence_path):
        if out is None:
            dimension = tuple(reversed(frame_img.shape[:2]))
            print(dimension)
            out = cv2.VideoWriter(f"{out_path.as_posix()}/{sequence_id}.{format}", cv2.VideoWriter_fourcc(*'H264'), fps, dimension)
        #if dimension != frame_img.size:
        #    frame_img = cv2.resize(frame_img, dimension, interpolation=cv2.INTER_AREA)
        out.write(frame_img)
    try:
        out.release()
    except AttributeError:
        print(f"No image files found in {sequence_path}")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("output", help="output path where sequences should be saved")
    parser.add_argument("list_path", help="Path to a comma separated file (csv) containing sequence_ids. On each line there should be a single sequence_id.", type=str)
    parser.add_argument("--sequence-folder-path", help="Path containing sequence folders.", type=str)
    parser.add_argument("--fps", help="Frames per second of the output video", type=float)

    args = parser.parse_args()

    output_path = Path(args.output)

    if args.list_path:
        sequence_ids = read_sequence_id_csv(Path(args.list_path))
        for sequence_id in sequence_ids:
            if args.sequence_folder_path is None:
                sequence_path = get_local_data_path() / 'sequences' / sequence_id
            else:
                sequence_path = Path(args.sequence_folder_path) / sequence_id
            export_video(sequence_id, sequence_path, out_path=output_path, fps = args.fps)
