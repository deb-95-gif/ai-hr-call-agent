from datetime import datetime, time
import pytz

IST = pytz.timezone("Asia/Kolkata")

def is_working_hours():
    now = datetime.now(IST)
    return now.weekday() < 6 and time(10,0) <= now.time() < time(18,0)
