import pytest
import pandas as pd
from market_regime import update_market_regime
import sqlite3
from trading_calendar import is_valid_session
import datetime

@pytest.fixture(autouse=True)
def clean_db():
    import os
    os.makedirs("data", exist_ok=True)
    with sqlite3.connect("data/signal_ledger.sqlite") as conn:
        conn.execute("DROP TABLE IF EXISTS regime_history")
    yield
    with sqlite3.connect("data/signal_ledger.sqlite") as conn:
        conn.execute("DROP TABLE IF EXISTS regime_history")

def test_regime_state_transitions():
    df = pd.DataFrame({"HistoryEligible": [True]*10, "Close": [110]*10, "SMA200": [100]*10, "Stage": [2]*10})
    
    res = update_market_regime("2026-09-01", df, 2)
    assert res["Regime"] == "BULLISH"
    
    df_stage4 = df.copy()
    df_stage4["Stage"] = 4
    res2 = update_market_regime("2026-09-02", df_stage4, 4)
    assert res2["Regime"] == "DEFENSIVE"
    
    df_crisis = df_stage4.copy()
    df_crisis["Close"] = 90
    
    d = datetime.date(2026, 9, 3)
    for i in range(40):
        update_market_regime(d.strftime("%Y-%m-%d"), df_crisis, 4)
        d += datetime.timedelta(days=1)
    res_crisis = update_market_regime(d.strftime("%Y-%m-%d"), df_crisis, 4)
    assert res_crisis["Regime"] == "CRISIS"
    
def test_crisis_exit_persistence():
    df = pd.DataFrame({"HistoryEligible": [True]*10, "Close": [90]*10, "SMA200": [100]*10, "Stage": [4]*10})
    d = datetime.date(2026, 9, 1)
    for i in range(40):
        update_market_regime(d.strftime("%Y-%m-%d"), df, 4)
        d += datetime.timedelta(days=1)
        
    df_good = pd.DataFrame({"HistoryEligible": [True]*10, "Close": [110]*10, "SMA200": [100]*10, "Stage": [2]*10})
    
    d += datetime.timedelta(days=1)
    while not is_valid_session(d.strftime("%Y-%m-%d")): d += datetime.timedelta(days=1)
    r1 = update_market_regime(d.strftime("%Y-%m-%d"), df_good, 2)
    assert r1["Regime"] == "CRISIS"
    
    d += datetime.timedelta(days=1)
    while not is_valid_session(d.strftime("%Y-%m-%d")): d += datetime.timedelta(days=1)
    r2 = update_market_regime(d.strftime("%Y-%m-%d"), df_good, 2)
    assert r2["Regime"] != "CRISIS"