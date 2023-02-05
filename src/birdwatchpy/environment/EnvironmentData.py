import logging
import traceback
from copy import deepcopy
from datetime import datetime
from typing import List, Dict

from birdwatchpy.database.environment import get_weather_datapoint, get_air_pressure_measurements, \
    get_avg_sound_pressure_measurements, get_avg_illuminance, get_magnetic_field, get_gps_datapoint
from birdwatchpy.environment.astral_info import get_astral_info
from birdwatchpy.utils.polar.conversion import cart2pol
from birdwatchpy.logger import get_logger

logger = get_logger(log_name="StreamReceiver", stream_logging_level=logging.DEBUG, file_handler=True,
                    filename='base.log')


class EnvironmentData:
    def __init__(self, timestamp: datetime, position: dict, temperature: float, humidity: float, wind_speed: float,
                 gust_speed: float,
                 wind_direction: str, magnetic_field: Dict,
                 avg_illuminance: float, air_pressure_measurements: List[tuple[datetime, float]],
                 avg_sound_pressure_measurements: List[tuple[datetime, float]]):
        self.datetime = datetime.fromtimestamp(timestamp)
        self.position = position
        self.temperature = temperature
        self.humidity = humidity
        self.wind_speed = wind_speed
        self.gust_speed = gust_speed
        self.wind_direction = wind_direction
        self.avg_illuminance = avg_illuminance  # [] ToDo: implement lx
        self.magnetic_field = magnetic_field

        self.air_pressure_measurements = air_pressure_measurements
        self.avg_sound_pressure_measurements = avg_sound_pressure_measurements

        self.astral_info = get_astral_info(self.datetime, longitude=position['longitude'],
                                           latitude=position['latitude'])

    def get_north_angle(self):
        north_angle, _ = cart2pol(self.magnetic_field["x"], self.magnetic_field["y"])
        return north_angle

    def as_dict(self) -> dict:
        environment_data_dict = deepcopy(self)
        environment_data_dict.datetime = str(self.datetime)
        return environment_data_dict.__dict__

    @staticmethod
    def from_db(timestamp: float, max_time_difference_s: int = 180):
        try:
            weather_datapoint = next(get_weather_datapoint(timestamp))
            gps_datapoint = next(get_gps_datapoint(timestamp))
            avg_illuminance = next(get_avg_illuminance(timestamp))

            air_pressure_measurements = [(it["timestamp"], it["air_pressure"]) for it in
                                         get_air_pressure_measurements(timestamp, window_in_sec=360)]
            avg_sound_pressure_measurements = [(it["timestamp"], it['avg_decibel']) for it
                                               in get_avg_sound_pressure_measurements(timestamp, window_in_sec=220)]

            magnetic_field = next(get_magnetic_field(timestamp))

        except StopIteration as e:
            logger.error(f'No data received for from db. {e} Stacktrace: {traceback.print_exc()}')

        # Check if time difference between requested data and results is within max_time_difference_s. Return if True.
        if (timestamp - weather_datapoint['timestamp']) > max_time_difference_s or (
                timestamp - gps_datapoint['timestamp']) > max_time_difference_s or (
                timestamp - avg_illuminance['timestamp']) > max_time_difference_s or (
                timestamp - air_pressure_measurements[0][0]) > max_time_difference_s or (
                timestamp - avg_sound_pressure_measurements[0][0]) > max_time_difference_s or (
                timestamp - magnetic_field['timestamp']) > max_time_difference_s:
            logger.error(f"""Outdated environment data received from db.
            weather: {timestamp - weather_datapoint['timestamp']} 
            gps: {timestamp - gps_datapoint['timestamp']}
            avg_illuminance: {timestamp - avg_illuminance['timestamp']}
            air_pressure_measurements: {timestamp - air_pressure_measurements[0][0]}
            avg_sound_pressure_measurements: {timestamp - avg_sound_pressure_measurements[0][0]}
            magnetic_field: {timestamp - magnetic_field['timestamp']}

            """)
        else:
            return EnvironmentData(
                timestamp=timestamp,
                position={'latitude': gps_datapoint['latitude'], 'longitude': gps_datapoint['longitude']},
                temperature=weather_datapoint["temperature"],
                humidity=weather_datapoint["humidity"],
                wind_speed=weather_datapoint["wind_speed"],
                gust_speed=weather_datapoint["gust_speed"],
                wind_direction=weather_datapoint["wind_direction"],
                magnetic_field=magnetic_field,
                avg_illuminance=avg_illuminance,
                air_pressure_measurements=air_pressure_measurements,
                avg_sound_pressure_measurements=avg_sound_pressure_measurements)


if __name__ == "__main__":
    EnvironmentData.from_db(1649684934.0844204)
