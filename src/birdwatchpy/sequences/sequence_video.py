import logging
from argparse import ArgumentParser
from pathlib import Path
import cv2 as cv
from birdwatchpy.logger import get_logger

from birdwatchpy.sequences.sequences_helper import load_sequence_from_pickle
from sequences.SequenceData import SequenceData
from utils import get_project_root

logger = get_logger(log_name="export_sequence_worker", stream_logging_level=logging.DEBUG, file_handler=True,
                    log_file_path=(get_project_root() / "logs" / "base.log").as_posix())

def write_plain_video(sequence_dir:Path, sequence: SequenceData):
    webm_out = None

    for frame_num, frame_data in sequence.frames.items():
        img = cv.imread(f"{sequence_dir}/images/{sequence.sequence_id}-{frame_num}.png") # ToDo: Prettieer project-wide solution
        if webm_out is None:
            video_path = f"{(sequence_dir / sequence.sequence_id).as_posix()}.webm"
            resolution = tuple(reversed(img.shape[:2]))
            webm_out = cv.VideoWriter(video_path,
                                      cv.VideoWriter_fourcc(*'VP90'), 30,
                                      resolution)
        webm_out.write(img)
    logger.info(f"Video file written. {video_path}")
    webm_out.release()

def convert_to_webm(filepath: Path):
    print(f"/usr/bin/HandBrakeCLI -i {filepath} -e vp9 -o {filepath.parent / filepath.stem}.webm")
   # print(["HandBrakeCLI","-i",filepath,"-e","VP9","-e",f"{filepath.parent / filepath.stem}.webm"])
    #result = subprocess.Popen(
    #    ["HandBrakeCLI","-i",filepath,"-e","VP9","-e",f"{filepath.parent / filepath.stem}.webm"], # ToDo: Path to HandBrakeCLI hardcoded
    #    #shell=True, # ToDo: Carefull! Security issue!
    #    )
    #print(result)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-r", "--recursive", action='store_true', help="Recursively load from subfolders")
    parser.add_argument("path", help="Input Path")

    args = parser.parse_args()

    # Prepare Notebook
    # prepare_notebook_for_papermill(template_notebook_path)

    if args.recursive:
        for path in Path(args.path).iterdir():
            if path.is_dir():
                sequence_file_path = Path(f"{path}/{Path(path).name}.sequence")
                if not sequence_file_path.is_file():
                    print("Sequence file not found!")  # ToDo: Logging
                    continue

                video_file = Path(f"{path}/{Path(path).name}.avi")
                if video_file.is_file():
                    print("Avi Video Found: Converting to webm")  # ToDo: Logging
                    convert_to_webm(video_file)
                sequence = load_sequence_from_pickle(sequence_file_path)

                #write_plain_video(path, sequence)

    else:
        sequence_file_path = Path(f"{args.path}/{Path(args.path).name}.sequence")
        sequence = load_sequence_from_pickle(sequence_file_path)
        write_plain_video(sequence_file_path.parent, sequence)
