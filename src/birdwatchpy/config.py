from configparser import ConfigParser
from pathlib import Path
from birdwatchpy.utils import get_project_root, get_work_dir
from typing import List

configur = ConfigParser(allow_no_value=True)
print(get_work_dir() / 'config.ini')
print(get_project_root() / 'config.ini')
if (get_work_dir() / 'config.ini').is_file():
    config_file= get_work_dir() / 'config.ini'

elif (get_project_root() / 'config.ini').is_file():
    config_file= get_project_root() / 'config.ini'
else:
    raise FileNotFoundError

print(f"Using following config file: {config_file}")
configur.read(config_file)

def get_mongo_db_host():
    return configur.get('database', 'mongo_db_host')


def get_mongo_db_port():
    try:
        return configur.getint('database', 'mongo_db_port')
    except ValueError:
        return None

def get_mongo_db_user():
    return configur.get('database', 'mongo_db_user')


def get_mongo_db_pw():
    return configur.get('database', 'mongo_db_pw')

def get_yolov4_weights_path():
    return configur.get('detection', 'path_to_weights')

def get_yolov4_names_path():
    return configur.get('detection', 'path_to_names')

def get_yolov4_cfg_path():
    return configur.get('detection', 'path_to_cfg')


# General
def get_resolution() -> List[int]:
    return [int(configur.get('general', 'resolution_width')), int(configur.get('general', 'resolution_height'))]

def get_local_data_path() -> Path:
    return Path(configur.get('general', 'local_data_path'))

def get_fps() -> float:
    return float(configur.get('general', 'fps'))

def get_tmp_storage_duration() -> int:
    return int(configur.get('general', 'tmp_storage_duration'))


# sequence-of-interest-filter
def get_soi_thresh_low():
    return configur.getint('sequence-of-interest-filter', 'thresh_low')

def get_soi_thresh_high():
    return configur.getint('sequence-of-interest-filter', 'thresh_high')

# Network
def get_network_latency():
    return configur.getint('network', 'latency')