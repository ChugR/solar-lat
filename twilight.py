#!/usr/bin/python
# twilight
# Use the SolarLat package to discover cool stuff about twilight.

from optparse import OptionParser
import SolarLat
from SolarLat import *
from PIL import Image, ImageDraw, ImageFont
import datetime
import traceback
import base64
import io

TWILIGHT_VERSION = 1.5


class Constants:
    """
    Earth orbital constants for defaults
    """
    OBLIQUITY = 23.44
    OBSERVER_LAT_DEG = 42.6


class BColors:
    """
    Ansi escapes to colorize flat text
    """
    BLACK   = '~[30m'
    BLUE    = '~[34m'
    MAGENTA = '~[35m'
    YELLOW  = '~[33m'
    WHITE   = '~[37m'


class DisplayState:
    """
    Given angle between sun and observer as seen from
    the center of the earth, return some display value
    to represent the light, dark and various twilights.
    strategy 1: return letter of light state
    strategy 2: return ansi escape sequence for color of light state
    strategy 3: return PIL rbg color
    """
    def __init__(self, strategy=1):
        # set up daylight ranges
        self.rad_max_L6 = radians(15)
        self.rad_max_L5 = radians(30)
        self.rad_max_L4 = radians(45)
        self.rad_max_L3 = radians(60)
        self.rad_max_L2 = radians(75)
        self.rad_max_L1 = radians(90)
        
        # set up twilight ranges
        self.rad_max_civil        = radians(90.0 + 1.0 * 6.0)
        self.rad_max_nautical     = radians(90.0 + 2.0 * 6.0)
        self.rad_max_astronomical = radians(90.0 + 3.0 * 6.0)
        
        # set up dark ranges
        self.rad_max_D1 = radians(132)
        self.rad_max_D2 = radians(156)

        # colors[] holds the set-ansi-color escape sequence
        self.color_ansi = {"L": BColors.WHITE,
                           "C": BColors.YELLOW,
                           "N": BColors.MAGENTA,
                           "A": BColors.BLUE,
                           "D": BColors.BLACK}
        self.color_pil = {  
                          "L6": "#FFFFFF",
                          "L5": "#F8F8F8",
                          "L4": "#F0F0F0",
                          "L3": "#E8E8E8",
                          "L2": "#E0E0E0",
                          "L1": "#D0D0D0",
                          "C": "#EA5D0D",
                          "N": "#0D3C89",
                          "A": "#607060",
                          "D1": "#303030",
                          "D2": "#181818",
                          "D3": "#000000"
                          }

        self.anticolor_pil = {
                          "L6": "#000000",
                          "L5": "#000000",
                          "L4": "#000000",
                          "L3": "#000000",
                          "L2": "#000000",
                          "L1": "#000000",
                          "C": "#FFFFFF",
                          "N": "#FFFFFF",
                          "A": "#FFFFFF",
                          "D1": "#FFFFFF",
                          "D2": "#FFFFFF",
                          "D3": "#FFFFFF"
                          }

        # pick a display strategy
        self.strategy = strategy

    def get_display_code(self, value_rad):
        return  \
                "L6" if value_rad <= self.rad_max_L6 else \
                "L5" if value_rad <= self.rad_max_L5 else \
                "L4" if value_rad <= self.rad_max_L4 else \
                "L3" if value_rad <= self.rad_max_L3 else \
                "L2" if value_rad <= self.rad_max_L2 else \
                "L1" if value_rad <= self.rad_max_L1 else \
                "C" if value_rad <= self.rad_max_civil else \
                "N" if value_rad <= self.rad_max_nautical else \
                "A" if value_rad <= self.rad_max_astronomical else \
                "D1" if value_rad <= self.rad_max_D1 else \
                "D2" if value_rad <= self.rad_max_D2 else \
                "D3"

    def get_display(self, value_rad):
        """
        :param value_rad:
        :return:
        """
        val = self.get_display_code(value_rad)
        if self.strategy == 1:
            return val
        elif self.strategy == 2:
            return self.color_ansi[val]
        elif self.strategy == 3:
            return self.color_pil[val]
        else:
            return "you lose"


class AccumulateState:
    """
    Count ticks per state.
    You need one of these for a.m. and one for p.m.
    """
    def __init__(self):
        self.counts = {"L6": 0, "L5": 0, "L4": 0, "L3": 0, "L2": 0, "L1": 0,
                       "C": 0, "N": 0, "A": 0, "D1": 0, "D2": 0, "D3": 0}


def compute_solar_coaltitude(day, fraction_tod, o_colat_rad, solarLat):
    date = float(day) + fraction_tod
    s_lat_rad = solarLat.lat_of_day_rad(date)
    s_colat_rad = math.pi / 2 - s_lat_rad
    s_lon_rad = solarLat.solar_lon_rad(fraction_tod)
    a = solarLat.solve_for_a(s_lon_rad, s_colat_rad, o_colat_rad)
    return a


