from argparse import ArgumentParser
from copy import deepcopy
from pathlib import Path
from typing import List

import bson
from bson.raw_bson import RawBSONDocument

from birdwatchpy.database.connection import db
from birdwatchpy.database.flight_data import insert_flights
from birdwatchpy.database.mongo_retry import mongo_retry
from birdwatchpy.sequences.SequenceData import SequenceData
from birdwatchpy.sequences.sequences_helper import SequenceDataFactory, load_sequence_from_pickle

sequences_col = db['sequences']


@mongo_retry
def get_all_sequences() -> List:
    return list(sequences_col.find({}))


@mongo_retry
def get_sequence_by_id(sequence_id):
    return sequences_col.find({"sequence_id": sequence_id})


@mongo_retry
def insert_sequence(sequence: SequenceData):
    sequence = deepcopy(sequence)
    if len(sequence.birds) > 0:
        insert_flights(sequence.birds)
    else:
        print("No birds in sequence")
    sequence.birds = []
    print("deepcopy(sequence).as_dict()")
    print(deepcopy(sequence).as_dict())
    return sequences_col.insert_one(RawBSONDocument(bson.BSON.encode(sequence.as_dict())))


@mongo_retry
def upsert_sequence(sequence: SequenceData):
    sequences_col.update_one({"sequence_id": sequence.sequence_id}, {'$set': sequence.as_dict}, upsert=True)


@mongo_retry
def get_sequences_with_birds(step: int = None, step_size: int = None) -> List[SequenceData]:
    query = {}
    query["is_ambiguous"] = True

    if step == None or step_size == None:
        return [SequenceDataFactory(seq) for seq in sequences_col.find(query)]
    else:
        return [SequenceDataFactory(seq) for seq in sequences_col.find(query).skip(step).limit(step_size)]


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-r", "--recursive", action='store_true', help="Recursively load from subfolders")
    parser.add_argument("path", help="Input Path")

    args = parser.parse_args()

    if args.recursive:
        for path in Path(args.path).iterdir():
            if path.is_dir():
                sequence_file_path = Path(f"{path}/{Path(path).name}.sequence")
                if not sequence_file_path.is_file():
                    print("Sequence file not found!")  # ToDo: Logging
                    continue

                sequence = load_sequence_from_pickle(sequence_file_path)
                insert_sequence(sequence)
                # write_plain_video(path, sequence)

    else:
        sequence_file_path = Path(f"{args.path}/{Path(args.path).name}.sequence")
        sequence = load_sequence_from_pickle(sequence_file_path)
        upsert_sequence(sequence)
