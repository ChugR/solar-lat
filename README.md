# solar-lat

This project holds work from some twilight studies. My original questions were: Why is early twilight happening at 3:00 a.m.? Which twilight am I seeing, is it nautical or astronomical twilight?

I need a model of earth that shows me why morning and evening twilights are what they are. It would be fun to see twilight values for any latitude.


# Files

## SolarLat.py

This file calculates the subsolar point given a time-of-day GMT.

It's pretty naive in terms of modeling the earth orbit and showing analemma details. There is no compensation for the equation of time.
Nor is there compensation for time zones, locations within a time zone, or for summer time offsets.

## twilight.py

This is the main program. There are two main view generators for an observer as some point on the prime meridian. Each view generator creates a .png file showing the results.

### Views

#### Day view

Day view shows a plot where the x-axis is the time of day and the y-axis is the elevation of the sun.

Vertical bands highlight when day, night, and twilights change.

A legend describes the plot colors.

#### Year view

Year view shows a plot where the x-axis is time of day and the y-axis is the day of the year. The elevation of the sun is implied by the colors of the graphs at each point.

### Example invocations

#### Run a year-view for observer at 42° north

> python twilight.py

#### Run a year-view for observer at the equator

> python twilight.py --o-lat 0.0

#### Run a day-view for observer at 42° north on January 5, 2024

> python twilight.py --show-day --date 2024.01.05

