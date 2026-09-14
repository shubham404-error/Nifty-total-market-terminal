import sqlite3
import json
import os
import pandas as pd
from datetime import datetime
from decision_config import V4_CONFIG

DB_PATH = "data/signal_ledger.sqlite"

def init_ledger_db():
    os.makedirs("data", exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS signal_ledger (
                SignalID TEXT PRIMARY KEY,
                Symbol TEXT,
                SignalDate TEXT,
                EntryDate TEXT,
                EntryPrice REAL,
                SignalClose REAL,
                Status TEXT,
                DecayState TEXT,
                DecayReasons TEXT,
                DecayFactorGroups TEXT,
                OriginalThesis TEXT,
                CurrentState TEXT,
                DataStatus TEXT
            )
        """)

def generate_signal_id(symbol: str, signal_date: str) -> str:
    # SignalID = Symbol_SignalDate_Strategy_ConfigVersion
    return f"{symbol}_{signal_date}_V4_{V4_CONFIG['CONFIG_VERSION']}"

def add_signal(symbol: str, signal_date: str, entry_date: str, entry_price: float, signal_close: float, original_thesis: dict, data_status: str = "FRESH"):
    init_ledger_db()
    signal_id = generate_signal_id(symbol, signal_date)
    
    with sqlite3.connect(DB_PATH) as conn:
        # Immutability guard: Check if exists
        existing = conn.execute("SELECT EntryPrice FROM signal_ledger WHERE SignalID = ?", (signal_id,)).fetchone()
        if existing:
            # Already exists, do not overwrite EntryPrice or OriginalThesis
            return
            
        conn.execute("""
            INSERT INTO signal_ledger (SignalID, Symbol, SignalDate, EntryDate, EntryPrice, SignalClose, Status, DecayState, OriginalThesis, DataStatus)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal_id, symbol, signal_date, entry_date, entry_price, signal_close, 
            "PENDING_ENTRY", "INTACT", json.dumps(original_thesis), data_status
        ))

def update_signal_state(signal_id: str, status: str, decay_state: str, decay_reasons: list, decay_groups: list, current_state: dict, data_status: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            UPDATE signal_ledger
            SET Status = ?, DecayState = ?, DecayReasons = ?, DecayFactorGroups = ?, CurrentState = ?, DataStatus = ?
            WHERE SignalID = ?
        """, (
            status, decay_state, json.dumps(decay_reasons), json.dumps(decay_groups), json.dumps(current_state), data_status, signal_id
        ))