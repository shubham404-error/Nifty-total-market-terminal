import pandas as pd
import exchange_calendars as xcals

_cal = xcals.get_calendar("XNSE")

def is_valid_session(date) -> bool:
    return _cal.is_session(pd.Timestamp(date))

def next_valid_session(date) -> pd.Timestamp:
    return _cal.next_open(pd.Timestamp(date)).normalize()

def sessions_between(start, end) -> list:
    return _cal.sessions_in_range(pd.Timestamp(start), pd.Timestamp(end)).tolist()