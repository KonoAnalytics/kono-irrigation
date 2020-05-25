import threading
import time

from _sql_calls import get_db_runs, set_run_state
from _env_vars import MAX_CONCURRENT_ZONES, ZONE_SUMMARY_MAP
from _relay_control import activate_relay, deactivate_relay

threadLimiter = threading.BoundedSemaphore(MAX_CONCURRENT_ZONES)


class MyThread(threading.Thread):
    def __init__(self, threadId, zone, duration, event_id, updated_utc):
        threading.Thread.__init__(self)
        self.threadId = threadId
        self.zone = zone
        self.duration = duration
        self.event_id = event_id
        self.updated_utc = updated_utc

    def run(self):
        threadLimiter.acquire()
        try:
            print(f"Starting zone {self.zone}")
            launch_zone(self.zone, self.duration, self.event_id, self.updated_utc)
            print(f"Finished with zone {self.zone}")
        finally:
            threadLimiter.release()


def get_zone_from_summary(summary):
    return ZONE_SUMMARY_MAP["summary"]


def launch_zone(zone, duration, event_id, updated_utc):
    print(f"running {zone} for {duration} seconds")
    set_run_state(event_id, updated_utc, "running")
    activate_relay(zone)
    time.sleep(duration)
    deactivate_relay(zone)
    # turn off relay for the right zone
    set_run_state(event_id, updated_utc, "finished")


def main():
    df = get_db_runs(["queued"])

    # do this quickly so no other process tries to process
    for index, row in df.iterrows():
        set_run_state(row["event_id"], row["updated_utc"], "processing")

    # cycle through these one at a time or multiple at a time depending on value of MAX_CONCURRENT_ZONES
    threads = []
    for index, row in df.iterrows():
        zone = ZONE_SUMMARY_MAP[row["summary"]]
        threads.append(MyThread(index, zone, row["duration_seconds"], row["event_id"], row["updated_utc"]))

    for index, row in df.iterrows():
        threads[index].start()

    for index, row in df.iterrows():
        threads[index].join()


if __name__ == "__main__":
    main()
