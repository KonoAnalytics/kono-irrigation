.. image:: https://konoanalytics.com/static/website/images/Kono-Logo-White-Color-Transparent-Back.svg
    :target: https://www.konoanalytics.com/

============================================
Raspberry Pi Irrigation System
============================================

This software, combined with a Raspberry Pi connected to relay switches and a Google calendar can control a multi-zone irrigation system.  The user controls the schedule for each zone through events on a Google Calendar.

* poll_calendary.py should be run periodically to copy events into a local sqlite database. A cron job launching this every 60 seconds should work well. Doing it less frequently will be ok, but any new calendar events won't be synced.  This grabs one month of future events each time. If the internet is irratic then it will be able to function for a full month based on the last calendar sync before it exhausts all synchronized events.
* launch_sprinkler.py will physically launch the irrigation zones if they are schduled now or within the next minute. It should be run frequently. A cron job launching this every 30 seconds should work well.
* this makes use of environment variables via the _env_vars.py file.  There are a few that must be set up and others that will use default values if they are not defined.
* this sqlite database file is created automatically, and can be deleted at any time.  If you so so, you will lose the irrigation history in the runs table, but go-forward functionality is not affected
* this hyperlink is helpful for setting up the Google token: https://developers.google.com/calendar/quickstart/python

-----
TO DO
-----

* write code to activate and deactivate relays
* use an environment variable to set the maximum duration for a single event to combat waste through user error or malfunction
* integrate with a weather API for smarter irrigation (such as precipitation, temperature, cloud cover, season, etc.)
* parse parameters in the calendar description field (like override_weather=True)

===============
Version History
===============
======= ========== ================ =============
Version Date       Editor           Release Notes
======= ========== ================ =============
0.0.1   2020-05-25 Jonathan Bennett initial version.
======= ========== ================ =============
