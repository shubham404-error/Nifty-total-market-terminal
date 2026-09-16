import sqlite3
from decision_config import V4_CONFIG
DB_PATH = "data/signal_ledger.sqlite"

with sqlite3.connect(DB_PATH) as conn:
    try:
        conn.execute("ALTER TABLE signal_ledger ADD COLUMN CloseReason TEXT")
        print("Added CloseReason")
    except sqlite3.OperationalError:
        print("CloseReason already exists")