import sqlite3
import pandas as pd
with sqlite3.connect("data/signal_ledger.sqlite") as conn:
    df = pd.read_sql("SELECT * FROM regime_history ORDER BY date DESC LIMIT 5", conn)
print(df.to_string())