# twilight-vs-latitude.py - this code explores minutes of day/twilight/night for a year
#
# In 1997 on a trip to Iceland at 66° north latitude one of the guides boasted:
# "We have the most twilight of anywhere on earth." Hmmm, I thought. That's quite the claim.
# Well, do they?
#
# Spoiler: yes, they do if you count only civil twilight. Folks at 83° north and south
# have more astronomical and more total twilight by a small margin. See a chart in
# /images/twilight-vs-latitude.pdf for a picture.
#
# Flip side: Who has the least twilight? That honor falls to folks on the equator.
# If you've ever been there you might notice that the transition from sunset to
# astronomical twilight, total darkness, is only 75 minutes. Be sure to take a
# flashlight if you plan to be out in the evening.
#
# Observation: What is up with the odd double peaks in the nautical and astronomical
# twilight plots at the polar latitudes?
#

import datetime as datetime
import SG_sunpos_ultimate_azi_atan2 as SG

observer_lon = 0.0


class max_tw():
    def __init__(self, category):
        self.category = category
        self.lat = None
        self.minutes = None

    def accumulate(self, lat, minutes):
        if self.lat is None or minutes > self.minutes:
            self.lat = lat
            self.minutes = minutes


max_d = max_tw("Daylight")
max_t = max_tw("Twilight")
max_n = max_tw("Night")
max_tc = max_tw("Twilight-civil")
max_tn = max_tw("Twilight-nautical")
max_ta = max_tw("Twilight-astronomical")

print("Latitude, Day, Twilight, Night, T-Civil, T-Nautical, T-Astronomical")
for observer_lat in range(-90, 91):
    c_d = c_n = t_c = t_n = t_a = 0
    tod_base_year = datetime.datetime(2024, 1, 1)
    for pday in range(0, 365):
        tod_base_day = tod_base_year + datetime.timedelta(days=pday)
        for pminute in range(24 * 60):
            tod_now = tod_base_day + datetime.timedelta(minutes=pminute)
            s_coalt, s_az, sunlat, sunlon, esd, eot = SG.solar_geometry(tod_now, observer_lat, observer_lon)

            if s_coalt <= 90.0:
                c_d += 1
            elif s_coalt <= 96.0:
                t_c += 1
            elif s_coalt <= 102.0:
                t_n += 1
            elif s_coalt <= 108.0:
                t_a += 1
            else:
                c_n += 1
    c_t = t_c + t_n + t_a
    print("%s, %d, %d, %d, %d, %d, %d" % (observer_lat, c_d, c_t, c_n, t_c, t_n, t_a))

    max_d.accumulate(observer_lat, c_d)
    max_t.accumulate(observer_lat, c_t)
    max_n.accumulate(observer_lat, c_n)
    max_tc.accumulate(observer_lat, t_c)
    max_tn.accumulate(observer_lat, t_n)
    max_ta.accumulate(observer_lat, t_a)

print("Observed maximums")
print("Category, Latitude, Minutes")
for maxx in [max_d, max_t, max_n, max_tc, max_tn, max_ta]:
    print("%s, %d, %d" % (maxx.category, maxx.lat, maxx.minutes))
