from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import pandas_market_calendars as mcal
NY = ZoneInfo("America/New_York")
def sessions(start,end):
    return mcal.get_calendar("NYSE").schedule(start_date=start,end_date=end)
def due(now: datetime) -> str | None:
    if now.tzinfo is None: raise ValueError("timezone required")
    local=now.astimezone(NY)
    # Catch delayed invocations until next morning 09:00 ET.
    day=local.date() if local.time()>=time(17,30) else local.date()-timedelta(days=1)
    if local.time()>=time(9) and local.time()<time(17,30): return None
    s=sessions(day,day)
    return str(day) if not s.empty and now>=s.iloc[0].market_close.to_pydatetime() else None
def next_session(day):
    d=datetime.fromisoformat(day).date()+timedelta(days=1)
    return str(sessions(d,d+timedelta(days=10)).index[0].date())
