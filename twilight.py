#!/usr/bin/python
# twilight
# Use the SolarLat package to discover cool stuff about twilight.

from optparse import OptionParser
from SolarLat import *
from PIL import Image, ImageDraw
import datetime
import traceback
import SG_sunpos_ultimate_azi_atan2 as SG
import string

TWILIGHT_VERSION = "2.1.1"

SG_COMPUTE_INTERVAL_MINUTES = 1

DEGREE_SYMBOL = "°"

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
        # ranges measured by zenith angle
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

        # angles defining ranges as observer +/- elevation angles in degrees
        self.elevations_in_deg = [-90, -66, -42, -18, -12, -6, 0, 15, 30, 45, 60, 75, 90]

        # colors[] holds the set-ansi-color escape sequence
        self.color_ansi = {"L": BColors.WHITE,    # light
                           "C": BColors.YELLOW,   # civil
                           "N": BColors.MAGENTA,  # nautical
                           "A": BColors.BLUE,     # astronomical
                           "D": BColors.BLACK}    # dark
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

    def get_display_code(self, zenith_angle_rad):
        """
        :param zenith_angle_rad: zenith angle in radians
        :return: display code
        """
        return  \
                "L6" if zenith_angle_rad <= self.rad_max_L6 else \
                "L5" if zenith_angle_rad <= self.rad_max_L5 else \
                "L4" if zenith_angle_rad <= self.rad_max_L4 else \
                "L3" if zenith_angle_rad <= self.rad_max_L3 else \
                "L2" if zenith_angle_rad <= self.rad_max_L2 else \
                "L1" if zenith_angle_rad <= self.rad_max_L1 else \
                "C" if zenith_angle_rad <= self.rad_max_civil else \
                "N" if zenith_angle_rad <= self.rad_max_nautical else \
                "A" if zenith_angle_rad <= self.rad_max_astronomical else \
                "D1" if zenith_angle_rad <= self.rad_max_D1 else \
                "D2" if zenith_angle_rad <= self.rad_max_D2 else \
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


def ddoy(draw, doy_string, doy_text, l_margin, t_margin, v_mag, width, grid_color):
    """
    Given a day-of-year string for a non-leap year
    Draw the doy_text and a tick mark in the left margin.
    :param draw       :
    :param doy_string :
    :param doy_text   :
    :param l_margin   :
    :param t_margin   :
    :param v_mag      :
    :param width      : plot diagram pixel width
    :param grid_color : draw this color line across plot diagram
    :return:
    """
    doy = get_doy(doy_string)
    x_o = 0
    x_e = l_margin
    y = t_margin + doy * v_mag
    draw.line((x_o, y, x_e, y), "black")
    # drawing the grid_color (green) grosses out the diagram
    # soften it up a little drawing only some pixels
    for x_o in range(l_margin, l_margin + width, 8):
        x_e = x_o + 1
        draw.line((x_o, y, x_e, y), grid_color)
    draw.text((1, y + 1), doy_text, "black")
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

def draw_titles(draw, width, l1, l2, l3):
    title_y1 = 2
    title_y2 = title_y1 + (1 * 12)
    title_y3 = title_y1 + (2 * 12)
    draw.text((2,title_y1), l1, "black")
    draw.text((2,title_y2), l2, "black")
    draw.text((2,title_y3), l3, "black")

    # Draw source facts
    source_info_x = width - 230
    source_info_x2 = width - 190
    draw.text((source_info_x, title_y1),
              "project:",
              "black")
    draw.text((source_info_x2, title_y1),
              "https://github.com/ChugR/solar-lat",
              "black")
    draw.text((source_info_x, title_y2),
              "file:",
              "black")
    draw.text((source_info_x2, title_y2),
              "twilight.py",
              "black")
    draw.text((source_info_x, title_y3),
              "version:",
              "black")
    draw.text((source_info_x2, title_y3),
              "%s" % TWILIGHT_VERSION,
              "black")



