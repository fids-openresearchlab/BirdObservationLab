import bson
import pymongo
from bson.raw_bson import RawBSONDocument

from birdwatchpy.database.connection import db
from birdwatchpy.database.mongo_retry import mongo_retry


@mongo_retry
def get_fids_audio_text_col():
    fids_text_col = db['fids_audio_text']
    fids_text_col.create_index([("timestamp", pymongo.ASCENDING)])
    return fids_text_col


fids_audio_text_col = get_fids_audio_text_col()


@mongo_retry
def insert_sentence_entry(data: dict):
    return fids_audio_text_col.insert_one(RawBSONDocument(bson.BSON.encode(data)))


@mongo_retry
def get_latest_sentence_entries(timestamp, count: int):
    return fids_audio_text_col.find({"timestamp": {"$lt": timestamp}}).sort("timestamp", -1).limit(count)
