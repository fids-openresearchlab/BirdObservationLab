from datetime import datetime, timezone
import functools
from typing import Tuple
import pytz
from astral import moon, sun, LocationInfo, geocoder

def timezone_converter(input_dt, current_tz='UTC', target_tz='US/Eastern'):
    current_tz = pytz.timezone(current_tz)
    target_tz = pytz.timezone(target_tz)
    target_dt = current_tz.localize(input_dt).astimezone(target_tz)
    return target_tz.normalize(target_dt)

def is_within(timespan:Tuple, dtime: datetime):
    print(timespan[0].tzinfo)
    print(dtime.tzinfo)
    print(type(timespan[0]))
    print(type(dtime))
    return timespan[0] < dtime < timespan[1]

def get_astral_info(dtime:datetime,  latitude: float, longitude: float):
    #loc = get_loc(latitude=latitude, longitude=longitude)
    loc = geocoder.lookup("Berlin", geocoder.database())

    print(loc)
    print(dtime.tzinfo )
    if dtime.tzinfo is None:
        dtime = timezone_converter(dtime, target_tz=loc.timezone)
    print(dtime.tzinfo)
    astral_info = {
        "is_twilight": is_within(sun.twilight(loc.observer, dtime, tzinfo= loc.timezone), dtime),
        "is_night": is_within(sun.night(loc.observer, dtime,tzinfo= loc.timezone), dtime),
        "is_daylight": is_within(sun.daylight(loc.observer, dtime, tzinfo= loc.timezone), dtime),
        "is_blue_hour": is_within(sun.blue_hour(loc.observer, dtime, tzinfo= loc.timezone), dtime),
        "is_golden_hour": is_within(sun.golden_hour(loc.observer, dtime, tzinfo= loc.timezone), dtime),
        "moon_phase": moon.phase(dtime),
        "m_till_dawn": (sun.dawn(loc.observer, dtime, tzinfo= loc.timezone) - dtime).total_seconds()/60,
        "m_till_sunrise": (sun.sunrise(loc.observer, dtime, tzinfo= loc.timezone) - dtime).total_seconds()/60,
        "m_till_noon": (sun.noon(loc.observer, dtime, tzinfo= loc.timezone) - dtime).total_seconds()/60,
    }
    return astral_info


@functools.lru_cache(maxsize=None)
def get_loc(latitude: float, longitude: float):
    return LocationInfo(name='Berlin', latitude=latitude, longitude=longitude)


if __name__ == "__main__":
    print(get_astral_info(datetime.now(), latitude=52.520008, longitude=13.404954))

