from datetime import datetime, time
import pytz

IST = pytz.timezone("Asia/Kolkata")

def is_working_hours():
    now = datetime.now(IST)
    start = time(10, 0)
    end = time(18, 0)
    return now.weekday() < 6 and start <= now.time() < end
