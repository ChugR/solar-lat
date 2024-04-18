# Produce movies of twilight views
# - year view for each latitude
# - day view (cartesian) for each day at some latitudes
# - day view (polar)     for each day at some latitudes

# developed with ffmpeg version 6.0.1

import subprocess

do_1 = True  # generate year-view png files
do_2 = True  # render year-view mp4
do_3 = False  # generate cartesian day-views files
do_4 = False  # render cartesian day-views mp4
do_5 = False  # generate polar day-views files
do_6 = False  # render polar day-views mp4

day_views_lats = [0.0, 42.5]


if do_1:
    print("Generating year-view png files")
    
    # Generate year-view .png files for latitudes -90..90
    # Files are named <prefix>_110..<prefix>_290, centered on 200

    base_n = 200

    for i in range(-90, 91):
        file_n = base_n + i
        filename = "twilight_year_%03d.png" % (base_n + i)
        print("Generating file for latitude ", i, "as file ", filename)
    
        cmd = ["python", "../twilight.py", "-o", "%d" % i, "-f", filename, "--no-autoview"]

        subprocess.run(cmd)

if do_2:
    print("Rendering year-view mp4")

    # Render the mp4 from the year view pngs

    cmd = ["ffmpeg", "-framerate", "2", "-pattern_type", "glob",  "-i",  "./twilight_year_*.png",
           "-profile:v", "main", "-pix_fmt", "yuv420p", "twilight-year.mp4"]

    subprocess.run(cmd)

if do_3:
    for observer_lat in day_views_lats:
        print("generate cartesian day-view files for at latitude %f"  % observer_lat)

        for day in range(365):
            filename = "twilight_day_%03d_lat_%04.1f.png" % (day, observer_lat)
            print("Generating file for day ", day, "as file ", filename)
            cmd = ["python", "../twilight.py", "-o", "%f" % observer_lat,
                   "--show-day", "-d", "%d" % day, "-f", filename, "--no-autoview"]

            subprocess.run(cmd)

if do_4:
    for observer_lat in day_views_lats:
        print("Rendering cartesian day-view for latitude %f mp4" % observer_lat)

        # Render the mp4 from the day view pngs
        filenames = "twilight_day_*_lat_%04.1f.png" % (observer_lat)

        cmd = ["ffmpeg", "-framerate", "4", "-pattern_type", "glob",  "-i",  filenames,
               "-profile:v", "main", "-pix_fmt", "yuv420p",
               "twilight-day-cartesian-lat-%04.1f.mp4" % observer_lat]

        subprocess.run(cmd)

if do_5:
    for observer_lat in day_views_lats:
        print("generate polar day-view files for at latitude %f"  % observer_lat)

        for day in range(365):
            filename = "twilight_day_polar_%03d_lat_%04.1f.png" % (day, observer_lat)
            print("Generating file for day ", day, "as file ", filename)
            cmd = ["python", "../twilight.py", "-o", "%f" % observer_lat, "--show-day",
                   "--polar", "-d", "%d" % day, "-f", filename, "--no-autoview"]

            subprocess.run(cmd)

if do_6:
    for observer_lat in day_views_lats:
        print("Rendering polar day-view for latitude %f  mp4" % observer_lat)

        # Render the mp4 from the day view pngs
        filenames = "twilight_day_polar_*_lat_%04.1f.png" % (observer_lat)
        cmd = ["ffmpeg", "-framerate", "4", "-pattern_type", "glob",  "-i",  filenames,
               "-profile:v", "main", "-pix_fmt", "yuv420p",
               "twilight-day-polar-lat-%04.1f.mp4" % observer_lat]

        subprocess.run(cmd)
