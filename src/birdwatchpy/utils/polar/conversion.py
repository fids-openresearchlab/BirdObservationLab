from math import radians

import numpy as np


compass_brackets = ['N', 'NW', 'W', 'SW', 'S', 'SE', 'E', 'NO', 'N']
def angle_lookup(direction:str):
    #lookup_dict = {dir_str: deg for dir_str, deg in zip(["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"],[d for d in np.arange(0,360,22.5)])}
    lookup_dict = {dir_str: deg for dir_str, deg in zip(["N", "NNW", "NW", "WNW", "W", "WSW", "SW", "SSW", "S", "SSE", "SE", "ESE", "E", "ENE", "NE", "NNE"],[d for d in np.arange(0,360,22.5)])}
    print(lookup_dict)
    return radians(lookup_dict[direction])

def direction_lookup(deg: float):
    if deg < 0:
        degrees_final = 360 + deg
    else:
        degrees_final = deg
    print(degrees_final)
    print(deg)
    compass_lookup = round(degrees_final/ 45)
    return compass_brackets[compass_lookup]


def cart2pol(x, y):
    """returns rho, theta (degrees)"""
    angle =  np.degrees(np.arctan2(y, x))
    return angle, np.hypot(x, y)

def pol2cart(rho, phi):
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return (x, y)