def main_show_a_year(options):
    #
    # mission code
    # Show 2019 ephemeris data
    #
    # Display as:
    #   .png file
    #
    # Settings for this run
    # arg 1: observer's latitude [42]
    # arg 2: time between sample points in minutes
    #
    # This program considers only a point at some latitude on the prime meridian north of the equator.
    # South of the equator might work, but it hasn't been tested.
    # There is no compensation for the fairly simple longitude correction where the longitude is
    # not centered on the local time zone. Also, there is no accommodation for daylight savings time that
    # shifts the plot by political DST rules.
    #
    # function args
    o_lat_deg = options.o_lat

    # observer location
    o_lon_deg = 0.0  # prime meridian

    ds = DisplayState(strategy=3)
    # print ("Twilight v%2.1f Observer is at %2.1f degrees north." % (TWILIGHT_VERSION, o_lat_deg))

    # image layout (in pixels)
    l_margin = 30
    r_margin = 10
    t_margin = 75
    b_margin = 10

    # horizontal - one pixel per minute
    # vertical   - 3 pixels per day
    h_mag = 1
    v_mag = 3

    # gross generalizations: 24 hr/day, 60 min/hr, 365 day/year
    h_points = 24 * 60
    v_points = 365 * v_mag

    W = l_margin + h_points + r_margin
    H = t_margin + v_points + b_margin

    # helpful grid lines
    grid_color = "green"

    # The PIL and draw canvas
    img = Image.new("RGB", (int(W), int(H)), "white")
    draw = ImageDraw.Draw(img)

    # Draw the main diagram
    base_dt = datetime.datetime(2019, 1, 1)
    working_y = t_margin - v_mag
    for pday in range(0, 365):
        working_y += v_mag
        working_x = l_margin - h_mag
        last_x_start = None
        last_x_end = None
        last_color = None
        for phour in range(0, 24):
            for pmin in range(0, 60):
                working_x += h_mag
                td_minute = datetime.timedelta(days=pday, hours=phour, minutes=pmin)
                date = base_dt + td_minute
                sun_zenith_degrees, sun_azimuth_degrees, sun_lat, sun_lon, esd, eot = \
                    SG.solar_geometry(date, o_lat_deg, o_lon_deg)
                color = ds.get_display(radians(sun_zenith_degrees))
                if last_x_start is None:
                    # initialize accumulated colors
                    last_x_start = working_x
                    last_x_end = working_x
                    last_color = color
                    continue
                else:
                    if last_color == color:
                        # accumulate another minute at this color
                        last_x_end = working_x
                        continue
                    else:
                        # emit current accumulation, start next
                        draw.rectangle((last_x_start, working_y, last_x_end + h_mag, working_y + v_mag), last_color)
                        last_x_start = working_x
                        last_x_end = working_x
                        last_color = color
        # emit last color block accumulation
        draw.rectangle((last_x_start, working_y, last_x_end + h_mag, working_y + v_mag), last_color)

    # Draw the plot title
    draw_titles(draw, W,
                "Solar-lat twilight year view",
                "Altitude of sun. Colors indicate height of sun above or below horizon",
                "Observer on prime meridian at latitude: %0.1f" % o_lat_deg)

    # Draw the legend
    # define legend box "lb"
    lb_top = 0
    lb_left = 450
    lb_width = 600  # better if divisible by 12

    lb_n_color_boxes = 12

    # legend box has [text divisions; colors; altitude in degrees]
    lb_horizontal_div_height = 15
    lb_horizontal_divs = 3
    lb_height = lb_horizontal_div_height * lb_horizontal_divs

    lb_bottom = lb_top + lb_height
    lb_right = lb_left + lb_width

    lb_text_margin = 2
    lb_width = lb_right - lb_left

    lb_row1_text_y = lb_top + lb_horizontal_div_height * 0 + lb_text_margin
    lb_row2_text_y = lb_top + lb_horizontal_div_height * 1 + lb_text_margin
    lb_row3_text_y = lb_top + lb_horizontal_div_height * 2 + lb_text_margin + 3

    # draw the legend color boxes
    x = lb_left
    y0 = 0 * lb_horizontal_div_height
    y1 = 1 * lb_horizontal_div_height
    y2 = 2 * lb_horizontal_div_height
    y3 = 3 * lb_horizontal_div_height
    x_inc = lb_width / lb_n_color_boxes
    def fill_rect(n, color_key):
        fr_x0 = float(lb_left + (n * x_inc))
        fr_y0 = float(y1)
        fr_x1 = float(lb_left + ((n + 1) * x_inc))
        fr_y1 = float(y2)
        draw.rectangle((fr_x0, fr_y0, fr_x1, fr_y1), fill=ds.color_pil[color_key])

    def draw_rects(color_keys):
        for i in range(len(color_keys)):
            fill_rect(i, color_keys[i])

    draw_rects(['D3', 'D2', 'D1', 'A', 'N', 'C', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6'])

    # draw legend box text and lines
    draw.text((lb_left + lb_text_margin + 1 * (lb_width / lb_n_color_boxes), lb_row1_text_y), "night", "black")
    draw.text((lb_left + lb_text_margin + 4 * (lb_width / lb_n_color_boxes), lb_row1_text_y), "twilight", "black")
    draw.text((lb_left + lb_text_margin + 8.5 * (lb_width / lb_n_color_boxes), lb_row1_text_y), "day", "black")

    draw.text((lb_left + lb_text_margin + 3 * (lb_width / lb_n_color_boxes), lb_row2_text_y), " ASTRO", "white")
    draw.text((lb_left + lb_text_margin + 4 * (lb_width / lb_n_color_boxes), lb_row2_text_y), " NAUT", "white")
    draw.text((lb_left + lb_text_margin + 5 * (lb_width / lb_n_color_boxes), lb_row2_text_y), " CIVIL", "white")

    # draw legend box text labels
    draw.text((lb_left - 80, lb_row1_text_y),
              "daytime phase", "black")
    draw.text((lb_left - 80, lb_row2_text_y),
              "plot color", "black")
    draw.text((lb_left - 80, lb_row3_text_y),
              "solar altitude", "black")


    # draw tick marks dividing color boxes
    for n in range(len(ds.elevations_in_deg)):
        fr_x = float(lb_left + (n * x_inc))
        fr_y0 = float(y2)
        fr_y1 = float(y2 + 3)
        draw.line((fr_x, fr_y0, fr_x, fr_y1), "black")

    for n in range(len(ds.elevations_in_deg)):
        xx_x = lb_left + (n * x_inc) - 7
        xx_y = lb_row3_text_y
        xx_s = str(ds.elevations_in_deg[n]) + DEGREE_SYMBOL
        draw.text((xx_x, xx_y), xx_s, "black")

    draw.rectangle((lb_left, lb_top, lb_right, y2), outline="black")
    draw.line((lb_left, lb_horizontal_div_height, lb_right, lb_horizontal_div_height), "black")

    draw.line((lb_left + 3 * x_inc, lb_top, lb_left + 3 * x_inc, y2), "black")
    draw.line((lb_left + 6 * x_inc, lb_top, lb_left + 6 * x_inc, y2), "black")

    # draw time of day across top
    x_hr_incr = h_points / 24
    y_st = t_margin
    # axis title
    draw.text((l_margin + 3 * lb_text_margin, t_margin - 24), "GMT", "black")
    # tick marks
    y_h = 12  # start with a longer tick mark
    for hr in range(0, 24, 1):
        x = l_margin + hr * x_hr_incr
        draw.line((x, y_st, x, y_st - y_h), "black")
        y_h ^= 8  # toggle between longer and shorter tick mark
        for y_o in range(t_margin, t_margin + v_points, 8):
            draw.line((x, y_o, x, y_o + 1), grid_color)
    # axis hour text
    for hr in range(0, 24, 2):
        draw.text((l_margin + hr * x_hr_incr + 3 * lb_text_margin, t_margin - 12), "%d:00" % hr, "black")

    # day of year down the side
    ddoy(draw, "2015.01.01", "Jan 1", l_margin, t_margin, v_mag, h_points, grid_color)
    ddoy(draw, "2015.02.01", "Feb 1", l_margin, t_margin, v_mag, h_points, grid_color)
    ddoy(draw, "2015.03.01", "Mar 1", l_margin, t_margin, v_mag, h_points, grid_color)
    ddoy(draw, "2015.04.01", "Apr 1", l_margin, t_margin, v_mag, h_points, grid_color)
    ddoy(draw, "2015.05.01", "May 1", l_margin, t_margin, v_mag, h_points, grid_color)
    ddoy(draw, "2015.06.01", "Jun 1", l_margin, t_margin, v_mag, h_points, grid_color)
    ddoy(draw, "2015.07.01", "Jul 1", l_margin, t_margin, v_mag, h_points, grid_color)
    ddoy(draw, "2015.08.01", "Aug 1", l_margin, t_margin, v_mag, h_points, grid_color)
    ddoy(draw, "2015.09.01", "Sep 1", l_margin, t_margin, v_mag, h_points, grid_color)
    ddoy(draw, "2015.10.01", "Oct 1", l_margin, t_margin, v_mag, h_points, grid_color)
    ddoy(draw, "2015.11.01", "Nov 1", l_margin, t_margin, v_mag, h_points, grid_color)
    ddoy(draw, "2015.12.01", "Dec 1", l_margin, t_margin, v_mag, h_points, grid_color)

    # little plus signs at key day times
    dplusses(draw, "2015.03.21", l_margin, t_margin, v_mag, h_points)
    dplusses(draw, "2015.06.21", l_margin, t_margin, v_mag, h_points)
    dplusses(draw, "2015.09.21", l_margin, t_margin, v_mag, h_points)
    dplusses(draw, "2015.12.21", l_margin, t_margin, v_mag, h_points)

    # Optionally save the image
    if options.filename is not None:
        img.save(options.filename, "PNG")

    # Optionally skip autoviewing the image
    if not options.noautoview:
        img.show()

    return 0


def polar_text_offsets(azimuth_deg):
    # Given an azimuth angle in degrees, return x,y text offsets for labels
    text_height = 9
    text_width  = 18
    spacing = 2
    result = ()
    if azimuth_deg <= 90.0:
        result = (-text_width, spacing)
    elif azimuth_deg <= 180.0:
        result = (-text_width, -(text_height + spacing))
    elif azimuth_deg <= 270.0:
        result = (spacing, -(text_height + spacing))
    else:
        result = (spacing, spacing)
    return result


def main_show_a_day_polar(options):

    # function args
    o_lat_deg = options.o_lat
    day = options.day
    date = options.date

    # observer location
    o_lon_deg = 0.0  # prime meridian

    ds = DisplayState(strategy=3)
    if date != '':
        day = get_doy(date)

    print ("Twilight v%s Observer is at %2.1f degrees north." % (TWILIGHT_VERSION, o_lat_deg))
    print ("  date: %s, day of year: %d" % (get_date_of_doy(day), day))

    l_margin = 50
    r_margin = 50
    t_margin = 76
    b_margin = 20
    radius = 450
    W = l_margin + radius * 2 + r_margin
    H = t_margin + radius * 2 + b_margin

    TIME_COLOR = "green"

    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)

    # circle center
    xc = l_margin + radius
    yc = t_margin + radius

    # This diagram plots the altitude against the azimuth of the sun.
    # The observer is at the center of the diagram facing south
    #   North (azimuth=0)   is at  6 o'clock
    #   South (azimuth=180) is at 12 o'clock
    # As the solar azimuth angle increases it moves clockwise in the diagram.
    # Solar altitudes are plotted with
    #   nadir is the circle center
    #   zenith is the circle circumference.

    zeniths  = [0.0] * (24 * 60)
    azimuths = [0.0] * (24 * 60)
    colors   = [""]  * (24 * 60)
    dcoses_az   = [0.0] * (24 * 60)
    dsines_az   = [0.0] * (24 * 60)

    # compute this plot's numbers
    base_dt = datetime.datetime(2019, 1, 1) + datetime.timedelta(days=(day+1))
    for phour in range(0, 24):
        for pmin in range(0, 60):
            this_minute = phour * 60 + pmin
            td_minute = datetime.timedelta(hours=phour, minutes=pmin)
            date = base_dt + td_minute
            sun_zenith_degrees, sun_azimuth_degrees, sun_lat, sun_lon, esd, eot = \
                SG.solar_geometry(date, o_lat_deg, o_lon_deg)

            assert(sun_zenith_degrees >=   0.0)
            assert(sun_zenith_degrees <= 180.0)

            color = ds.get_display(radians(sun_zenith_degrees))
            dcos_az = cos(radians(sun_azimuth_degrees))
            dsin_az = sin(radians(sun_azimuth_degrees))

            zeniths[this_minute] = sun_zenith_degrees
            azimuths[this_minute] = sun_azimuth_degrees
            colors[this_minute] = color
            dcoses_az[this_minute] = dcos_az
            dsines_az[this_minute] = dsin_az

    # plot the background colors
    # zenith angles: 0, 15, 30, ... for each display color bound.
    # ignore the last one
    zas = [x + 90 for x in reversed(ds.elevations_in_deg[1:])]
    # color codes corresponding to entries in zas
    za_ccs = ["L6", "L5", "L4", "L3", "L2", "L1", "C", "N", "A", "D1", "D2", "D3"]

    for zai in range(len(zas)):
        za = zas[zai]
        color = ds.color_pil[za_ccs[zai]]
        bg_radius = int((float(za) / 180.0) * radius)
        ulx = xc - bg_radius
        uly = yc - bg_radius
        lrx = xc + bg_radius
        lry = yc + bg_radius
        draw.ellipse((ulx, uly, lrx, lry), fill=color)

    # Enclosing circle
    ulx = xc - radius
    uly = yc - radius
    lrx = xc + radius
    lry = yc + radius
    draw.ellipse((ulx, uly, lrx, lry), fill=None, outline="black")

    # draw aa/el chart, time ticks and labels
    for phour in range(0, 24):
        for pmin in range(0, 60):
            this_minute = phour * 60 + pmin
            xtick = xc - int(dsines_az[this_minute] * (1.0 - (zeniths[this_minute] / 180.0)) * radius)
            ytick = yc + int(dcoses_az[this_minute] * (1.0 - (zeniths[this_minute] / 180.0)) * radius)
            color = "white" if zeniths[this_minute] > 90.0 else "black"
            draw.line((xtick, ytick, xtick, ytick), color, width=2)

            if pmin == 0:
                # Every hour gets a tick mark
                xtick2 = xc - int(dsines_az[this_minute] * (1.0 - (zeniths[this_minute] / 180.0)) * (radius + 10))
                ytick2 = yc + int(dcoses_az[this_minute] * (1.0 - (zeniths[this_minute] / 180.0)) * (radius + 10))
                draw.line((xtick, ytick, xtick2, ytick2), TIME_COLOR, width=1)

                # Every other hour gets a label
                if phour % 2 == 0:
                    xtick3 = xc - int(dsines_az[this_minute] * (1.0 - (zeniths[this_minute] / 180.0)) * (radius + 15))
                    ytick3 = yc + int(dcoses_az[this_minute] * (1.0 - (zeniths[this_minute] / 180.0)) * (radius + 15))
                    xoff, yoff = polar_text_offsets((azimuths[this_minute] + 90.0) % 360.0)
                    draw.text((xtick3 + xoff, ytick3 + yoff), "%d:00"%phour, TIME_COLOR)
                pass

    # draw azimuth angles around circle
    for az_deg in range(0, 360, 10):
        xtick = xc - int(sin(radians(az_deg)) * (radius - 2))
        ytick = yc + int(cos(radians(az_deg)) * (radius - 2))
        xtick2 = xc - int(sin(radians(az_deg)) * (radius + 2))
        ytick2 = yc + int(cos(radians(az_deg)) * (radius + 2))
        draw.line((xtick, ytick, xtick2, ytick2), "black", width=1)

        xoff, yoff = polar_text_offsets(az_deg)
        label = "%d%s"%(az_deg, DEGREE_SYMBOL)
        if az_deg == 0:
            label = label + " - N"
        elif az_deg == 90:
            label = "E\n" + label
            yoff -= 12
        elif az_deg == 180:
            label = label + " - S"
        elif az_deg == 270:
            label = "W\n" + label

        draw.text((xtick2 + xoff, ytick2 + yoff), label, "black")

    # Draw the title and other facts
    ttext = "Solar-lat twilight polar day view - altitude and azimuth of sun at time in GMT"
    draw.text((W / 2, 2),
              ttext,
              "black",
              anchor="ma")

    draw_titles(draw, W,
                "Solar-lat twilight polar day view",
                "Altitude of sun. Colors indicate height of sun above or below horizon",
                "Observer on prime meridian at latitude: %0.1f, Date: %s, Day of year: %d"
                % (o_lat_deg, get_date_of_doy(day), day))

    # Optionally save the image
    if options.filename is not None:
        img.save(options.filename, "PNG")

    # Optionally skip autoviewing the image
    if not options.noautoview:
        img.show()

    return 0


def main_show_a_day_cartesian(options):

    # function args
    o_lat_deg = options.o_lat
    day = options.day
    date = options.date

    # Observer location
    o_lon_deg = 0.0  # prime meridian

    ds = DisplayState(strategy=3)
    if date != '':
        day = get_doy(date)

    # image layout (in pixels)
    l_margin = 50
    r_margin = 100  # leaves room for legend-box-right
    t_margin = 60
    b_margin = 10
    h_points = 24*60
    v_points = 800

    W = l_margin + h_points + r_margin
    H = t_margin + v_points + b_margin

    # helpful grid lines
    grid_color = "green"

    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)

    # draw the diagram
    base_dt = datetime.datetime(2019, 1, 1) + datetime.timedelta(days=(day+1))
    for minute in range(0, 24 * 60):
        # get solar geometry for this minute
        td_minute = datetime.timedelta(minutes=minute)
        date = base_dt + td_minute
        sun_zenith_degrees, sun_azimuth_degrees, sun_lat, sun_lon, esd, eot = \
            SG.solar_geometry(date, o_lat_deg, o_lon_deg)

        # draw the colorized vertical bar for this minute
        color = ds.get_display(radians(sun_zenith_degrees))
        x = l_margin + minute
        draw.line((x, t_margin, x, t_margin + v_points), color, width=1)

        # draw the blip to show the solar altitude for this minute
        color = "black" if sun_zenith_degrees <= 90 else "white"
        yse = t_margin + int((float(v_points) / 180.0) * sun_zenith_degrees)

        draw.line((x, yse, x, yse), color, width=1)

    # draw horizon
    y = t_margin + v_points / 2
    draw.line((l_margin, y, l_margin + h_points, y), "green", width=1)

    # Draw the title and other facts
    ttext = "Solar-lat twilight day view - altitude of sun vs. GMT"
    draw.text(((l_margin + h_points + r_margin) / 2, 2),
              ttext,
              "black",
              anchor="ma")

    draw_titles(draw, W,
                "Solar-lat twilight day view",
                "Altitude of sun. Colors indicate height of sun above or below horizon",
                "Observer on prime meridian at latitude: %0.1f, Date: %s, Day of year: %d" %
                (o_lat_deg, get_date_of_doy(day), day)
                )

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

    draw.text((lbr_x_o + 5, lbr_y_o - 24), "twilight", "black")
    draw.text((lbr_x_o + 5, lbr_y_o - 12), "condition", "black")

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

    # draw graph grids
    for hr in range(0, 24, 1):
        x = l_margin + hr * x_hr_incr
        for y_o in range(t_margin, t_margin + v_points, 20):
            draw.line((x, y_o, x, y_o + 1), grid_color)
    y_base = t_margin + (v_points / 2)
    for elevation in range(10, 90, 10):  # elevation degrees from horizon
        pixels_per_degree = float(v_points) / 180.0
        y_off = int(float(elevation) * pixels_per_degree)
        for x_o in range(l_margin, l_margin + h_points, 20):
            draw.line((x_o, y_base - y_off, x_o, y_base - y_off), grid_color)
            draw.line((x_o, y_base + y_off, x_o, y_base + y_off), grid_color)

    # Optionally save the image
    if options.filename is not None:
        img.save(options.filename, "PNG")

    # Optionally skip autoviewing the image
    if not options.noautoview:
        img.show()

    return 0


