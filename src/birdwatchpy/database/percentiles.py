import bson
import numpy as np
import pymongo
from bson.raw_bson import RawBSONDocument

from birdwatchpy.bird_flight_analysis.BirdFlightData import BirdFlightData
from birdwatchpy.database.flight_data import get_flights_sample_filtered_by_default_values
from birdwatchpy.database.mongo_retry import mongo_retry

percentiles = [v for v in range(0, 101, 5)]

from birdwatchpy.database.connection import db

percentiles_col = db['fids_percentiles']
percentiles_col.create_index([("timestamp", pymongo.ASCENDING)])


@mongo_retry
def update_percentiles_col():
    percentiles = get_percentiles()
    percentiles_col.find_one_and_delete({})
    return percentiles_col.insert_one(RawBSONDocument(bson.BSON.encode(percentiles)))


@mongo_retry
def get_latest_percentile_dict():
    return next(percentiles_col.find())


@mongo_retry
def get_percentiles():
    flights_sample = [BirdFlightData.load_from_dict(flight_dict) for flight_dict in
                      get_flights_sample_filtered_by_default_values()]

    percentiles_data_dict = {
        "Avg. Speed": {
            'data': list(map(lambda flight: int(flight.avg_speed), flights_sample)),
            'percentile_res': None},
        "Avg. Size": {
            'data': list(map(lambda flight: int(flight.avg_size), flights_sample)),
            'percentile_res': None},
        "Length": {
            'data': list(map(lambda flight: int(flight.length), flights_sample)),
            'percentile_res': None},
        "wing_flap_frequency": {
            'data': list(map(lambda flight: float(flight.wing_flap_frequency), flights_sample)),
            'percentile_res': None},
    }

    for key, values in percentiles_data_dict.items():
        percentiles_data_dict[key]['percentile_res'] = {str(perc): round(np.percentile(values['data'], perc), 9) for
                                                        perc in percentiles}

    return percentiles_data_dict


if __name__ == "__main__":
    update_percentiles_col()
    print(get_latest_percentile_dict())
