# solar-lat

This project holds work from some recreational twilight studies. My original questions were:

 * Why is early twilight happening at 3:00 a.m.?
 * Which twilight am I seeing, is it nautical or astronomical twilight?

I need a model of the earth and sun that shows why morning and evening twilights are what they are. It would be fun to see twilight values for any latitude.

# Files

## twilight.py

This is the main program. It has two main view generators for an observer at some point on the prime meridian. See *Twilight Views* in the next section. Each view generator creates a .png file showing the results.

## SG_sunpos_ultimate_azi_atan2.ph

An advanced solar geometry calculator.

[A solar azimuth formula that renders circumstantial treatment unnecessary without compromising mathematical rigor: Mathematical setup, application and extension of a formula based on the subsolar point and atan2 function - ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0960148121004031)

Algorithms/implementations: Taiping Zhang, Paul W. Stackhouse Jr., Bradley Macpherson, J. Colleen Mikovitz
 
## SolarLat.py

This file is being deprecated. It calculates the subsolar point given a time-of-day GMT modeling a naive, circular earth orbit around the sun. 

# Twilight Views

## Day view

Day view shows a plot where the x-axis is the time of day and the y-axis is the elevation of the sun.

Vertical bands highlight when day, night, and twilights change.

A legend describes the plot colors.

## Year view

Year view shows a plot where the x-axis is time of day and the y-axis is the day of the year. The elevation of the sun is implied by the colors of the graph at each point.

![Example year-view plot](images/twilight_year_lat-43.png "Twilight year-view from 42.6 degrees north")

### Example invocations

#### Run a year-view for observer at 42° north

> python twilight.py

#### Run a year-view for observer at the equator

> python twilight.py --o-lat 0.0

#### Run a day-view for observer at 42° north on January 5, 2024

> python twilight.py --show-day --date 2024.01.05