def compute_display_state(day, fraction_tod, o_colat_rad, solarLat, displayState):
    """
    Given a day number, fractional time of day, observer colat, solarLat, and displayState
    calculate the display state.
    param day:
    param fraction_tod:
    param o_colat_rad:
    param solarLat:
    return:
    """
    a = compute_solar_coaltitude(day, fraction_tod, o_colat_rad, solarLat)
    state = displayState.get_display(a)
    return state


def compute_half_day(day, o_colat_rad, solar_lat, start_min, interval, accumulator):
    displaystate = DisplayState()
    for mins in range(0, 12*60, interval):
        fraction_tod = float(start_min + mins) / float(24*60)
        state = compute_display_state(day, fraction_tod, o_colat_rad, solar_lat, displaystate)
        accumulator.counts[state] += 1


def main_except_v0(argv):
    #
    # mission code
    #
    # Display as:
    # 1. Simple ascii letters only
    # 2. Ansi colorized escapes sequences and then letters
    #
    display_as = 1

    # Settings for this run
    # arg 1: observer's latitude [42]
    o_lat_deg = 42.2    # user latitude in degrees North
    if len(sys.argv) >= 2:
        o_lat_deg = float(sys.argv[1])
    # arg 2: time between sample points in minutes
    interval_min = 10   # time between plot points in minutes
    if len(sys.argv) >= 3:
        interval_min = int(sys.argv[2])

    # The run
    o_colat_rad = radians(90 - o_lat_deg)
    solarLat = SolarLat()
    ds = DisplayState()
    print("Twilight v%2.1f Observer is at %2.1f degrees north." % (TWILIGHT_VERSION, o_lat_deg))
    xlabel1 = ""
    xlabel2 = ""
    pad = " " * int(60 / interval_min - 2)
    for hr in range(0, 24):
        xlabel1 += format(hr, '02d') + pad
        xlabel2 += "| " + pad
    print("     " + xlabel1)
    print("     " + xlabel2)
    for day in range (0, 365):
        as_am = AccumulateState()
        compute_half_day(day, o_colat_rad, solarLat, 00*60, interval_min, as_am)
        as_pm = AccumulateState()
        compute_half_day(day, o_colat_rad, solarLat, 12*60, interval_min, as_pm)
        line = format(day, '03d') + ": "
        for s in ["D3", "D2", "D1", "A", "N", "C", "L1", "L2", "L3", "L4", "L5", "L6"]:
            n = as_am.counts[s]
            if n > 0:
                if display_as == 2:
                    line += ds.color_pil[s]
                line += s * n
        for s in ["L6", "L5", "L4", "L3", "L2", "L1", "C", "N", "A", "D1", "D2", "D3"]:
            n = as_pm.counts[s]
            if n > 0:
                if display_as == 2:
                    line += ds.color_pil[s]
                line += s * n
        print("%s" % line)
    return 0


def get_doy(doy_string):
    """
    Given a doy string like "2011.01.01" return the day of the year 0..364
    Note: Be sure to pick a non-leap year.
    :param doy_string:
    :return:
    """
    dt = datetime.datetime.strptime(doy_string, '%Y.%m.%d')
    tt = dt.timetuple()
    doy = tt.tm_yday - 1
    return doy


