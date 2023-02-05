"""Export Sequences

This module exports sequences

Example:
        $  python -m birdwatchpy.export.export --output /media/data/many_bird_export --list_path /mnt/fids_data/many_birds_sequence_id_list.csv

"""
import csv
from argparse import ArgumentParser
from pathlib import Path
from typing import List
from distutils.dir_util import copy_tree

from birdwatchpy.config import get_local_data_path
from birdwatchpy.sequences.sequence_from_folder import create_new_sequence_from_path


def read_sequence_id_csv(path: Path):
    with open(path, mode='r') as file:
        csvFile = csv.reader(file)

        return [line[0] for line in csvFile]

def export(sequence_ids: List[str], type: str, out_path: Path):
    if type == 'sequence_folders':
        export_as_sequence_folder(sequence_ids, out_path)
    elif type == 'video':
        export_as_video(sequence_ids, out_path)

def export_as_video(sequence_ids: List[str], out_path: Path):
    sequence_path = get_local_data_path() / 'sequences'

    sequences_without_folder = []

    for index, sequence_id in enumerate(sequence_ids):
        print(sequence_id)
        sequence_path = sequence_path / sequence_id
        if not sequence_path.exists():
            sequences_without_folder.append(sequence_id)
            continue

        sequence = create_new_sequence_from_path(sequence_path, load_detections=True)

    print(f"Sequence folder not found for {len(sequences_without_folder)} sequences.")
    print(f"Sucessfully exported {index - len(sequences_without_folder)} sequences")

def export_as_sequence_folder(sequence_ids: List[str], out_path: Path):
    sequence_path = get_local_data_path() / 'sequences'

    sequences_without_folder = []

    for index, sequence_id in enumerate(sequence_ids):
        print(sequence_id)
        origin_path = sequence_path / sequence_id
        if not origin_path.exists():
            sequences_without_folder.append(sequence_id)
            continue

        target_path = out_path / sequence_id
        target_path.mkdir(parents=True, exist_ok=True)

        print(target_path)
        print(origin_path)
        copy_tree(origin_path.as_posix(), target_path.as_posix())

    print(f"Sequence folder not found for {len(sequences_without_folder)} sequences.")
    print(f"Sucessfully exported {index - len(sequences_without_folder)} sequences")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--output", help="output path where sequences should be saved")
    parser.add_argument("--export_type", help="Export type", type=str, choices=('sequence_folders', 'video'), default='sequence_folders')
    parser.add_argument("--list_path", help="Path to a comma separated file (csv) containing sequence_ids. On each line there should be a single sequence_id.", type=str)
    args = parser.parse_args()

    output_path = Path(args.output)

    if args.list_path:
        sequence_ids = read_sequence_id_csv(Path(args.list_path))
        export(sequence_ids, args.export_type, out_path=output_path)
