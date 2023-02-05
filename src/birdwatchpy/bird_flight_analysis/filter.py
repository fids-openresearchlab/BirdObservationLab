from typing import Sequence

from birdwatchpy.bird_flight_analysis.BirdFlightData import BirdFlightData


def filter_by_velocity(flights: Sequence[BirdFlightData], min_thresh: int = 2, max_thresh: int = 1500) -> list:
    return list(filter(lambda flight: min_thresh < flight.mean_vel < max_thresh, flights))


def filter_by_length(flights: Sequence[BirdFlightData], min_thresh: int = 800, max_thresh: int = 99999999) -> list:
    return list(filter(lambda flight: min_thresh < flight.length < max_thresh, flights))


def filter_by_straightness(flights: Sequence[BirdFlightData], min_thresh: int, max_thresh: int) -> list:
    return list(filter(lambda flight: min_thresh < flight.straightness < max_thresh, flights))


def default_bird_flight_filter(flights: Sequence[BirdFlightData]):
    return filter_by_length(flights)
