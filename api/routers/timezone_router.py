from datetime import datetime
import time

@app.get("/debug/time")
def debug_time():
    return {
        "datetime_now": str(datetime.now()),
        "datetime_utc": str(datetime.utcnow()),
        "timezone": time.tzname,
        "offset": time.timezone,
    }