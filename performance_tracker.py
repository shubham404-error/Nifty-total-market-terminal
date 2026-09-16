import sqlite3
import os
import json
import pandas as pd
from trading_calendar import next_valid_session, get_previous_sessions, is_valid_session, sessions_between
from engine import download_prices

DB_PATH = "data/signal_ledger.sqlite"

def init_performance_db():
    os.makedirs("data", exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS signal_performance (
                SignalID TEXT PRIMARY KEY,
                EntryPrice REAL,
                CurrentPrice REAL,
                ReturnFromEntry REAL,
                RunningMFE REAL,
                RunningMAE REAL,
                DaysHeld INTEGER,
                NiftyReturn REAL
            )
        """)

def update_signal_performance(as_of_session: str, universe: pd.DataFrame):
    init_performance_db()
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        active_signals = pd.read_sql("SELECT * FROM signal_ledger WHERE Status IN ('ACTIVE', 'PENDING_ENTRY')", conn)
        
        if active_signals.empty:
            return
            
    # Need recent prices
    # Since we need to calculate MFE/MAE from entry date to as_of_session, we need price history
    # Let's download a small chunk of prices for active symbols
    symbols = active_signals["Symbol"].unique()
    # Map Symbol to Yahoo Symbol
    yahoo_symbols = universe[universe["Symbol"].isin(symbols)]["Yahoo Symbol"].tolist()
    if "^NSEI" not in yahoo_symbols:
        yahoo_symbols.append("^NSEI")
        
    prices, _ = download_prices(
        universe=universe[universe["Yahoo Symbol"].isin(yahoo_symbols)],
        years=1, # Just need recent 65 days basically
        as_of_session=as_of_session
    )
    
    if prices.empty:
        return
        
    nifty_prices = prices[prices["Yahoo Symbol"] == "^NSEI"].set_index("Date")
        
    updates_ledger = {}
    updates_perf = []
    
    for _, sig in active_signals.iterrows():
        sig_id = sig["SignalID"]
        symbol = sig["Symbol"]
        status = sig["Status"]
        entry_date = sig["EntryDate"]
        
        ysym = universe.loc[universe["Symbol"] == symbol, "Yahoo Symbol"]
        if ysym.empty:
            continue
        yahoo_sym = ysym.values[0]
        
        # Filter prices for this symbol
        sym_prices = prices[prices["Yahoo Symbol"] == yahoo_sym]
        if sym_prices.empty:
            continue
            
        sym_prices = sym_prices.sort_values("Date").set_index("Date")
        
        # Resolve PENDING_ENTRY
        entry_price = sig["EntryPrice"]
        if status == "PENDING_ENTRY":
            if entry_date in sym_prices.index:
                # Fill entry price using Open
                entry_price = sym_prices.loc[entry_date, "Open"]
                status = "ACTIVE"
                updates_ledger[sig_id] = {"EntryPrice": entry_price, "Status": status}
            else:
                continue
                
        if status != "ACTIVE" or pd.isna(entry_price):
            continue
            
        post_entry = sym_prices.loc[entry_date:as_of_session]
        if post_entry.empty:
            continue
            
        current_price = post_entry.iloc[-1]["Close"]
        highest_high = post_entry["High"].max()
        lowest_low = post_entry["Low"].min()
        
        ret = (current_price - entry_price) / entry_price if entry_price else 0
        mfe = (highest_high - entry_price) / entry_price if entry_price else 0
        mae = (lowest_low - entry_price) / entry_price if entry_price else 0
        
        days_held = max(0, len(sessions_between(entry_date, as_of_session)) - 1)
        
        nifty_ret = None
        if entry_date in nifty_prices.index and as_of_session in nifty_prices.index:
            nifty_entry = nifty_prices.loc[entry_date, "Close"]
            nifty_curr = nifty_prices.loc[as_of_session, "Close"]
            nifty_ret = (nifty_curr - nifty_entry) / nifty_entry if nifty_entry else 0
            
        updates_perf.append((sig_id, entry_price, current_price, ret, mfe, mae, days_held, nifty_ret))
        
        decay_state = sig.get("DecayState", "INTACT")
        if decay_state == "THESIS_BROKEN" or days_held >= 65:
            close_reason = "THESIS_BROKEN" if decay_state == "THESIS_BROKEN" else "TIME_STOP_65"
            if sig_id not in updates_ledger:
                updates_ledger[sig_id] = {}
            updates_ledger[sig_id].update({"Status": "CLOSED", "CloseReason": close_reason})
            
    # Write back
    if updates_ledger or updates_perf:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("BEGIN TRANSACTION")
            try:
                for sig_id, fields in updates_ledger.items():
                    set_clause = ", ".join([f"{k} = ?" for k in fields.keys()])
                    values = list(fields.values()) + [sig_id]
                    conn.execute(f"UPDATE signal_ledger SET {set_clause} WHERE SignalID = ?", values)
                
                for upd in updates_perf:
                    conn.execute("""
                        INSERT INTO signal_performance (SignalID, EntryPrice, CurrentPrice, ReturnFromEntry, RunningMFE, RunningMAE, DaysHeld, NiftyReturn)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(SignalID) DO UPDATE SET
                            EntryPrice=excluded.EntryPrice,
                            CurrentPrice=excluded.CurrentPrice,
                            ReturnFromEntry=excluded.ReturnFromEntry,
                            RunningMFE=excluded.RunningMFE,
                            RunningMAE=excluded.RunningMAE,
                            DaysHeld=excluded.DaysHeld,
                            NiftyReturn=excluded.NiftyReturn
                    """, upd)
                
                conn.execute("COMMIT")
            except Exception as e:
                conn.execute("ROLLBACK")
                raise e