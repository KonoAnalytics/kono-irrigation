from _sql_calls import get_db_events, get_db_runs, replace_table, insert_runs
from _google_calendar_api import get_google_calendar_events
import datetime as dt
import pandas as pd

from _env_vars import CALENDAR_ID, TOTAL_DAYS, CALENDAR_POLLING_PERIOD_SECONDS


def _process_events(df):
    """
    Insert records into the runs table (which is a queue)
    :param df: records to check for insertion
    :return: None
    """
    # we want to process anything that starts fewer than 60 seconds in the future
    # and ends less than CALENDAR_POLLING_PERIOD_SECONDS seconds ago
    beginning_time_span = (
        dt.datetime.utcnow() + dt.timedelta(seconds=-CALENDAR_POLLING_PERIOD_SECONDS)
    ).isoformat() + "Z"
    ending_time_span = (dt.datetime.utcnow() + dt.timedelta(seconds=60)).isoformat() + "Z"
    records_to_process = (df["start_utc"] < ending_time_span) & (df["end_utc"] > beginning_time_span)
    df = df[records_to_process]
    df = df.merge(get_db_runs(), on=["event_id", "updated_utc"], suffixes=("", "_runs"), how="left")
    df = df[pd.isnull(df["state"])]
    df["state"] = "queued"
    if df.empty:
        print("No records to insert into queue")
    else:
        plural = (len(df) > 1) * "s"
        print(f"inserting {len(df)} record{plural} into run queue")
        insert_runs(df)


def main():
    # get latest google calendar
    df_events = get_google_calendar_events(CALENDAR_ID, TOTAL_DAYS)
    if df_events is None:
        # if we can't reach google calendar, pull from our existing database
        df_events = get_db_events()
    else:
        # flush/fill database with google calendar
        replace_table("events", df_events)

    # parse events to determine which should be queued
    _process_events(df_events)


if __name__ == "__main__":
    main()
