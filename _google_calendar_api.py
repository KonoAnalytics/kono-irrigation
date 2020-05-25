from collections import namedtuple
import datetime as dt
import pickle
import os

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import TransportError
from httplib2 import ServerNotFoundError

import pandas as pd

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def _get_google_calendar_creds():
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    try:
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)
    except TransportError as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)
        print("Exiting. Can't complete task. Check the internet connection.")
        exit()
    return creds


def _format_calendar_events(events):
    Record = namedtuple("Record", ["id", "start_utc", "end_utc", "updated_utc", "summary", "description"])
    events_list = []
    for event in events:
        try:
            description = event["description"]
        except KeyError:
            description = None
        try:
            startdatetime = event["start"]["dateTime"]
            enddatetime = event["end"]["dateTime"]
            updated_utc = event["updated"]
        except KeyError:
            # if the event is "all day", it will be a date instead of dateTime. We ignore these events
            startdatetime = None
            enddatetime = None
        event_tuple = Record(event["id"], startdatetime, enddatetime, updated_utc, event["summary"], description)
        events_list.append(event_tuple)
    df = pd.DataFrame(events_list, columns=Record._fields)
    df = df.rename(columns={"id": "event_id"})
    df["duration_seconds"] = (pd.to_datetime(df["end_utc"]) - pd.to_datetime(df["start_utc"])).astype("timedelta64[s]")
    return df


def get_google_calendar_events(calendar_id, total_days):
    """
    Calls the Google Calendar API to pull calendar events
    :param calendar_id: Google calendar ID
    :param total_days: total days in the future to pull
    :return: returns a list of first 2500 events (Google API property) or up to "total days" worth of events, each event is a dictionary
    """
    credentials = _get_google_calendar_creds()
    try:
        service = build("calendar", "v3", credentials=credentials)
    except ServerNotFoundError as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)
        print("Can't connect to Google Calendar. Check the internet connection.")
        return
    now = dt.datetime.utcnow()
    last_day = (now + dt.timedelta(days=total_days)).isoformat() + "Z"
    now = now.isoformat() + "Z"  # 'Z' indicates UTC time
    try:
        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=now,
                timeMax=last_day,
                singleEvents=True,
                orderBy="startTime",
                timeZone="UTC",
            )
            .execute()
        )
    except ServerNotFoundError as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)
        print("Exiting. Can't get calendar events from the Google Calendar. Check the internet connection.")
        return
    events = events_result.get("items", [])
    events = _format_calendar_events(events)
    return events