def check_problematic_filename(filename):
    # return true if given non-blank filename contains no problematic characters
    if len(filename) == 0:
        return False  # name may not be blank
    for c in filename:
        if c not in string.printable:
            return False  # printable chars only
        if c in string.whitespace:
            return False  # whitespace disallowed
        if c in r"/\?%*:|<>'`":
            return False  # problematic for various reasons
        if c in r'"':
            return False
    return True


def main_except(argv):
    parser = OptionParser()

    # Observer location
    parser.add_option("-o", "--o-lat", action="store", type="float", dest="o_lat",
                      help="Observer latitude in degrees north [0.0 .. 90.0]", default=Constants.OBSERVER_LAT_DEG)
    # View control
    parser.add_option("--show-day", action="store_true", dest="showDay", default=False,
                      help="Show day-view instead of year-view")
    parser.add_option("--polar", action="store_true", dest="polar", default=False,
                      help="Show day-view in polar coordinates instead of cartesion coordinates")
    parser.add_option("-d", "--day", action="store", type="int", dest="day", default=0,
                      help="In day-view, which day in range 0..364 to render. default=0. "
                           "Use -d/--day or --date but not both.")
    parser.add_option("--date", action="store", dest="date", default="",
                      help="In day-view, which day of year to view. Use format 'YYYY.MM.DD'. "
                           "Use -d/--day or --date but not both.")
    # Output options
    parser.add_option("-f", "--filename", action="store", type="string", dest="filename",
                      help="When specified, write image to .png FILE", metavar="FILE", default=None)
    parser.add_option("--no-autoview", action="store_true", dest="noautoview", default=False,
                      help="Do not automatically spawn system image viewer for generated image")

    # version info
    parser.add_option("-v", "--version", action="store_true", dest="showversion", default=False,
                      help="Print program version number and exit")

    #
    (options, args) = parser.parse_args()

    if options.showversion:
        print("V%s" % TWILIGHT_VERSION)
        return

    # If filename given then limit it to plain characters in CWD
    if options.filename is not None:
        if not check_problematic_filename(options.filename):
            raise Exception("The --file option is limited to alphanumeric characters with no directory traversals")

    #
    if options.showDay:
        if options.polar:
            main_show_a_day_polar(options)
        else:
            main_show_a_day_cartesian(options)
    else:
        if options.polar:
            raise Exception("The --polar option is valid only in --show-day day view")
        main_show_a_year(options)


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