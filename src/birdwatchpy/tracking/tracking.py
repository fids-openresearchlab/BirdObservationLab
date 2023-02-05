import logging
from argparse import ArgumentParser
from glob import glob
from pathlib import Path
from typing import List, Sequence

import motpy
import numpy as np
from imgaug.augmentables import bbs
from motpy import MultiObjectTracker
from yupi import Trajectory

from birdwatchpy.bird_flight_analysis.BirdFlightData import BirdFlightData
from birdwatchpy.config import get_fps
from birdwatchpy.logger import get_logger
from birdwatchpy.frames.FrameData import FrameData
from birdwatchpy.sequences.SequenceData import SequenceData
from birdwatchpy.sequences.folder_structure import extract_info_from_filestem
from birdwatchpy.sequences.sequences_helper import load_sequence_from_pickle, save_sequence_as_pickle
from birdwatchpy.utils import get_project_root
from birdwatchpy.sequences.sequence_from_folder import create_new_sequence_from_path

logger = get_logger(log_name="motpy tracker", stream_logging_level=logging.DEBUG, file_handler=True,
                    log_file_path=(get_project_root() / "logs" / "base.log").as_posix())

fps = get_fps()


def tracking_on_sequence(sequence: SequenceData) -> SequenceData:
    tracker = MultiObjectTracker(dt=1 / fps,
                             matching_fn_kwargs={'min_iou': 0.0000000001},
                              #                   'multi_match_min_iou': 0.000000005},
                             tracker_kwargs={'max_staleness': 30},
                             active_tracks_kwargs={'min_steps_alive': 6, 'max_staleness': 30},
                             )

    frames = list(sequence.frames.values())
    frames.sort(key=lambda frame_data: frame_data.frame_number)
    motpy_tracks = tracking_on_multiple_frames(tracker, frames)
    bird_flights = motpy_to_BirdFlightData(sequence.sequence_id,  motpy_tracks)
    logger.info(f"Count Bird Flight Detected: {len(bird_flights)}")
    for bird_flight in bird_flights:
        sequence.birds.append(bird_flight)

    return sequence

def tracking_on_sequence_path(sequence_path: Path, load_existing_sequence:bool =False, save_sequence:bool = True):
    sequence_info = extract_info_from_filestem(sequence_path.stem)
    (sequence_path / "trajectories").mkdir(exist_ok=True)
    flight_data_dir = sequence_path / "flight_data"
    flight_data_dir.mkdir(exist_ok=True)

    if not Path(sequence_path / "yolov4_out" / "output.json").is_file():  # ToDo: Handle
        return

    print(sequence_path)
    sequence_filepath = sequence_path / f"{sequence_info['sequence_id']}.sequence"
    if sequence_filepath.is_file() and load_existing_sequence:
        logger.info(f"Saved sequence found. Loading SequenceData. {sequence_filepath}")
        sequence: SequenceData = load_sequence_from_pickle(sequence_filepath)
    else:
        logger.info(f"No saved sequence found or 'load_existing_sequence' is disabled. Creating new SequenceData. {sequence_filepath}")
        sequence = create_new_sequence_from_path(sequence_path)

    tracking_on_sequence(sequence)



    if save_sequence:
        save_sequence_as_pickle(sequence_filepath.parent, sequence)