def get_date_of_doy(doy):
    """
    Given a day-of-year 0..364 for a non leap year, return "Mmm DD" string
    """
    dofdoy = datetime.datetime(2010, 1, 1) + datetime.timedelta(doy)
    mons = ["foo", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    res = "%s %d" % (mons[dofdoy.month], dofdoy.day)
    return res


def ddoy(draw, doy_string, doy_text, l_margin, t_margin, v_mag):
    """
    Given a day-of-year string for a non-leap year
    Draw the doy_text and a tick mark in the left margin.
    :param draw:
    :param doy_string:
    :param doy_text:
    :param l_margin:
    :param t_margin:
    :param v_mag:
    :return:
    """
    doy = get_doy(doy_string)
    x_o = 0
    x_e = l_margin
    y = t_margin + doy * v_mag
    draw.line((x_o, y, x_e, y), "black")
    draw.text((x_o + 1, y + 1), doy_text, "black")
    return


def dalt(draw, altitude, alt_text, l_margin, t_margin, v_points):
    """
    Draw the altitude legend string in the left margin of a cartesian
    drawing.
    param draw:
    param altitude:
    param alt_text:
    param l_margin:
    param t_margin:
    param v_points:
    return:
    """
    # altitude goes from 90..-90. Subtracting 90 gives 0..-180.
    # negate that to get the vertical offset in the graph.
    scale = -(altitude - 90)
    y = t_margin + v_points * scale / 180
    xo = l_margin - 4
    xe = l_margin
    draw.line((xo, y, xe, y), "black")
    draw.text((1, y - 5), alt_text, "black")


def dplusses(draw, doy_string, l_margin, t_margin, v_mag, h_points):
    """
    Given a day-of-year string for a non-leap year
    Draw plus marks at 6:00, 12:00, and 18:00
    Use black-on-white for contrast over any background color
    :param draw: drawing context
    :param doy_string: what day?
    :param l_margin: left margin
    :param t_margin: top margin
    :param v_mag: vertical magnification
    :param h_points: size of drawing along x axis
    :return: none
    """
    doy = get_doy(doy_string)
    y = t_margin + doy * v_mag
    for qd in range(1, 4):
        x = l_margin + h_points * qd / 4
        draw.line((x + 0, y - 1, x + 0, y + 1), "black")
        draw.line((x - 1, y + 0, x + 1, y + 0), "black")
        draw.line((x - 1, y - 1, x - 1, y - 1), "white")
        draw.line((x - 1, y + 1, x - 1, y + 1), "white")
        draw.line((x + 1, y - 1, x + 1, y - 1), "white")
        draw.line((x + 1, y + 1, x + 1, y + 1), "white")


def ddoy_lbr(draw, ds, x_o, y_o, v_ticks, wid, deg1, deg2, color, boxlabel, bl2=''):
    """
    Draw day-of-year legend box right part.
    param draw:
    param x_o: legend origin x
    param y_o: legend origin y
    param v_ticks: total legend height
    param wid: box width
    param deg1: upper degrees 90..-90
    param deg2: lowed degrees 90..-90
    param color:
    param boxlabel: what to show inside the color box
    return:
    """
    x = x_o
    y_top = y_o + (90 - deg1) * v_ticks / 180
    y_bot = y_o + (90 - deg2) * v_ticks / 180
    # Show color box with label unless suppressed
    if not deg1 == deg2:
        draw.rectangle([(x, y_top), (x + wid, y_bot)], fill=ds.color_pil[color])
        if not boxlabel == '':
            color = "black" if deg1 > 0 else "white"
            draw.text((x + 2, y_top + 1), boxlabel, color)
            if not bl2 == '':
                draw.text((x+2, y_top + 1 + 10), bl2, color)
    # Show tick label using deg1
    draw.line((x + wid, y_top, x + wid + 2, y_top), "black")
    draw.text((x + wid + 5, y_top - 5), str(deg1), "black")


def image_output(image, fname, b64):
    """
    Dump the image. If b64 then show base64 on stdout else
    write png to file.
    :param image:
    :param fname:
    :param b64:
    :return:
    """
    if b64:
        buffered = io.StringIO()
        image.save(buffered, "PNG")
        image_str = base64.b64encode(buffered.getvalue())
        print("%s" % image_str)
    else:
        image.save(fname, "PNG")
        image.show()


def main_show_a_year(o_lat_deg=Constants.OBSERVER_LAT_DEG,
                     axial_tilt=Constants.OBLIQUITY,
                     interval_min=1,
                     b64=False):
    #
    # mission code
    #
    # Display as:
    #   .png file
    #
    # Settings for this run
    # arg 1: observer's latitude [42]
    # arg 2: axial tilt [earth = 23.44]
    # arg 3: time between sample points in minutes
    #
    # This program considers only a point on some latitude
    # on the prime meridian.
    #
    # Time of day 0 = midnight in Greenwich.
    # Since the day is (should be) a floating point number,
    # the time of day goes from 00:00:00.00 (HH.MM.SS.xx)
    # to 23:59:59.99. The "N" sent to the SolarLat goes
    # from day N.0 to N.999 proportionally.
    #
    # The day number goes from 0..364. The "normal"  reference to
    # days goes from 1..365. If you use 1..365 then you have to
    # adjust the "10.0" magic constant in lat_of_day.
    #

    tilt_hint = "_tilt-%0.0f" % axial_tilt
    tilt_legend = ", axial tilt: %0.1f" % axial_tilt

    # The run
    o_colat_rad = radians(90 - o_lat_deg)
    solarLat = SolarLat(axial_tilt)
    ds = DisplayState(strategy=3)
    # print ("Twilight v%2.1f Observer is at %2.1f degrees north." % (TWILIGHT_VERSION, o_lat_deg))
    l_margin = 30
    r_margin = 10
    t_margin = 60
    b_margin = 10
    h_mag = interval_min
    h_points = (24 * 60 / interval_min) * h_mag
    v_mag = 3
    v_points = 365 * v_mag
    W = l_margin + h_points + r_margin
    H = t_margin + v_points + b_margin

    img = Image.new("RGB", (int(W), int(H)), "white")
    draw = ImageDraw.Draw(img)

    # Draw the main diagram
    for day in range(0, 365):
        as_am = AccumulateState()
        compute_half_day(day, o_colat_rad, solarLat, 00*60, interval_min, as_am)
        as_pm = AccumulateState()
        compute_half_day(day, o_colat_rad, solarLat, 12*60, interval_min, as_pm)

        y_orig = t_margin + (day * v_mag)
        x_work = l_margin
        for s in ["D3", "D2", "D1", "A", "N", "C", "L1", "L2", "L3", "L4", "L5", "L6"]:
            n = as_am.counts[s]
            if n > 0:
                draw.rectangle([(x_work, y_orig), (x_work + n * h_mag, y_orig + v_mag)], fill=ds.color_pil[s])
                x_work += n * h_mag
        for s in ["L6", "L5", "L4", "L3", "L2", "L1", "C", "N", "A", "D1", "D2", "D3"]:
            n = as_pm.counts[s]
            if n > 0:
                draw.rectangle([(x_work, y_orig), (x_work + n * h_mag, y_orig + v_mag)], fill=ds.color_pil[s])
                x_work += n * h_mag

    # Draw the title and facts
    draw.text((2,2),
              "SolarTwilight v%s            Altitude of Sun during a year" % TWILIGHT_VERSION,
              "black")
    draw.text((2,14),
              "Observer latitude: %0.1f" % o_lat_deg,
              "black")

    # Draw the legend
    # define legend box "lb"
    lb_top = 0
    lb_left = 450
    lb_bottom = 30
    lb_right = 1050
    lb_text_margin = 1
    lb_horiz_div_height = 15
    #lb_height = lb_bottom - lb_top
    lb_width = lb_right - lb_left

    # draw the legend color boxes
    # this could stand some refactoring
    x = lb_left
    y = lb_horiz_div_height
    x_inc = lb_width / 12
    draw.rectangle([(x + 0 * x_inc, y), (x + 1 * x_inc, lb_bottom)], fill=ds.color_pil['D3'])
    draw.rectangle([(x + 1 * x_inc, y), (x + 2 * x_inc, lb_bottom)], fill=ds.color_pil['D2'])
    draw.rectangle([(x + 2 * x_inc, y), (x + 3 * x_inc, lb_bottom)], fill=ds.color_pil['D1'])
    draw.rectangle([(x + 3 * x_inc, y), (x + 4 * x_inc, lb_bottom)], fill=ds.color_pil['A'])
    draw.rectangle([(x + 4 * x_inc, y), (x + 5 * x_inc, lb_bottom)], fill=ds.color_pil['N'])
    draw.rectangle([(x + 5 * x_inc, y), (x + 6 * x_inc, lb_bottom)], fill=ds.color_pil['C'])
    draw.rectangle([(x + 6 * x_inc, y), (x + 7 * x_inc, lb_bottom)], fill=ds.color_pil['L1'])
    draw.rectangle([(x + 7 * x_inc, y), (x + 8 * x_inc, lb_bottom)], fill=ds.color_pil['L2'])
    draw.rectangle([(x + 8 * x_inc, y), (x + 9 * x_inc, lb_bottom)], fill=ds.color_pil['L3'])
    draw.rectangle([(x + 9 * x_inc, y), (x + 10 * x_inc, lb_bottom)], fill=ds.color_pil['L4'])
    draw.rectangle([(x + 10 * x_inc, y), (x + 11 * x_inc, lb_bottom)], fill=ds.color_pil['L5'])
    draw.rectangle([(x + 11 * x_inc, y), (x + 12 * x_inc, lb_bottom)], fill=ds.color_pil['L6'])

    # draw legend box lines
    draw.rectangle((lb_left, lb_top, lb_right, lb_bottom), outline="black")
    draw.text((lb_left + lb_text_margin + 1 * (lb_width / 12), lb_top + lb_text_margin), "dark", "black")
    draw.text((lb_left + lb_text_margin + 4 * (lb_width / 12), lb_top + lb_text_margin), "twilight", "black")
    draw.text((lb_left + lb_text_margin + 8.5 * (lb_width / 12), lb_top + lb_text_margin), "light", "black")
    draw.text((lb_left + lb_text_margin + 3 * (lb_width / 12), lb_horiz_div_height + 3 * lb_text_margin),
              " astro", "white")
    draw.text((lb_left + lb_text_margin + 4 * (lb_width / 12), lb_horiz_div_height + 3 * lb_text_margin),
              " naut", "white")
    draw.text((lb_left + lb_text_margin + 5 * (lb_width / 12), lb_horiz_div_height + 3 * lb_text_margin),
              " civil", "white")
    draw.line((lb_left, lb_horiz_div_height, lb_right, lb_horiz_div_height), "black")
    draw.line((lb_left + 3 * x_inc, lb_top, lb_left + 3 * x_inc, lb_bottom), "black")
    draw.line((lb_left + 6 * x_inc, lb_top, lb_left + 6 * x_inc, lb_bottom), "black")

    # draw time of day across top
    x_hr_incr = h_points / 24
    y_st = t_margin
    y_h = 12
    for hr in range(0, 24, 1):
        x = l_margin + hr * x_hr_incr
        draw.line((x, y_st, x, y_st - y_h), "black")
        y_h ^= 8
    for hr in range(0, 24, 2):
        draw.text((l_margin + hr * x_hr_incr + 3 * lb_text_margin, t_margin - 12), "%d:00" % hr, "black")

    # day of year down the side
    ddoy(draw, "2015.01.01", "Jan 1", l_margin, t_margin, v_mag)
    ddoy(draw, "2015.02.01", "Feb 1", l_margin, t_margin, v_mag)
    ddoy(draw, "2015.03.01", "Mar 1", l_margin, t_margin, v_mag)
    ddoy(draw, "2015.04.01", "Apr 1", l_margin, t_margin, v_mag)
    ddoy(draw, "2015.05.01", "May 1", l_margin, t_margin, v_mag)
    ddoy(draw, "2015.06.01", "Jun 1", l_margin, t_margin, v_mag)
    ddoy(draw, "2015.07.01", "Jul 1", l_margin, t_margin, v_mag)
    ddoy(draw, "2015.08.01", "Aug 1", l_margin, t_margin, v_mag)
    ddoy(draw, "2015.09.01", "Sep 1", l_margin, t_margin, v_mag)
    ddoy(draw, "2015.10.01", "Oct 1", l_margin, t_margin, v_mag)
    ddoy(draw, "2015.11.01", "Nov 1", l_margin, t_margin, v_mag)
    ddoy(draw, "2015.12.01", "Dec 1", l_margin, t_margin, v_mag)

    # little plus signs at key day times
    dplusses(draw, "2015.03.21", l_margin, t_margin, v_mag, h_points)
    dplusses(draw, "2015.06.21", l_margin, t_margin, v_mag, h_points)
    dplusses(draw, "2015.09.21", l_margin, t_margin, v_mag, h_points)
    dplusses(draw, "2015.12.21", l_margin, t_margin, v_mag, h_points)

    # Spit out the image
    fname = "twilight_lat-%0.0f%s.png" % (o_lat_deg, tilt_hint)
    image_output(img, fname, b64)
    return 0


def main_show_a_day_polar(o_lat_deg=Constants.OBSERVER_LAT_DEG,
                          axial_tilt=Constants.OBLIQUITY,
                          day=0,
                          date='',
                          b64=False):
    tilt_hint = "_tilt-%0.0f" % axial_tilt
    # tilt_legend = ", axial tilt: %0.1f" % axial_tilt

    # The run
    o_colat_rad = radians(90 - o_lat_deg)
    solarLat = SolarLat(axial_tilt)
    ds = DisplayState(strategy=3)
    if date != '':
        day = get_doy(date)

    print ("Twilight v%2.1f Observer is at %2.1f degrees north." % (TWILIGHT_VERSION, o_lat_deg))
    print ("  day of year=%d, axial tilt=%f" % (day, axial_tilt))

    l_margin = 30
    r_margin = 10
    t_margin = 60
    b_margin = 10
    radius = 300
    W = l_margin + radius * 2 + r_margin
    H = t_margin + radius * 2 + b_margin

    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)

    # circle center
    xc = l_margin + radius
    yc = t_margin + radius

    # draw the pattern
    min_per_day = float(24) * float(60)
    for min in range(0, 24 * 60):
        # draw the pie wedge for this minute
        fraction_tod = float(min) / min_per_day
        cos_tod = cos(fraction_tod * 2 * math.pi)
        sin_tod = sin(fraction_tod * 2 * math.pi)
        dx = cos_tod * radius
        dy = sin_tod * radius
        xe = xc + dx
        ye = yc + dy
        state = compute_display_state(day, fraction_tod, o_colat_rad, solarLat, ds)
        draw.line((xc, yc, xe, ye), state, width=2)
    for min in range(0, 24 * 60):
        # draw the blip to show the solar altitude
        fraction_tod = float(min) / min_per_day
        cos_tod = cos(fraction_tod * 2 * math.pi)
        sin_tod = sin(fraction_tod * 2 * math.pi)
        dx = cos_tod * radius
        dy = sin_tod * radius
        xe = xc + dx
        ye = yc + dy
        ca = compute_solar_coaltitude(day, fraction_tod, o_colat_rad, solarLat)

        plot_strategy=2
        if plot_strategy == 1:
            # plot by the sin of the altitude. Looks weird.
            if ca <= radians(90):
                color="black"
            else:
                color="white"
            xse = xc + dx * sin(ca)
            yse = yc + dy * sin(ca)

        if plot_strategy == 2:
            # plot linear angle. Looks weird.
            if ca <= radians(90):
                color="black"
                scale = ca * 2.0 / math.pi
            else:
                color="white"
                scale = (math.pi - ca) * 2.0 / math.pi
            xse = xc + dx * scale
            yse = yc + dy * scale

        # print ("Min=%d, ca=%f xc=%d, yc=%d, xe=%f, ye=%f, xse=%f, yse=%f " % (min, degrees(ca), xc, yc, xe, ye, xse, yse))
        draw.line((xse, yse, xse, yse), color, width=1)

    # Spit out the image
    fname = "twilight_polar_day_%s_lat-%0.0f%s.png" % (day, o_lat_deg, tilt_hint)
    image_output(img, fname, b64)
    return 0


