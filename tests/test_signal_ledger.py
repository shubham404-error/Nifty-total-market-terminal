import pytest
import sqlite3
import json
from signal_ledger import add_signal, update_signal_state, generate_signal_id

@pytest.fixture(autouse=True)
def clean_db():
    import os
    os.makedirs("data", exist_ok=True)
    with sqlite3.connect("data/signal_ledger.sqlite") as conn:
        conn.execute("DROP TABLE IF EXISTS signal_ledger")
    yield
    with sqlite3.connect("data/signal_ledger.sqlite") as conn:
        conn.execute("DROP TABLE IF EXISTS signal_ledger")

def test_signal_immutability():
    add_signal("TCS", "2026-09-01", "2026-09-02", 3000.0, 2900.0, {"Stage": 2})
    
    # Try to overwrite entry price
    add_signal("TCS", "2026-09-01", "2026-09-02", 3500.0, 2900.0, {"Stage": 1})
    
    with sqlite3.connect("data/signal_ledger.sqlite") as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM signal_ledger").fetchone()
        
    assert row["EntryPrice"] == 3000.0
    assert json.loads(row["OriginalThesis"])["Stage"] == 2
    
def test_deterministic_signal_id():
    sid = generate_signal_id("RELIANCE", "2026-09-01")
    assert sid.startswith("RELIANCE_2026-09-01_V4")