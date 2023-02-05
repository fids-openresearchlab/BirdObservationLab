from pathlib import Path
from typing import Generator, Tuple

from birdwatchpy.database import get_consecutive_frames_by_session_and_frame_number_gen
from birdwatchpy.database.sequences_db import get_sequences_with_birds
from birdwatchpy.frames.annotation import annotatate_frame
from birdwatchpy.frames.frame_extractor import extract_consecutive_frames
from birdwatchpy.sequences.SequenceData import SequenceData


def to_video(sequence: SequenceData, out_path: Path, dimension: Tuple[int, int]):
    write_video_gen: Generator = write_to_video(out_path / f"{sequence.sequence_id}", fps=29.95, dimension=dimension)
    extract_frame_gen: Generator = extract_consecutive_frames(min(sequence.frame_numbers),
                                                              max(sequence.frame_numbers),
                                                              sequence.session_id)
    get_frame_data_gen: Generator = get_consecutive_frames_by_session_and_frame_number_gen(sequence.session_id,
                                                                                           min(sequence.frame_numbers),
                                                                                           max(sequence.frame_numbers))
    next(write_video_gen)
    for frame_data, frame_img in zip(get_frame_data_gen, extract_frame_gen):
        text_set, frame_img = annotatate_frame(frame_data, frame_img, show_detections=True, add_session_id_text=True,
                                               add_has_birds_text=True, show_detection_score=True)
        write_video_gen.send(frame_img)
    try:
        write_video_gen.send(None)
    except StopIteration:
        return


def export_sequences_with_birds(out_path: Path, dimension: Tuple[int, int], export_video: bool = True,
                                to_images: bool = False):
    # ToDo: Is this still needed?
    """"""
    step = 0
    while True:
        sequences = get_sequences_with_birds(step, step_size=10)
        if not sequences:
            break

        for sequence in sequences:
            if export_video:
                to_video(sequence, out_path, dimension)

        step += 1


if __name__ == "__main__":
    export_sequences_with_birds(Path("/home/kubus/Downloads"), (3840, 2160), export_video=True)
