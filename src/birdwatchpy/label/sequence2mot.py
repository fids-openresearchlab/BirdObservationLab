# -*- coding: utf-8 -*-
"""Export Sequences to MOT Challange format.

This module saves sequences in the MOT Challange format.

Example:
        $  python -m birdwatchpy.label.sequence2mot -out_path /mnt/fids_data/many_bird_export2/MOT -path /mnt/fids_data/many_bird_export2/sequence_selection -r --num_cpus 16
        #ToDo: Change path in doc
"""
from argparse import ArgumentParser
from pathlib import Path
import ray

from birdwatchpy.sequences.sequence_from_folder import create_new_sequence_from_path
from birdwatchpy.label.format_conversion import save_mot_det
from birdwatchpy.sequences.SequenceData import SequenceData

@ray.remote
def sequence2MOT_det(sequence: SequenceData, path, out_path:Path):
    save_mot_det(sequence.sequence_id, list(sequence.frames.values()), path, out_path)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-out_path", help="output path where sequences should be saved")
    #list_input_group = parser.add_argument_group('group1', 'Load sequence from database or API.')
    #list_input_group.add_argument('foo', help='foo help')
    parser.add_argument("-path", help="Path to folder with sequence")
    parser.add_argument("-r", "--recursive", action='store_true', help="Recursively load from subfolders")
    parser.add_argument("-c", "--num_cpus", help="Specifies how many CPU cores should be used")
    #parser.add_argument("-d", "--load_darknet", action='store_true', help="Load detections in darknet json format")

    args = parser.parse_args()

    ray.init(num_cpus=int(args.num_cpus))
    ray_tasks = []

    if args.recursive:
        for path in Path(args.path).iterdir():
            print(path)
            if path.is_dir():
                sequence = create_new_sequence_from_path(path)
                ray_tasks.append(sequence2MOT_det.remote(sequence, path, Path(args.out_path)))

        while True:
            waiting_tasks, ray_tasks = ray.wait(ray_tasks, num_returns = 1)
            print("Task returned")
            if len(waiting_tasks) == 0:
                break

    else:
        create_new_sequence_from_path(Path(args.path))