def main_show_a_day_cartesian(o_lat_deg=Constants.OBSERVER_LAT_DEG,
                              axial_tilt=Constants.OBLIQUITY,
                              day=0,
                              date='',
                              b64=False):
    tilt_hint = "_tilt-%0.0f" % axial_tilt
    # tilt_legend = ", axial tilt: %0.1f" % axial_tilt

    # The run
    o_colat_rad = radians(90 - o_lat_deg)
    solarLat = SolarLat(axial_tilt)
    ds = DisplayState(strategy=3)
    if date != '':
        day = get_doy(date)

    if not b64:
        print("Twilight v%2.1f Observer is at %2.1f degrees north." % (TWILIGHT_VERSION, o_lat_deg))
        print("  day of year=%d, date: %s, axial tilt=%f" % (day, get_date_of_doy(day), axial_tilt))

    l_margin = 50
    r_margin = 100 # leaves room for legend-box-right
    t_margin = 40
    b_margin = 10
    h_points = 24*60
    v_points = 800

    W = l_margin + h_points + r_margin
    H = t_margin + v_points + b_margin

    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)

    # draw the pattern
    # draw the vertical bars for each minute
    min_per_day = float(24) * float(60)
    for minute in range(0, 24 * 60):
        fraction_tod = float(minute) / min_per_day
        state = compute_display_state(day, fraction_tod, o_colat_rad, solarLat, ds)
        x = l_margin + minute
        draw.line((x, t_margin, x, t_margin + v_points), state, width=1)

    # draw horizon
    y = t_margin + v_points / 2
    draw.line((l_margin, y, l_margin + h_points, y), "green", width=1)

    # draw the blips to show the solar altitude
    for minute in range(0, 24 * 60):
        fraction_tod = float(minute) / min_per_day
        ca = compute_solar_coaltitude(day, fraction_tod, o_colat_rad, solarLat)
        x = l_margin + minute

        color = "black" if ca <= radians(90) else "white"
        yse = t_margin + v_points * ca / math.pi

        draw.line((x, yse, x, yse), color, width=1)

    # Draw the title and other facts
    ttext = "Altitude of Sun vs. Time of Day."
    draw.text(((l_margin + h_points + r_margin) / 2, 1),
              ttext,
              "black",
              anchor="ma")
    draw.text((2,1),
              "Solar Twilight v%s" % TWILIGHT_VERSION,
              "black")
    draw.text((2,13),
              "Observer latitude: %0.1f, Date: %s, Day of year: %d" % (o_lat_deg, get_date_of_doy(day), day),
              "black")

    # draw fancy legend box right "lbr"
    # the 0,0 for lbr is the upper right corner of the main drawing
    lbr_top = t_margin
    lbr_left = l_margin + h_points
    lbr_l_margin = 3
    lbr_w_boxes = 60

    lbr_x_o = lbr_left + lbr_l_margin
    lbr_y_o = lbr_top

    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, 90, 75, 'L6', '')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, 75, 60, 'L5', '')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, 60, 45, 'L4', '')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, 45, 30, 'L3', '')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, 30, 15, 'L2', '')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, 15, 0, 'L1', '')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, 0, -6, 'C', 'civil')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, -6, -12, 'N', 'nautical')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, -12, -18, 'A', 'astro-', 'nomical')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, -18, -42, 'D1', '')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, -42, -66, 'D2', '')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, -66, -90, 'D3', '')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, -90, -90, 'D3', '')

    draw.text((lbr_x_o + 5, lbr_y_o - 24), "chart", "black")
    draw.text((lbr_x_o + 5, lbr_y_o - 12), "colors", "black")

    draw.line((lbr_x_o, lbr_y_o, lbr_x_o + lbr_w_boxes, lbr_y_o), "black")
    draw.line((lbr_x_o, lbr_y_o - 26, lbr_x_o + lbr_w_boxes, lbr_y_o - 26), "black")
    draw.line((lbr_x_o, lbr_y_o - 26, lbr_x_o, lbr_y_o + v_points / 2), "black")
    draw.line((lbr_x_o + lbr_w_boxes, lbr_y_o - 26, lbr_x_o + lbr_w_boxes, lbr_y_o + v_points / 2), "black")

    # draw time of day across top
    x_hr_incr = h_points / 24
    y_st = t_margin
    y_h = 12
    for hr in range(0, 24, 1):
        x = l_margin + hr * x_hr_incr
        draw.line((x, y_st, x, y_st - y_h), "black")
        y_h ^= 8
    for hr in range(0, 24, 2):
        draw.text((l_margin + hr * x_hr_incr + 3 * 1, t_margin - 12), "%d:00" % hr, "black")

    # draw solar altitude legend down the side
    dalt(draw,  90, " zenith", l_margin, t_margin, v_points)
    dalt(draw,  80, "     80", l_margin, t_margin, v_points)
    dalt(draw,  70, "     70", l_margin, t_margin, v_points)
    dalt(draw,  60, "     60", l_margin, t_margin, v_points)
    dalt(draw,  50, "     50", l_margin, t_margin, v_points)
    dalt(draw,  40, "     40", l_margin, t_margin, v_points)
    dalt(draw,  30, "     30", l_margin, t_margin, v_points)
    dalt(draw,  20, "     20", l_margin, t_margin, v_points)
    dalt(draw,  10, "     10", l_margin, t_margin, v_points)
    dalt(draw,  00, "horizon", l_margin, t_margin, v_points)
    dalt(draw, -10, "    -10", l_margin, t_margin, v_points)
    dalt(draw, -20, "    -20", l_margin, t_margin, v_points)
    dalt(draw, -30, "    -30", l_margin, t_margin, v_points)
    dalt(draw, -40, "    -40", l_margin, t_margin, v_points)
    dalt(draw, -50, "    -50", l_margin, t_margin, v_points)
    dalt(draw, -60, "    -60", l_margin, t_margin, v_points)
    dalt(draw, -70, "    -70", l_margin, t_margin, v_points)
    dalt(draw, -80, "    -80", l_margin, t_margin, v_points)
    dalt(draw, -90, "  nadir", l_margin, t_margin, v_points)

    # Spit out the image
    fname = "twilight_cart_day_%s_lat-%0.0f%s.png" % (day, o_lat_deg, tilt_hint)
    image_output(img, fname, b64)
    return 0


