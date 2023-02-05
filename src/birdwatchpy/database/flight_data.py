from typing import List

import bson
from bson.raw_bson import RawBSONDocument
from bson.son import SON

from birdwatchpy.bird_flight_analysis.BirdFlightData import BirdFlightData
from birdwatchpy.database.connection import db
from birdwatchpy.database.mongo_retry import mongo_retry

flights_col = db['flights']


@mongo_retry
def insert_flight(flight_data: BirdFlightData):
    return flights_col.insert_one(RawBSONDocument(bson.BSON.encode(flight_data.as_dict())))


@mongo_retry
def insert_flights(flights: List[BirdFlightData]):
    [print(flight.as_dict()) for flight in flights]
    return flights_col.insert_many([flight.as_dict() for flight in flights])


@mongo_retry
def create_flight_filter_query_document(min_positions_count: int, max_positions_count: int, min_length: int,
                                        max_length: int, min_avg_speed: int,
                                        max_avg_speed: int,
                                        min_wing_flap_frequency: int, max_wing_flap_frequency: int, min_avg_size: int,
                                        max_avg_size: int,
                                        max_speed_deviation: int):
    return {
        "positions_count": {"$gt": min_positions_count, "$lt": max_positions_count},
        "length": {"$gt": min_length, "$lt": max_length},
        "avg_speed": {"$gt": min_avg_speed, "$lt": max_avg_speed},
        "max_speed_deviation": {"$lt": max_speed_deviation},
        # "wing_flap_frequency": {"$gt": max_wing_flap_frequency, "$lt": min_avg_size},
        "avg_size": {"$gt": min_avg_size, "$lt": max_avg_size}, }


def create_default_flights_query_document() -> dict:
    return {'positions_count': {'$gt': 15, '$lt': 1800}, 'length': {'$gt': 1000, '$lt': 12000},
            'avg_speed': {'$gt': 6, '$lt': 60}, 'max_speed_deviation': {'$lt': 500},
            'avg_size': {'$gt': 4, '$lt': 100000}}


@mongo_retry
def get_random_flight(query_document: dict):
    # ToDo: Remove limit
    return flights_col.agregate([
        {'$match': create_default_flights_query_document()},
        {'$sample': {'size': 1}}])


@mongo_retry
def get_flights_sample(query_document: dict):
    # ToDo: Remove limit
    return flights_col.find(query_document).limit(50)


@mongo_retry
def get_flights_sample_filtered_by_default_values():
    return get_flights_sample(create_default_flights_query_document())


@mongo_retry
def get_relevant_flights_from_sequence(sequence_id: str):
    filter_object = create_default_flights_query_document()
    filter_object.update({'sequence_id': sequence_id})
    return get_flights_sample(filter_object)


@mongo_retry
def get_relevant_flight_ids_from_sequence(sequence_id: str):
    filter_object = create_default_flights_query_document()
    filter_object.update({'sequence_id': sequence_id})
    return flights_col.find(filter_object, {"flight_id": 1.0, "_id": 0.0})


@mongo_retry
def get_flights_sample_count(query_document: dict) -> int:
    return flights_col.count_documents(query_document)


def get_relevant_flight_ids_grouped_by_sequence_id(min_flights_count: int, max_flights_count: int):
    pipeline = [
        {
            u"$match": create_default_flights_query_document()
        },
        {
            u"$group": {
                u"_id": {
                    u"sequence_id": u"$sequence_id"
                },
                u"flights_count": {
                    u"$count": {}
                },
                u"flights": {
                    u"$push": {
                        u"flight_id": u"$flight_id"
                    }
                }
            }
        },
        {
            u"$match": {
                u"flights_count": {
                    u"$gt": int(min_flights_count),
                    u"$lt": int(max_flights_count),

                }
            }
        },
        {
            u"$sort": SON([(u"flights_count", -1)])
        }
    ]

    return flights_col.aggregate(
        pipeline,
        allowDiskUse=True
    )
