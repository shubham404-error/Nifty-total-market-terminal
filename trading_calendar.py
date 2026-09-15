import pandas as pd
import exchange_calendars as xcals

_cal = xcals.get_calendar("XBOM")

def is_valid_session(date) -> bool:
    return _cal.is_session(pd.Timestamp(date))

def next_valid_session(date) -> pd.Timestamp:
    return _cal.next_open(pd.Timestamp(date)).normalize()

def sessions_between(start, end) -> list:
    return _cal.sessions_in_range(pd.Timestamp(start), pd.Timestamp(end)).tolist()

def get_previous_sessions(date, n_sessions: int) -> pd.Timestamp:
    """
    Returns the valid trading session date that is exactly `n_sessions` before `date`.
    If n_sessions=1, it returns the previous valid trading day.
    """
    ts = pd.Timestamp(date)
    # sessions_window with -(n+1) will return a list ending on `ts`.
    # The 0th element is exactly T-n.
    return _cal.sessions_window(ts, -(n_sessions + 1))[0]