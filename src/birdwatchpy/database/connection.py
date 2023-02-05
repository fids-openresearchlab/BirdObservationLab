import logging
import time

import pymongo
from pymongo.server_api import ServerApi
from birdwatchpy.database.mongo_retry import mongo_retry
from birdwatchpy import config
from birdwatchpy.logger import get_logger

logger = get_logger(log_name="sparse_lk_cpu_worker", stream_logging_level=logging.DEBUG, file_handler=True,
                    filename='base.log')


print(config.get_mongo_db_host())

print(config.get_mongo_db_user())
print(config.get_mongo_db_pw())


@mongo_retry
def create_connection():
    return pymongo.MongoClient(config.get_mongo_db_host(),
                               port=config.get_mongo_db_port(),
                               username=config.get_mongo_db_user(),
                               password=config.get_mongo_db_pw(),
                               retryWrites=True,
                               server_api=ServerApi('1'),
                               # authSource='admin',
                               authMechanism='SCRAM-SHA-256',
                               )
db_client = create_connection()
time.sleep(4)

print("a")
print(db_client[0])
print("b")
db = db_client['fids_db']

