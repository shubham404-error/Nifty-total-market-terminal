import pandas as pd
from scoring import compute_funnel_booleans
from decision_config import V4_CONFIG
import pytest
import sqlite3

@pytest.fixture(autouse=True)
def clean_db():
    import os
    os.makedirs("data", exist_ok=True)
    with sqlite3.connect("data/signal_ledger.sqlite") as conn:
        conn.execute("DROP TABLE IF EXISTS regime_history")
    yield

def test_funnel_boolean_sums():
    df = pd.DataFrame({
        "Symbol": ["A", "B", "C"],
        "HistoryEligible": [True, True, False],
        "AvgTradedValue20": [2_00_00_000, 500_000, 2_00_00_000],
        "Stage": [2, 2, 2],
        "Raw_RS_Rating": [80, 80, 80],
        "RS_Rating": [80, 80, 80],
        "ConvergenceScore": [70, 70, 70],
        "EntryPattern": ["Hammer", "Hammer", "Hammer"],
        "EntrySetupQualified": [True, True, True],
        "Close": [100, 100, 100],
        "SMA200": [90, 90, 90]
    })
    
    res = compute_funnel_booleans(df, as_of_session="2026-09-16")
    assert res["passed_data_quality"].sum() == 2
    assert res["passed_liquidity"].sum() == 2
    assert res["passed_all"].sum() == 1 # Only A passes all