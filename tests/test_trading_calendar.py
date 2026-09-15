from trading_calendar import is_valid_session, next_valid_session
import pandas as pd

def test_valid_trading_session():
    # Sep 5, 2026 is a Saturday
    assert is_valid_session("2026-09-05") == False
    
    # Sep 7, 2026 is a Monday (assuming not a holiday)
    assert is_valid_session("2026-09-07") == True
    
def test_next_valid_session():
    assert next_valid_session("2026-09-05").strftime("%Y-%m-%d") == "2026-09-07"
from trading_calendar import get_previous_sessions
def test_get_previous_sessions():
    # Sep 16, 2026 is Wed. T-5 should be Sep 8 (Tue)
    t_5 = get_previous_sessions('2026-09-16', 5)
    assert t_5.strftime('%Y-%m-%d') == '2026-09-08'