def tracking_on_multiple_frames(tracker: MultiObjectTracker, frames: Sequence[FrameData], fps=30, bb_scale=0.05):
    tracks = {}
    frame_counter = 0
    time_delta = 1 / 30
    for frame_data in frames:
        frame_counter += 1
        points = []
        confidences = []
        class_ids = []
        for det in frame_data.detection:
            # Scale bounding boxes. This allows to decrease id switches due to IoU comparison.
            extend_length_half = det.bb.width * bb_scale  # ToDo: Decide what to use
            extend_height_half = det.bb.height * bb_scale
            bb = bbs.BoundingBox(det.bb.tl[0], det.bb.tl[1], det.bb.br[0], det.bb.br[1])
            assert (bb.x1 == det.bb.tl[0])
            bb_extended = bb.extend(all_sides=extend_length_half)
            assert (bb != bb_extended)
            points.append((bb_extended.x1, bb_extended.y1, bb_extended.x2, bb_extended.y2))
            confidences.append(det.confidence)
            class_ids.append(det.class_id)

        # Run Tracking
        motpy_detections=[motpy.core.Detection(points, confidence, class_id) for points, confidence, class_id in
                          zip(points, confidences, class_ids)]
        tracking_result = tracker.step(motpy_detections)

        if len(tracking_result) == 0:
            continue
        for t in tracking_result:
            bb_track = bbs.BoundingBox(t.box[0], t.box[1], t.box[2], t.box[3], )
            # Decrease bb sizes only if previous detections where enlarged
            bb_final = bb_track.extend(all_sides=-extend_length_half) if len(frame_data.detection) > 0 else bb_track

            # ToDo: Bad implementation. Necessary because tracking returns negative bb positions
            # if bb_track.center_x < 0 and bb_final.center_x < 0:
            #    print('No bounding box after elimination of bb with negative positions!')
            #    continue

            # if len(bb_arrays) == 0:
            #    raise ValueError('No bounding box after elimination of bb with negative positions!')

            if t.id not in tracks:
                tracks[t.id] = {"points": [], "t": [], "bb": [], "frame_numbers":[],"start_frame": frame_counter}

            #print(tracks)
            #print((bb_track.x1, bb_track.y1, bb_track.x2, bb_track.y2))

            tracks[t.id]["points"].append((bb_final.center_x, bb_final.center_y))
            tracks[t.id]["frame_numbers"].append(frame_data.frame_number)
            tracks[t.id]["bb"].append(np.array((bb_track.x1, bb_track.y1, bb_track.x2, bb_track.y2)))
            # tracks[t.id]["t"].append((frame_counter-1) * time_delta)

    return tracks


def motpy_to_BirdFlightData(sequence_id, tracks) -> List[BirdFlightData]:
    trajs = []
    bird_flights = []
    for track_id, track in tracks.items():
        trajs.append(
            Trajectory(traj_id=track_id, points=track["points"], t0=tracks[track_id]["start_frame"]))
        # , t=track["t"], dt = None))
        # trajectories[-1].dt = None

        # Filter out trajectories with less than 10 positions
        if len(track["bb"]) > 10:
            bird_flights.append(BirdFlightData(track_id, sequence_id, frame_numbers=track["frame_numbers"], bb_arrays=track["bb"]))

    return bird_flights


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("--track_thresh", default="0.01", help="track_thresh")
    parser.add_argument("--track_buffer", default="det.txt", help="Path to folder with img files")
    parser.add_argument("--load_existing_sequence", action='store_true', help="Load existing sequence data if available")
    parser.add_argument("--cpus", default = 1, help="Number of CPU cores to use for parallel computing", type=int)
    parser.add_argument("--recursive", action='store_true', help="Recursively apply tracking to subfolders")
    parser.add_argument("path", default="det.txt",
                        help="Path to folder")  # ToDo: Differentiate between single file and recursive folder
    args = parser.parse_args()

    if args.recursive:
        #with ThreadPoolExecutor(max_workers=16) as cpu_worker_pool:
        for dir in glob(args.path + "/*/yolov4_out", recursive=False):
            sequence_path = Path(dir).parent
            tracking_on_sequence_path(sequence_path, args.load_existing_sequence, save_sequence = True)
            #cpu_worker_pool.submit(tracking_on_sequence_path,sequence_path,args.load_existing_sequence, save_sequence=True)

            # for track_id, track in yupi_trajs:
            #    with open(f'{flight_data_dir}/{track_id}.json', 'w', encoding='utf-8') as f:
            #        try:
            #            json.dump(BirdFlightData(flight_id=track_id, bb_arrays=track["bb"]).as_dict(), f,
            #                      ensure_ascii=False)
            #        except ValueError:
            #            print("FlightData rejected because of ValueError")
            #    BirdFlightData.load(f'{flight_data_dir}/{track_id}.json')

            # ToDo: Depricated? Remove if not needed
            # plot_2D(trajs, legend=False)
            # Trajectory.save_trajectories(trajs, (Path(dir).parent / "trajectories").as_posix())

        print("All jobs completed")
    else:
        sequence_path = Path(args.path)
        tracking_on_sequence_path(sequence_path, args.load_existing_sequence, save_sequence=True)
