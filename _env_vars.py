import os
import json

try:
    CALENDAR_ID = os.getenv("calendar_id", "primary")
    TOTAL_DAYS = int(os.getenv("total_days", 30))
    DATABASE_NAME = os.getenv("db_name", "sprinkler.db")
    CALENDAR_POLLING_PERIOD_SECONDS = int(os.getenv("calendar_polling_period_seconds", 60))
    LAUNCH_SPRINKLER_PERIOD_SECONDS = int(os.getenv("launch_sprinkler_period_seconds", 20))
    MAX_CONCURRENT_ZONES = int(os.getenv("max_concurrent_zones", 1))
    ZONE_SUMMARY_MAP = json.loads(
        os.getenv("zone_summary_map", """{"Zone 1": 1, "Zone 2":2, "Zone 3": 3, "Zone 4": 4}""")
    )

except KeyError:
    print("Error. Did you forget to set your environment variables?")
