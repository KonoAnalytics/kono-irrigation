import os
import sqlite3
import pandas as pd

from _env_vars import DATABASE_NAME


def _get_con():
    """
    Get the sqlite connection to the database
    :return: sqlite connection
    """
    con = None
    try:
        con = sqlite3.connect(DATABASE_NAME)
    except sqlite3.Error as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)
        print("Exiting. Can't complete database task. Check the database.")
        exit()
    finally:
        return con


def replace_table(table_name, df):
    """
    Drops table and re-creates based on the parameters from df
    :param table_name: name of table to drop and re-create
    :param df: dataframe to upload
    :return: True if successful, False if not successful
    """
    try:
        _initialize_database()
        con = _get_con()
        cursor = con.cursor()
        drop_table_query = f"DROP TABLE IF EXISTS {table_name};"
        cursor.execute(drop_table_query)
        df.to_sql(table_name, con, if_exists="append", index=False)
        cursor.close()
        con.close()
        return True
    except sqlite3.Error as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)
        print("Exiting. Can't complete database task. Check the database.")
    return False


def _initialize_database(rebuild=False):
    """
    creates database and tables if they do not exist.
    :param rebuild: if True, deletes existing database first
    :return: True if successful, False if not successful
    """
    if rebuild:
        os.remove(DATABASE_NAME)
    try:
        con = _get_con()
        cursor = con.cursor()
        create_events_table_query = """
    CREATE TABLE IF NOT EXISTS events (
        event_id TEXT,
        start_utc TEXT,
        end_utc TEXT,
        updated_utc TEXT,
        duration_seconds INTEGER,
        summary TEXT,
        description TEXT
    );"""
        # states queued -> processing -> running -> finished
        # queued (waiting to for launch_sprinkler to run)
        # processing (pulled from runs table, marked so other processes won't try to run it)
        # running (zone actively engaged in watering)
        # finished (completed wartering)
        create_runs_table_query = """
    CREATE TABLE IF NOT EXISTS runs (
        event_id TEXT,
        start_utc TEXT,
        end_utc TEXT,
        updated_utc TEXT,
        duration_seconds INTEGER,
        summary TEXT,
        description TEXT,
        state TEXT
    );"""
        cursor.execute(create_events_table_query)
        cursor.execute(create_runs_table_query)
        cursor.close()
        con.close()
        return True
    except sqlite3.Error as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)
        print("Exiting. Can't complete database task. Check the database.")
    return False


def get_db_events():
    """
    Gets all events from the database
    :return: a dataframe of records if successful, None if not successful
    """
    try:
        _initialize_database()
        con = _get_con()
        df = pd.read_sql_query("SELECT * FROM events", con)
        con.close()
        return df
    except sqlite3.Error as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)
        print("Exiting. Can't complete database task. Check the database.")


def get_db_runs(states=None):
    """
    Gets top [num_records] oldest start_utc from the runs table
    :param states: a list of states. if None, returns records with all states
    :return: a dataframe of records if successful, None if not successful
    """
    try:
        _initialize_database()
        con = _get_con()
        if states is not None:
            where_clause = ",".join([f"'{state}'" for state in states])
            where_clause = f"WHERE state in ({where_clause})"
        else:
            where_clause = ""
        query = f"SELECT * FROM runs {where_clause} ORDER by start_utc ASC;"
        df = pd.read_sql_query(query, con)
        con.close()
        return df
    except sqlite3.Error as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)
        print("Exiting. Can't complete database task. Check the database.")


def set_run_state(event_id, updated_utc, state):
    """
    updates the state field of the runs table based on matching event_id and updated_utc field (which together is unique)
    :param event_id: event_id that originally comes from the google calendar
    :param updated_utc: update timestamp in utc that comes from the google calendar
    :param state: the state to which the record will be assigned
    :return: True if successful, False if not successful
    """
    try:
        _initialize_database()
        con = _get_con()
        cursor = con.cursor()
        sql_update_query = f"""UPDATE runs SET state = '{state}'
        WHERE event_id = '{event_id}' AND updated_utc = '{updated_utc}';"""
        cursor.execute(sql_update_query)
        con.commit()
        cursor.close()
        con.close()
        return True
    except sqlite3.Error as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)
        print("Exiting. Can't complete database task. Check the database.")
    return False


# def update_run_state(event_id, updated_utc, old_states, new_state):
#     try:
#         _initialize_database()
#         con = _get_con()
#         cursor = con.cursor()
#         old_state_string = ",".join([f"'{old_state}'" for old_state in old_states])
#         sql_update_query = f"""UPDATE runs SET state = '{new_state}'
#         WHERE event_id = '{event_id}'
#             AND start_utc = '{updated_utc}'
#             AND state in ({old_state_string});"""
#         cursor.execute(sql_update_query)
#         con.commit()
#         cursor.close()
#         con.close()
#         return True
#     except sqlite3.Error as ex:
#         template = "An exception of type {0} occurred. Arguments:\n{1!r}"
#         message = template.format(type(ex).__name__, ex.args)
#         print(message)
#         print("Exiting. Can't complete database task. Check the database.")
#     return False


def insert_runs(df):
    upload_cols = [
        "event_id",
        "start_utc",
        "end_utc",
        "updated_utc",
        "duration_seconds",
        "summary",
        "description",
        "state",
    ]
    try:
        _initialize_database()
        con = _get_con()
        df[upload_cols].to_sql("runs", con, if_exists="append", index=False)
        con.close()
        return True
    except sqlite3.Error as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)
        print("Exiting. Can't complete database task. Check the database.")
    return False
