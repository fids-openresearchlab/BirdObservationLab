import numpy as np
import matplotlib.pyplot as plt
import math


# LS 220509

def flight_dir_location_match(pointA, pointB, cog, angleTolerance):
    """
    Checks, whether pointB is in the direction cog, starting from pointA, to within angleTolerance.
    :Inputs:
      - `pointA: The tuple representing the latitude/longitude for the
    first point. Latitude and longitude must be in decimal degrees
      - `pointB: The tuple representing the latitude/longitude for the
    second point. Latitude and longitude must be in decimal degrees
      - `cog: Course over ground from location pointA, decimal degrees
      - `angleTolerance: +- angleTolerance will be tolerated as a match, indecimal degrees
    :Returns:
        isMatch: True if condition is met, false otherwise

    """

    bearing = calculate_initial_compass_bearing(pointA, pointB)

    angleDiff = shortest_angle(cog, bearing)

    if abs(angleDiff) <= angleTolerance:
        isMatch = True
    else:
        isMatch = False

    return isMatch, cog, angleDiff, bearing


def calculate_initial_compass_bearing(pointA, pointB):
    """
    Calculates the bearing between two points.
    The formulae used is the following:
        θ = atan2(sin(Δlong).cos(lat2),
                  cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))
    :Parameters:
      - `pointA: The tuple representing the latitude/longitude for the
        first point. Latitude and longitude must be in decimal degrees
      - `pointB: The tuple representing the latitude/longitude for the
        second point. Latitude and longitude must be in decimal degrees
    :Returns:
      The bearing in degrees
    :Returns Type:
      float
    """

    # if (type(pointA) != tuple) or (type(pointB) != tuple):
    #    raise TypeError("Only tuples are supported as arguments")

    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])

    diffLong = math.radians(pointB[1] - pointA[1])

    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
                                           * math.cos(lat2) * math.cos(diffLong))

    bearing = math.atan2(x, y)

    # Now we have the initial bearing but math.atan2 return values
    # from -180° to + 180° which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360

    return bearing


def shortest_angle(start, end):
    # return the shortest difference between two angles (in 0-360 degrees)
    angle = ((end - start) + 180) % 360 - 180
    return angle

if __name__ == "__main__":
    # Test
    pointA = [0, 0]  # lat, lon
    pointB = [1, 1]
    cog = 30.5
    angleTolerance = 1

    plt.subplots(1, 1, figsize=(10, 10))
    plt.subplot(1, 1, 1)
    plt.plot(pointA[1], pointA[0], '.', label='pointA')
    plt.plot(pointB[1], pointB[0], '.', label='pointB')
    plt.xlim([-1.5, 1.5])
    plt.ylim([-1.5, 1.5])
    plt.xlabel('lon')
    plt.ylabel('lat')
    plt.grid()

    flight_dir_location_match(pointA, pointB, cog, angleTolerance)