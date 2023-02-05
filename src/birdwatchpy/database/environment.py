import bson
import pymongo
from bson.raw_bson import RawBSONDocument

from birdobs import db
from birdobs import mongo_retry


@mongo_retry
def get_weather_station_col():
    weather_station_col = db['weather_station']
    weather_station_col.create_index([("timestamp", pymongo.ASCENDING)])
    return weather_station_col


weather_station_col = get_weather_station_col()


@mongo_retry
def get_barometer_col():
    barometer_col = db['barometer']
    barometer_col.create_index([("timestamp", pymongo.ASCENDING)])
    return barometer_col


barometer_col = get_barometer_col()


@mongo_retry
def get_gps_col():
    gps_col = db['gps']
    gps_col.create_index([("timestamp", pymongo.ASCENDING)])
    return gps_col


gps_col = get_gps_col()


@mongo_retry
def get_magnetic_field_col():
    magnetic_field_col = db['magnetic_field']
    magnetic_field_col.create_index([("timestamp", pymongo.ASCENDING)])
    return magnetic_field_col


magnetic_field_col = get_magnetic_field_col()


@mongo_retry
def get_sound_pressure_alert_col():
    sound_pressure_alert_col = db['sound_pressure_alert_col']
    sound_pressure_alert_col.create_index([("timestamp", pymongo.ASCENDING)])
    return sound_pressure_alert_col


sound_pressure_alert_col = get_sound_pressure_alert_col()


@mongo_retry
def get_avg_sound_pressure_col():
    avg_sound_pressure_col = db['avg_sound_pressure_col']
    avg_sound_pressure_col.create_index([("timestamp", pymongo.ASCENDING)])
    return avg_sound_pressure_col


avg_sound_pressure_col = get_avg_sound_pressure_col()


@mongo_retry
def get_avg_illuminance_col():
    avg_illuminance_col = db['avg_illuminance_col']
    avg_illuminance_col.create_index([("timestamp", pymongo.ASCENDING)])
    return avg_illuminance_col


avg_illuminance_col = get_avg_illuminance_col()


@mongo_retry
def insert_weather_entry(data: dict):
    return weather_station_col.insert_one(RawBSONDocument(bson.BSON.encode(data)))


@mongo_retry
def insert_barometer_entry(data: dict):
    return barometer_col.insert_one(RawBSONDocument(bson.BSON.encode(data)))


@mongo_retry
def insert_gps_entry(data: dict):
    return gps_col.insert_one(RawBSONDocument(bson.BSON.encode(data)))


@mongo_retry
def insert_magnetic_field_entry(data: dict):
    return magnetic_field_col.insert_one(RawBSONDocument(bson.BSON.encode(data)))


@mongo_retry
def insert_air_pressure_alert_entry(data: dict):
    return sound_pressure_alert_col.insert_one(RawBSONDocument(bson.BSON.encode(data)))


@mongo_retry
def insert_avg_sound_pressure_entry(data: dict):
    return avg_sound_pressure_col.insert_one(RawBSONDocument(bson.BSON.encode(data)))


@mongo_retry
def insert_avg_illuminance_entry(data: dict):
    return avg_illuminance_col.insert_one(RawBSONDocument(bson.BSON.encode(data)))


@mongo_retry
def get_weather_datapoint(timestamp: float):
    return weather_station_col.find({"timestamp": {"$lt": timestamp}}, {"_id": 0.0}).sort("timestamp", -1).limit(1)


@mongo_retry
def get_gps_datapoint(timestamp: float):
    return gps_col.find({"timestamp": {"$lt": timestamp}}, {"_id": 0.0}).sort("timestamp", -1).limit(1)


@mongo_retry
def get_magnetic_field(timestamp):
    return magnetic_field_col.find({"timestamp": {"$lt": timestamp}}, {"_id": 0.0}).sort("timestamp", -1).limit(1)


@mongo_retry
def get_air_pressure_measurements(timestamp: float, window_in_sec: int):
    return barometer_col.find(
        {"timestamp": {"$gt": timestamp - window_in_sec, "$lt": timestamp}}, {"_id": 0.0}).sort(
        "timestamp",
        -1)


@mongo_retry
def get_avg_sound_pressure_measurements(timestamp: float, window_in_sec: int):
    return avg_sound_pressure_col.find(
        {"timestamp": {"$gt": timestamp - window_in_sec, "$lt": timestamp}}, {"_id": 0.0}).sort(
        "timestamp",
        -1)


@mongo_retry
def get_avg_illuminance(timestamp: float):
    return avg_illuminance_col.find(
        {"timestamp": {"$lt": timestamp}}, {"_id": 0.0}).sort("timestamp", -1).limit(1)
