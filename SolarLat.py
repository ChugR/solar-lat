#!/usr/bin/python
# SolarLat
# Given the day of the year N (0 == Jan 1), compute the
# latitude of the sun.
#
# Swiping liberally from Wikipedia
# https://en.wikipedia.org/wiki/Position_of_the_Sun
#
# MODEL 1
# =======
# The first approximation is
# o = - 23.44 x  cos ( [ (360 / 365) x ( N + 10 ) ] )
#
# where N is the day of the year beginning with N=0 at midnight 
# Universal Time (UT) as January 1 begins (i.e. the days part of the 
# ordinal date -1). The number 10, in (N+10), is the approximate number 
# of days after the December solstice to January 1. 
# This equation overestimates the declination near the September equinox 
# by up to +1.5 degrees. The sine function approximation by itself leads to an 
# error of up to 0.26 degrees and has been discouraged for use in solar energy 
# applications.[2] The 1971 Spencer formula[9] (based on a fourier series) 
# is also discouraged for having an error of up to 0.28 degrees.[10] 
# An additional error of up to 0.5 degrees can occur in all equations around 
# the equinoxes if not using a decimal place when selecting N to adjust 
# for the time after UT midnight for the beginning of that day. So the 
# above equation can have up to 2.0 degrees of error, about four times the Sun's 
# angular width, depending on how it is used.
#
# MODEL 2
# =======
# The next approximation is
# o = \arcsin \left [ \sin \left ( -23.44^\circ \right ) \cdot 
#        \cos \left ( \frac{360^\circ}{365.24} \left (N + 10 \right ) + 
#        \frac{360^\circ}{\pi} \cdot 0.0167 \sin \left ( 
#        \frac{360^\circ}{365.24} \left ( N - 2 \right ) \right ) \right ) \right ]
#
# o = arcsin ( sin ( -23.44(deg) ) * 
#        cos ( (360(deg) / 365.24) * (N + 10) + 
#        360(deg) / pi * 0.0167 * sin ( 
#        360(deg) / 365.24 * ( N - 2 ) ) ) )
#
# or
# o = - \arcsin \left [ 0.39779 \cos ( 0.98565 (N + 10 ) + 1.914 \sin ( 0.98565 ( N - 2 ) ) ) ]
#
# N is the number of days since midnight UT as January 1 begins (i.e. the 
# days part of the ordinal date -1) and can include decimals to adjust for 
# local times later or earlier in the day. The number 2, in (N-2), is the 
# approximate number of days after January 1 to the Earth's perihelion. 
# The number 0.0167 is the current value of the eccentricity of the 
# Earth's orbit. The eccentricity varies very slowly over time, but for 
# dates fairly close to the present, it can be considered to be constant. 
# The largest errors in this equation are less than +/- 0.2 degrees, but are less 
# than +/- 0.03 degrees for a given year if the number 10 is adjusted up or down 
# in fractional days as determined by how far the previous year's December 
# solstice occurred before or after noon on December 22. These accuracies 
# are compared to NOAA's advanced calculations[12][13] which are based on 
# the 1999 Jean Meeus algorithm that is accurate to within 0.01 degrees.[14]

# Facts for planets
#
# Planet      Axial tilt(degrees)
#             obliquity_deg
# ----------  -------------------
# Mercury      0.03
# Venus        2.64
# Earth       23.44
# Mars        25.19
# Jupiter      3.13
# Saturn      26.73
# Uranus      82.23
# Neptune     28.32
# Pluto       57.47

import math
import sys
from math import sin, cos, asin, acos, radians, degrees