def main_show_a_day_cartesian_panels(o_lat_deg=Constants.OBSERVER_LAT_DEG,
                                     axial_tilt=Constants.OBLIQUITY,
                                     day=0,
                                     date='',
                                     b64=False,
                                     panel_az=180,
                                     panel_el=90):
    tilt_hint = "_tilt-%0.0f" % axial_tilt
    # tilt_legend = ", axial tilt: %0.1f" % axial_tilt

    # The run
    o_colat_rad = radians(90 - o_lat_deg)
    solarLat = SolarLat(axial_tilt)
    ds = DisplayState(strategy=3)
    if date != '':
        day = get_doy(date)

    if not b64:
        print("Twilight v%2.1f Observer is at %2.1f degrees north. Panel az, el = %f, %s" %
              (TWILIGHT_VERSION, o_lat_deg, panel_az, panel_el))
        print("  day of year=%d, date: %s, axial tilt=%f" % (day, get_date_of_doy(day), axial_tilt))

    l_margin = 50
    r_margin = 100  # leaves room for legend-box-right
    t_margin = 40
    b_margin = 10
    h_points = 24*60
    v_points = 800

    W = l_margin + h_points + r_margin
    H = t_margin + v_points + b_margin

    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)

    # draw the pattern
    # draw the vertical bars for each minute
    min_per_day = float(24) * float(60)
    for minute in range(0, 24 * 60):
        fraction_tod = float(minute) / min_per_day
        state = compute_display_state(day, fraction_tod, o_colat_rad, solarLat, ds)
        x = l_margin + minute
        draw.line((x, t_margin, x, t_margin + v_points), state, width=1)

    # draw horizon
    y = t_margin + v_points / 2
    draw.line((l_margin, y, l_margin + h_points, y), "green", width=1)

    # draw the blips to show the solar altitude
    for minute in range(0, 24 * 60):
        fraction_tod = float(minute) / min_per_day
        ca = compute_solar_coaltitude(day, fraction_tod, o_colat_rad, solarLat)
        x = l_margin + minute

        color = "black" if ca <= radians(90) else "white"
        yse = t_margin + v_points * ca / math.pi

        draw.line((x, yse, x, yse), color, width=1)

    # Draw the title and other facts
    ttext = "Altitude of Sun vs. Time of Day."
    w, h = draw.textsize(ttext)
    draw.text(((W - w ) / 2, 1),
              ttext,
              "black")
    draw.text((2,1),
              "Solar Twilight v%s" % TWILIGHT_VERSION,
              "black")
    draw.text((2,13),
              "Observer latitude: %0.1f, Date: %s, Day of year: %d" % (o_lat_deg, get_date_of_doy(day), day),
              "black")

    # draw fancy legend box right "lbr"
    # the 0,0 for lbr is the upper right corner of the main drawing
    lbr_top = t_margin
    lbr_left = l_margin + h_points
    lbr_l_margin = 3
    lbr_w_boxes = 60

    lbr_x_o = lbr_left + lbr_l_margin
    lbr_y_o = lbr_top

    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, 90, 75, 'L6', '')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, 75, 60, 'L5', '')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, 60, 45, 'L4', '')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, 45, 30, 'L3', '')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, 30, 15, 'L2', '')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, 15, 0, 'L1', '')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, 0, -6, 'C', 'civil')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, -6, -12, 'N', 'nautical')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, -12, -18, 'A', 'astro-', 'nomical')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, -18, -42, 'D1', '')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, -42, -66, 'D2', '')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, -66, -90, 'D3', '')
    ddoy_lbr(draw, ds, lbr_x_o, lbr_y_o, v_points, lbr_w_boxes, -90, -90, 'D3', '')

    draw.text((lbr_x_o + 5, lbr_y_o - 24), "chart", "black")
    draw.text((lbr_x_o + 5, lbr_y_o - 12), "colors", "black")

    draw.line((lbr_x_o, lbr_y_o, lbr_x_o + lbr_w_boxes, lbr_y_o), "black")
    draw.line((lbr_x_o, lbr_y_o - 26, lbr_x_o + lbr_w_boxes, lbr_y_o - 26), "black")
    draw.line((lbr_x_o, lbr_y_o - 26, lbr_x_o, lbr_y_o + v_points / 2), "black")
    draw.line((lbr_x_o + lbr_w_boxes, lbr_y_o - 26, lbr_x_o + lbr_w_boxes, lbr_y_o + v_points / 2), "black")

    # draw time of day across top
    x_hr_incr = h_points / 24
    y_st = t_margin
    y_h = 12
    for hr in range(0, 24, 1):
        x = l_margin + hr * x_hr_incr
        draw.line((x, y_st, x, y_st - y_h), "black")
        y_h ^= 8
    for hr in range(0, 24, 2):
        draw.text((l_margin + hr * x_hr_incr + 3 * 1, t_margin - 12), "%d:00" % hr, "black")

    # draw solar altitude legend down the side
    dalt(draw,  90, " zenith", l_margin, t_margin, v_points)
    dalt(draw,  80, "     80", l_margin, t_margin, v_points)
    dalt(draw,  70, "     70", l_margin, t_margin, v_points)
    dalt(draw,  60, "     60", l_margin, t_margin, v_points)
    dalt(draw,  50, "     50", l_margin, t_margin, v_points)
    dalt(draw,  40, "     40", l_margin, t_margin, v_points)
    dalt(draw,  30, "     30", l_margin, t_margin, v_points)
    dalt(draw,  20, "     20", l_margin, t_margin, v_points)
    dalt(draw,  10, "     10", l_margin, t_margin, v_points)
    dalt(draw,  00, "horizon", l_margin, t_margin, v_points)
    dalt(draw, -10, "    -10", l_margin, t_margin, v_points)
    dalt(draw, -20, "    -20", l_margin, t_margin, v_points)
    dalt(draw, -30, "    -30", l_margin, t_margin, v_points)
    dalt(draw, -40, "    -40", l_margin, t_margin, v_points)
    dalt(draw, -50, "    -50", l_margin, t_margin, v_points)
    dalt(draw, -60, "    -60", l_margin, t_margin, v_points)
    dalt(draw, -70, "    -70", l_margin, t_margin, v_points)
    dalt(draw, -80, "    -80", l_margin, t_margin, v_points)
    dalt(draw, -90, "  nadir", l_margin, t_margin, v_points)

    # Spit out the image
    fname = "twilight_cart_day_%s_lat-%0.0f%s.png" % (day, o_lat_deg, tilt_hint)
    image_output(img, fname, b64)
    return 0


