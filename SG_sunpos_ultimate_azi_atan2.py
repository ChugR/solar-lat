# 2021-04-14 # Solar Geometry using subsolar point and atan2
# See: https://www.sciencedirect.com/science/article/pii/S0960148121004031
# Algorithms/implementations: Taiping Zhang, Paul W. Stackhouse Jr., Bradley Macpherson, J. Colleen Mikovitz

import math

import numpy as np
# import xarray as xr
import pandas as pd 

from datetime import datetime


def modulo(A, P):
    return A - math.floor(A / P) * P


def constants():
    """ The standard constants in the solar equations.  """

    pi = math.pi
    rpd = math.pi/180.0
    dpr = 180.0/math.pi

    return pi, rpd, dpr


def astronomical_almanac(date):
    """
    Given the date, return almanac values of interest
    based on 'Astronomical Almanac for the Year 2019'

    :param date: the datetime object defining time of observation
    :return : delta - solar coaltitude in degrees
    :       : esd   - earth-sun distance in a.u.
    :       : eot   - equation of time in mysterious units
    """

    pi, rpd, dpr = constants()

    n = (date - datetime(2000, 1, 1, 12)).total_seconds() / 86400                                                 #       n: Number of days from J2000.0.
    L = modulo(280.460 + 0.9856474 * n, 360.0)                                                                    #       L: Mean longitude of the Sun, corrected for aberration, in deg.
    g = modulo(357.528 + 0.9856003 * n, 360.0)                                                                    #       g: Mean anomaly, in deg.
    lamb = modulo(L + 1.915 * math.sin(g * rpd) + 0.020 * math.sin(2 * g * rpd), 360.0)                           #    lamb: Ecliptic longitude, in deg.
    epsilon = 23.439 - 0.0000004 * n                                                                              # epsilon: Obliquity of ecliptic, in deg.
    alpha = modulo(math.atan2(math.cos(epsilon * rpd) * math.sin(lamb * rpd), math.cos(lamb * rpd)) / rpd, 360.0) #   alpha: Right ascension, in deg.
    delta = math.asin(math.sin(epsilon * rpd) * math.sin(lamb * rpd)) / rpd                                       #   delta: Declination of Sun, in deg.
    esd = 1.00014 - 0.01671 * math.cos(g * rpd) - 0.00014 * math.cos(2 * g * rpd)                                 #     esd: Earth-Sun distance, in au.
    eot = modulo((L - alpha) + 180.0, 360.0) - 180.0                                                              #     eot: Equation of Time (range: -180, 180).
            
    return delta, esd, eot


def solar_angle_equations(delta, sunlon, latitude, longitude):
    """
    Creates the solar zenith angle and solar azimuth angle values.

    - delta: declination of sun in degrees, same as sunlat. (required)
    - sunlon: the longitude of the subsolar point, the spot directly under sun (required)
    - latitudes: the latitude values as a float in an array (required)
    - longitudes: the longitude values as a float in an array (required)
    """


    pi, rpd, dpr = constants()

    sunlat = delta

    PHIo = latitude * rpd
    PHIs = sunlat * rpd
    LAMo = longitude * rpd
    LAMs = sunlon * rpd

    Sx = np.cos(PHIs) * np.sin(LAMs - LAMo)
    Sy = np.cos(PHIo) * np.sin(PHIs) - np.sin(PHIo) * np.cos(PHIs) * np.cos(LAMs - LAMo)
    Sz = np.sin(PHIo) * np.sin(PHIs) + np.cos(PHIo) * np.cos(PHIs) * np.cos(LAMs - LAMo)
    del sunlon, PHIo, PHIs, LAMo, LAMs

    sza = np.arccos(Sz) / rpd  # solar_zenith_angle BEFORE correction. Equivalent to the original one.
    saa = np.arctan2(-Sx, -Sy) / rpd  # solar_azimuth_angle #!South-Clockwise Convention.
    del Sx, Sy, Sz

    # Solar Zenith Angle in degrees
    #    Multiply by rpd = Radians
    sza = sza.transpose("time", "lat", "lon")
    sza.attrs["long_name"] = "Solar Zenith Angle"
    sza.attrs["units"] = "Degree"

    saa = saa.transpose("time", "lat", "lon")
    saa.attrs["long_name"] = "Solar Azimuth Angle"
    saa.attrs["units"] = "Degree"

    return sza, saa


def solar_geometry_dataframe(date, latitudes, longitudes):
    """
    Adds the dataset coordinates to the input dataframe and computes the Solar Zenith Angle and Solar Azimuth Angle.
    - date: the datetime object (required)
    - latitudes: the latitude values as a float in an array (required)
    - longitudes: the longitude values as a float in an array (required)
    """

    data = []
    for latitude in latitudes:
        for longitude in longitudes:
            data.append((latitude, longitude, date, latitude, longitude))

    ds = pd.DataFrame(data, columns=['lat', 'lon', 'time', 'latitude', 'longitude']).set_index(['time', 'lat', 'lon']).to_xarray()
    
    hour = float(date.hour + round(((date.minute * 60) + date.second) / 3600, 3)) # The hour fraction value as an float...

    delta, esd, eot = astronomical_almanac(date)

    sunlon = -15.0*(hour-12.0+eot*4/60)   #eot*4 is Equation of Time in minutes.
    sza, saa = solar_angle_equations(delta, sunlon, ds.latitude, ds.longitude)
    
    ds["SG_SZA"] = sza
    ds["SG_SAA"] = saa
    
    return ds, delta, sunlon, esd, eot


