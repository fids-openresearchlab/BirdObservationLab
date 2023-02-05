import itertools
from typing import Union, List

from birdwatchpy.bird_flight_analysis import BirdFlightData
from birdwatchpy.database import get_latest_percentile_dict
from birdwatchpy.environment import EnvironmentData
from birdwatchpy.utils.polar.compass_bearing import flight_dir_location_match
from birdwatchpy.sequences import SequenceData
from birdwatchpy.text_generation.productions import TerminalProduction, SentenceProduction


def lt_and_gt_and_eq_predicate(key, value, thresh):
    if key.endswith("_lt"):
        return lt_predicate(value, thresh)
    elif key.endswith("_gt"):
        return gt_predicate(value, thresh)
    elif key.endswith("_eq"):
        return eq_predicate(value, thresh)
    else:
        raise ValueError


def lt_predicate(value, thresh):
    return value < float(thresh)


def gt_predicate(value, thresh):
    return value > float(thresh)


def eq_predicate(value, thresh):
    return value == thresh


def is_predicate(value, thresh):
    if type(value) == bool:
        return str(value) == thresh.strip(' ')


def process_single_flight(sequence: SequenceData, environment: EnvironmentData, flight: BirdFlightData,
                          sentence_productions_list: List[SentenceProduction],
                          terminal_productions_list: List[TerminalProduction]):

    # Extend flight with direction info
    # ToDo: Still required?
    if flight.flight_direction is None:
        flight.set_flight_direction(environment)

    filtered_terminal_prod = []
    for prod in itertools.chain(sentence_productions_list, terminal_productions_list):
        # Productions without args
        if prod.processor == "always_include_processor":
            pass
        elif prod.processor == "bird_count_processor":
            arg = list(prod.processor_args.items())[0]
            if lt_and_gt_and_eq_predicate(arg[0], 1, int(arg[1])) is not True:
                prod = None
        elif prod.processor == "locations_processor":
            #(environment.position['latitude'],environment.position['longitude'])
            if not flight_dir_location_match((53.542668, 10.033612),(float(prod.processor_args['latitude']),float(prod.processor_args['longitude'])) ,
                                             cog=flight.flight_direction, angleTolerance=12):
                prod=None
        elif prod.processor == 'generic_processor':
            prod = generic_processor(prod, environment, flight = flight)
        else:
            print(f"Processor not found: {prod.processor}")
            prod = None

        if prod is not None:
            filtered_terminal_prod.append(prod)
    return filtered_terminal_prod

def create_audio_based_productions(environment: EnvironmentData, sentence_productions_list: List[SentenceProduction],
                          terminal_productions_list: List[TerminalProduction]):

    filtered_terminal_prod = []
    for prod in itertools.chain(sentence_productions_list, terminal_productions_list):
        # Productions without args
        if prod.processor == "always_include_processor":
            pass
        elif prod.processor == "is_bird_sound_processor":
            pass
        elif prod.processor == 'generic_processor':
            prod = generic_processor(prod, environment)
        else:
            print(f"Processor not found: {prod.processor}")
            prod = None

        if prod is not None:
            filtered_terminal_prod.append(prod)
    return filtered_terminal_prod


def generic_processor(prod: Union[TerminalProduction, SentenceProduction], environment: EnvironmentData, sequence: SequenceData = None,
                       flight: BirdFlightData= None):
    percentiles_data_dict = get_latest_percentile_dict()

    for key, thresh in prod.processor_args.items():
        #####################
        ###### Weather ######
        #####################
        if key == 'temp_absolute_gt' or key == 'temp_absolute_lt':
            if not lt_and_gt_and_eq_predicate(key, environment.temperature, int(thresh)):
                return
        # Astral Info
        elif key == 'is_night':
            if not is_predicate(environment.astral_info['is_night'], thresh):
                return
        elif key == 'is_twilight':
            if not is_predicate(environment.astral_info['is_twilight'], thresh):
                return
        elif key == 'is_daylight':
            if not is_predicate(environment.astral_info['is_daylight'], thresh):
                return
        elif key == 'is_golden_hour':
            if not is_predicate(environment.astral_info['is_golden_hour'], thresh):
                return
        elif key == 'is_blue_hour':
            if not is_predicate(environment.astral_info['is_blue_hour'], thresh):
                return
        elif key == 'is_night':
            if not is_predicate(environment.astral_info['is_night'], thresh):
                return
        elif key == 'is_night':
            if not is_predicate(environment.astral_info['is_night'], thresh):
                return
        elif key == 'temp_absolute_gt' or key == 'temp_absolute_lt':
            if not lt_and_gt_and_eq_predicate(key, environment.temperature, thresh):
                return
        elif key == 'moon_phase_gt' or key == 'moon_phase_lt':
            if not lt_and_gt_and_eq_predicate(key, environment.astral_info['moon_phase'], thresh):
                return

        #####################
        #### Flight Data ####
        #####################
        elif (key == 'speed_percentile_gt' or key == 'speed_percentile_lt') and flight is not None:
            thresh = percentiles_data_dict['Avg. Speed']['percentile_res'][str(thresh)]
            if not lt_and_gt_and_eq_predicate(key, flight.avg_speed, thresh):
                return None
        elif (key == 'full_path_straightness_gt' or key == 'full_path_straightness_lt') and flight is not None:
            if not lt_and_gt_and_eq_predicate(key, flight.straightness_dict['1/1'], thresh):
                return None
        elif (key == 'flap_frequency_percentile_gt' or key == 'flap_frequency_percentile_lt') and flight is not None:
            thresh = percentiles_data_dict['wing_flap_frequency']['percentile_res'][str(thresh)]
            if not lt_and_gt_and_eq_predicate(key, flight.wing_flap_frequency, thresh):
                return None
        # Geo
        elif key == 'orientation_eq' and flight is not None:
            if not eq_predicate(flight.get_flight_direction_char(), thresh):
                return

        else:
            print(f"Arg processor not found: {key}")
            return

    return prod
