# -*- coding: utf-8 -*-
"""Export Sequences with many Birds.

This module searches the database for sequences with a minimum of birds specified as argument and copies the sequences
folder to an outpout folder specified in the ouput argument.

Example:
        $  python -m birdwatchpy.export.export_sequences_with_many_birds -output /media/data/many_bird_export -limit 50 -min_flights_count 8 -max_flights_count 20

"""
import random
from argparse import ArgumentParser
from pathlib import Path

from birdwatchpy.database import get_relevant_flight_ids_grouped_by_sequence_id
from birdwatchpy.export.export import export

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-output", help="output path where sequences should be saved")
    parser.add_argument("-min_flights_count", type=int, help="Number of minimum number of birds in sequence")
    parser.add_argument("-max_flights_count", type=int, help="Number of maximum number of birds in sequence")
    parser.add_argument("-limit", type=int, default=500, help="Maximum number of sequences")
    parser.add_argument("--export_type", help="Export type", type=str, choices=('sequence_folders', 'video'), default='sequence_folders')
    args = parser.parse_args()

    output_path = Path(args.output)
    min_flights_count = args.min_flights_count
    max_flights_count = args.max_flights_count


    sequence_ids = [it['_id']['sequence_id'] for it in get_relevant_flight_ids_grouped_by_sequence_id(min_flights_count, max_flights_count)]
    print(f"Number of Sequences with at least {min_flights_count} birds: {len(sequence_ids)}")

    sample_size = len(sequence_ids) if len(sequence_ids) < args.limit else args.limit
    sample = random.sample(sequence_ids, sample_size)

    export(sample, args.export_type, output_path)