class SolarLat:
    def __init__(self, obliquity_deg=23.44):
        # select the crappy or really great computational model
        self.computational_model = 2

        # define orbital constants (earth = 23.44)
        self.obliquity_deg = obliquity_deg
        self.eccentricity = 0.0167
        self.days_in_year = 365.24

        self.jan1_days_since_winter_solstice = 10
        self.jan1_days_before_perihelion = 2

        self.sin_of_obliquity = math.sin(math.radians(self.obliquity_deg))
        self.orbital_degrees_per_day = 360 / self.days_in_year

        self.orbital_radians_per_day = radians(self.orbital_degrees_per_day)
        self.eccentricity_const_rad = radians(360 / math.pi * self.eccentricity)
    
    def lat_of_day_rad(self, day_number):
        """
        Here is the putt putt
        """
        return -asin(self.sin_of_obliquity *
                     cos(self.orbital_radians_per_day *
                         (day_number + self.jan1_days_since_winter_solstice) +
                         (self.eccentricity_const_rad *
                          sin(self.orbital_radians_per_day *
                              (day_number - self.jan1_days_before_perihelion))
                          )
                         )
                     )

    def lat_of_day(self, day_number):
        """
        Given number of days N, the number of days since midnight UT as 
        January 1 begins (i.e. the # days part of the ordinal date -1)
        return the latitude of the sun in degreees.
        """
        if self.computational_model == 1:
            return -self.obliquity_deg * \
                   cos(self.orbital_radians_per_day *
                       (day_number + self.jan1_days_since_winter_solstice))

        if self.computational_model == 2:
            return math.degrees(self.lat_of_day_rad(day_number))

        raise Exception('bad version', 'bad version')

    @staticmethod
    def solve_for_a(A, b, c):
        """
        Given angles in radians
        1. A - angle at North Pole between two points
        2. b - angle from North Pole to solar point latitude
        3. c - angle from North Pole to observer on Prime 
        Return angle a in radians
        This is the cosine rule solving for 'a'.
        """
        return acos(cos(b) * cos(c) + sin(b) * sin(c) * cos(A))

    def test_solve_for_a(self, A, b, c, exp):
        """
        Given angles in degrees print the answer in degrees
        and OK or FAIL based on the expected answer.
        """
        thresh = 0.001
        ans = self.solve_for_a(radians(A), radians(b), radians(c))
        tresult = "OK" if abs(exp - degrees(ans)) < thresh else "FAIL"
        print("Test A=%d, b=%d, c=%d. Answer = %d, Result=%s" % (A, b, c, degrees(ans), tresult))

    def test_reasonable_slat(self, day_number, expected):
        actual = self.lat_of_day(float(day_number))
        if math.fabs(expected - actual) > 0.1:
            print("ERROR: on day {0:d} the expected= {1:d}, actual= {2:d}".format(day_number, expected, actual))

    @staticmethod
    def solar_lon_rad(tod):
        """
        Given tod 0.0..1.0 representing 00:00:00..23:59:59.999... in any day,
        return the longitude of the sun in radians -2pi..2pi
        """
        if tod < 0.0 or tod > 1.0:
            raise Exception('bad tod: tod goes from 0.0..1.0', 'bad tod')
        result = (tod * 2 * math.pi) - math.pi
        return result


#
# main
#
# This program considers only a point on some latitude
# on the prime meridian. Furthermore, the latitude is 
# north of the equator, as far as I care. Maybe south of
# the equator works.
#
# Time of day 0 = midnight in Greenwich. 
# Since the day is (should be) a floating point number,
# the time of day goes from 00:00:00.00 (HH.MM.SS.xx)
# to 23:59:59.99. The "N" sent to the SolarLat goes
# from day N.0 to N.999 proportionally.
#
# The day number goes from 0..364. The "normal" reference to
# days goes from 1..365. If you use 1..365 then you have to
# adjust the  magic constant 
# self.jan1_days_since_winter_solstice in lat_of_day. 
#
def main_except(argv):
    slat = SolarLat()
    for N in range(0, 365):
        print(" Day N=%s  Lat=%f" % (N, slat.lat_of_day(N)))

    # Checks based on Earth tilt=23.44, nDays=365
    # check spherical trig function. As if this will fail!
    slat.test_solve_for_a(90, 90, 90, 90)
    slat.test_solve_for_a(0, 10, 20, 10)
    slat.test_solve_for_a(100, 90, 90, 100)

    # check a few "pretty good" latitudes
    slat.test_reasonable_slat(0,    -23.08)
    slat.test_reasonable_slat(31,   -17.38)
    slat.test_reasonable_slat(80,    0.227)
    slat.test_reasonable_slat(100,   7.94)
    slat.test_reasonable_slat(146,  21.12)
    slat.test_reasonable_slat(172,  23.44)
    slat.test_reasonable_slat(211,  18.52)
    slat.test_reasonable_slat(252,   5.33)
    slat.test_reasonable_slat(287,  -8.14)
    slat.test_reasonable_slat(324, -19.69)
    slat.test_reasonable_slat(354, -23.42)


def main(argv):
    try:
        main_except(argv)
        return 0
    #    except ExitStatus, e:
    #        return e.status
    except Exception as e:
        print("%s: %s" % (type(e).__name__, e))
        return 1


if __name__ == "__main__":
    main(sys.argv)
