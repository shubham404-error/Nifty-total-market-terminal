import sqlite3
import pandas as pd
import json
import os
import hashlib
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from signal_ledger import init_ledger_db

def migrate():
    csv_path = "performance terminal/performance_database.csv"
    db_path = "data/signal_ledger.sqlite"
    
    if not os.path.exists(csv_path):
        print(f"CSV not found: {csv_path}")
        return
        
    init_ledger_db()
        
    df = pd.read_csv(csv_path)
    
    with sqlite3.connect(db_path) as conn:
        for idx, row in df.iterrows():
            symbol = row["Symbol"]
            signal_date = row["CohortDate"]
            
            sig_hash = hashlib.md5(f"{symbol}_{signal_date}_{idx}".encode()).hexdigest()[:6]
            signal_id = f"{symbol}_{signal_date}_LEGACY_{sig_hash}"
            
            entry_price = float(row["EntryPrice"]) if pd.notna(row["EntryPrice"]) else None
            signal_close = entry_price 
            entry_date = signal_date
            status = "CLOSED" if row.get("Status") == "Closed" else "ACTIVE"
            decay_state = "INTACT"
            
            original_thesis = {
                "Stage": 2, 
                "RS_Rating": 80, 
                "Confluence": float(row["Score"]) if pd.notna(row["Score"]) else None,
                "Setup": row["Setup"],
                "IsLegacy": True
            }
            
            data_status = "LEGACY"
            
            try:
                conn.execute("""
                    INSERT INTO signal_ledger (SignalID, Symbol, SignalDate, EntryDate, EntryPrice, SignalClose, Status, DecayState, OriginalThesis, DataStatus)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    signal_id, symbol, signal_date, entry_date, entry_price, signal_close, 
                    status, decay_state, json.dumps(original_thesis), data_status
                ))
            except sqlite3.IntegrityError:
                pass
                
        conn.commit()
        print(f"Migrated {len(df)} legacy signals.")

if __name__ == "__main__":
    migrate()