def solar_angle_equations_no_df(delta, sunlon, latitude, longitude):
    """
    Creates the solar zenith angle and solar azimuth angle values.
    This function uses math functions and not numpy.
    Az/El returned directly and not in numpy arrays

    :param     delta: coaltitude (declination) of sun in degrees, same as sunlat.
    :param    sunlon: the longitude of the subsolar point in degrees
    :param  latitude: observer latitude in degrees float
    :param longitude: observer longitude in degrees float

    :return : sza - solar zenith angle (coaltitude) in degrees
    :       : saa - solar azimuth angle in degrees
    """
    sunlat = delta

    PHIo = math.radians(latitude)
    PHIs = math.radians(sunlat)
    LAMo = math.radians(longitude)
    LAMs = math.radians(sunlon)

    Sx = math.cos(PHIs) * math.sin(LAMs - LAMo)
    Sy = math.cos(PHIo) * math.sin(PHIs) - math.sin(PHIo) * math.cos(PHIs) * math.cos(LAMs - LAMo)
    Sz = math.sin(PHIo) * math.sin(PHIs) + math.cos(PHIo) * math.cos(PHIs) * math.cos(LAMs - LAMo)

    sza = math.degrees(math.acos(Sz))  # solar_zenith_angle BEFORE correction. Equivalent to the original one.
    # saa = math.degrees(math.atan2(-Sx, -Sy))  # solar_azimuth_angle #!South-Clockwise Convention.
    saa = math.degrees(math.atan2(Sx, Sy))  # solar_azimuth_angle #!North-Clockwise Convention.

    return sza, saa


def solar_geometry(date, latitude, longitude):
    """ solar_geometry

    Given a time, observer lat and lon, return solar azimuth and elevation

    :param : date - observation time as datetime object
    :param : latitude - observer latitude in floating degrees
    :param : longitude - observer longitude in floating degrees

    :return
    :    : results from observer's position
    :       : observer's solar coaltitude (zenith angle) (float degrees)
    :       : observer's solar azimuth angle (float degrees)
    :    : facts about solar position
    :       : sunlat   - almanac position of sun on earth (float degrees)
    :       : sunlon   - almanac position of sun on earth (float degrees)
    :       : esd      - earth-sun distance (float a.u.)
    :       : eot      - equation of time in degrees. positive values when sun-fast.
    """
    hour = float(date.hour + round(((date.minute * 60) + date.second) / 3600, 3))  # fractional hour

    sunlat, esd, eot = astronomical_almanac(date)

    sunlon = -15.0 * (hour - 12.0 + eot * 4 / 60)  # eot*4 is Equation of Time in minutes.
    sza, saa = solar_angle_equations_no_df(sunlat, sunlon, latitude, longitude)

    return sza, saa, sunlat, sunlon, esd, eot


if __name__ == '__main__':

    # My Single Case
    inyear = 2023   # Input year.
    inmon = 1       # Input month.
    inday = 1      # Input day.
    inGMT = 0.0   # Input time in GMT.
    date = datetime(inyear, inmon, inday, int(inGMT), int((inGMT*60) % 60), int((inGMT*3600) % 60))
    latitudes = [42.6]    # np.arange(-89.75,  90, 1)
    longitudes = [0.0]  # np.arange(-179.75, 180, 1)
    ds, delta, sunlon, esd, eot = solar_geometry_dataframe(date, latitudes, longitudes)

    print("===== Dataframe results =====")
    print("----- DS -----")
    print(ds)
    print("----- DS-SG_SZA -----")
    print(ds["SG_SZA"])
    print("----- DS-SG_SAA -----")
    print(ds["SG_SAA"])
    print("----- solar lat-lon -----")
    print(delta, sunlon)

    print("===== streamlined solar lat-lon =====")
    slat, slon, sunlat, sunlon, esd, eot = solar_geometry(date, latitudes[0], longitudes[0])
    print("slat, slon, sunlat, sunlon, esd: ", slat, slon, sunlat, sunlon, esd)

    # insolation values
    watts_per_m_m = 1377
    print("nominal watts/m*m = %9.5f" % watts_per_m_m)

    print("Jan 1 watts/m*m = %9.5f" % (watts_per_m_m / (esd * esd)))

    inyear = 2023   # Input year.
    inmon = 7       # Input month.
    inday = 1      # Input day.
    inGMT = 0.0   # Input time in GMT.
    date = datetime(inyear, inmon, inday, int(inGMT), int((inGMT*60) % 60), int((inGMT*3600) % 60))
    slat, slon, sunlat, sunlon, esd, eot = solar_geometry(date, latitudes[0], longitudes[0])
    print("Jul 1 watts/m*m = %9.5f" % (watts_per_m_m / (esd * esd)))

    print("")

    print("Debug - feb 10 2023")
    inyear = 2023   # Input year.
    inmon = 1       # Input month.
    inday = 1      # Input day.
    inGMT = 12.0   # Input time in GMT.
    date = datetime(inyear, inmon, inday, int(inGMT), int((inGMT*60) % 60), int((inGMT*3600) % 60))
    # That's supposed to be noon on Jan 1, 2023
    ds, delta, sunlon_d, esd, eot = solar_geometry_dataframe(date, latitudes, longitudes)

    o_sun_zenith_deg, o_sun_azimuth_deg, sunlat, sunlon, esd, eot = solar_geometry(date, latitudes[0], longitudes[0])
    pass