def main_except(argv):
    parser = OptionParser()
    parser.add_option("-f", "--file", action="store", type="string", dest="filename",
                      help="Write image to FILE", metavar="FILE")
    parser.add_option("-o", "--o-lat", action="store", type="float", dest="o_lat",
                      help="Observer latitude in degrees north", default=Constants.OBSERVER_LAT_DEG)
    parser.add_option("-t", "--tilt", action="store", type="float", dest="tilt",
                      help="Axial tilt in degrees", default=Constants.OBLIQUITY)
    parser.add_option("--show-day", action="store_true", dest="showDay", default=False,
                      help="Show day-view instead of year-view")
    parser.add_option("--polar", action="store_true", dest="polar", default=False,
                      help="Show day-view in polar coordinates instead of cartesion coordinates")
    parser.add_option("-d", "--day", action="store", type="int", dest="day", default=0,
                      help="In day-view, which day in range 0..364 to render. default=0")
    parser.add_option("--date", action="store", dest="date", default="",
                      help="In day-view, which day of year to view. Use format 'YYYY.MM.DD'. Use --day or --date but not both.")
    parser.add_option("-b", "--base64",  action="store_true", dest="b64", default=False,
                      help="Send base64 image to stdout")

    #
    (options, args) = parser.parse_args()
    #
    if options.showDay:
        if options.polar:
            main_show_a_day_polar(options.o_lat, options.tilt, options.day, options.date, options.b64)
        else:
            main_show_a_day_cartesian(options.o_lat, options.tilt, options.day, options.date, options.b64)
    else:
        if options.polar:
            raise Exception("The --polar option is valid only in --show-day day view")
        main_show_a_year(options.o_lat, options.tilt, 1, options.b64)


def main(argv):
    try:
        main_except(argv)
        return 0
    #    except ExitStatus, e:
    #        return e.status
    except Exception as e:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    main(sys.argv)