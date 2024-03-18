# solar-lat

This project holds work from some recreational twilight studies. My original questions were:

 * Why is early twilight happening at 3:00 a.m.?
 * Which twilight am I seeing: is it civil, nautical, or astronomical twilight?

This project instantiates a model of the earth and sun that answers my questions and shows why morning and evening twilights are what they are. 

# Installation

Clone the solar-lat project to a directory of your choice.

Several python modules are required to run it:
```
python -m pip install numpy pandas Pillow
```

# Files

## twilight.py

This is the main program. It has view generators for an observer at some point on the prime meridian. See *twilight.py Views* in a following section. Each view generator creates a picture to be viewed on-screen and/or saved as a .png file.

### twilight.py command line switches

| Switch        | Description                                         |
| ------------- | --------------------------------------------------- |
| --help        | Show help and exit                                  |
| -o O_LAT      | Observer latitude in floating point degrees north   |
| --show-day    | Select day-view instead of default year-view        |
| --polar       | Show polar day-view                                 |
| -d DAY        | In day-view, show this day [0..364]                 |
| --day=DAY     | In day-view, show this day [0..364]                 |
| --date=DATE   | In day-view, show this date. Use format 'YYYY.MM.DD'|
| -f FILE       | Save .png image to FILE in current directory        |
| --no-autoview | Do not autoview the image                           |
| -v --version  | Show program version and exit                       |

#### Notes

* In addition to year-view and day-view a polar-day-view is under development.
* When specifying a day to view in day-view, options -d/--day and --date are mutually exclusive. Specify one or the other but not both.
* This code does not attempt to show leap years. Internally a leap year is computed with all the precision as a regular year but only 365 days of it are displayed. Being one day off in these diagrams is not significant.
* This code does not attempt to show daylight savings time. If I was lazy I could always go to https://www.timeanddate.com/sun/usa/boston and see what they say about DST. But what fun is that?
* This code doesn't correct for the sun being a non-zero width disc nor does it correct for atmospheric refraction. The sun is taken as a point source and twilight.py pretends there is no atmosphere on earth.
* Regardless of the year specified by *--date YYYY.MM.DD* this code shows plots for the year 2019.

> A little inaccuracy sometimes saves tons of explanation. -Tyron Saki

## SG_sunpos_ultimate_azi_atan2.ph

An advanced solar geometry calculator. This function finds the subsolar point for any time and date using 2019 ephemeris data.

[A solar azimuth formula that renders circumstantial treatment unnecessary without compromising mathematical rigor: Mathematical setup, application and extension of a formula based on the subsolar point and atan2 function - ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0960148121004031)

Algorithms/implementations: Taiping Zhang, Paul W. Stackhouse Jr., Bradley Macpherson, J. Colleen Mikovitz
 
# twilight.py Views

## Year view

Year view shows a plot where the x-axis is time of day and the y-axis is the day of the year. The elevation of the sun is implied by the colors of the graph at each point.

### Example year view

![Example year-view plot](images/twilight_year_lat-43.png "Twilight year-view from 42.6 degrees north")

## Day view

Day view shows a plot where the x-axis is the time of day and the y-axis is the elevation of the sun.

Vertical bands highlight when day, night, and twilights change.

A legend describes the plot colors.

### Example day view

![Example day-view plot](images/twilight_day_69_lat-43.png "Twilight day-view from 42.6 degrees north")

## Polar day view

The --polar view is different from year and cartesian day view.
The polar view takes into account that mean time hour angles and solar
position azimuth angles may be wildly different. The polar view is
essentially an azimuth/elevation plot of the sun's position for the day.
Then points on the plot are marked with their corresponding GMT times.
    
 * The azimuth angle is plotted from the center of the circle with north
   being straight down. This gives a view with noon at the top of the plot
   and makes more sense for observers in the northern hemisphere.
 
 * The solar elevation is plotted with the nadir at the center of the
   circle, the horizon as the boundary between the twilight color and the
   whitish daylight color, and the zenith at the outer edge of the circle.

Note that some plots might not make sense.

 * Observers in the middle latitudes see plots that are understandable. During the day the sun is above the horizon
   and during the night the sun is below the horizon returning to where it will rise the next day.
 * Observers in the tropics may see the sun pass directly overhead or directly underneath the nadir.
   In those events the displayed azimuth values swing rapidly and the position plot might not appear as a solid connected line.
 * Observers near the poles will see the position plots making near-circles while the sun does not change much in
   elevation angle.
 
This view satisfies some of my research goals.

### Example polar day view

![Example day-view --polar plot](images/twilight_day_171_lat-42.6_polar.png "Twilight --polar day-view from 42.6 degrees north")

# twilight.py example invocations

## Run a year-view for observer at 42.6° north

> python twilight.py

## Run a year-view for observer at the equator

> python twilight.py --o 0.0

## Run a day-view for observer at 42.6° north on January 5, 2019

> python twilight.py --show-day --date 2024.01.05

