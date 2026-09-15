import streamlit as st
import sqlite3
import pandas as pd
import json

def positions_at_risk_page():
    st.title("🚨 Positions at Risk (Thesis Monitoring)")
    st.markdown("Monitor decay in the original investment thesis for active signals.")
    
    try:
        from signal_ledger import init_ledger_db
        init_ledger_db()
        with sqlite3.connect("data/signal_ledger.sqlite") as conn:
            df = pd.read_sql("SELECT * FROM signal_ledger WHERE Status = 'ACTIVE' ORDER BY SignalDate DESC", conn)
            
        if df.empty:
            st.info("No active signals found in the ledger.")
            return
            
        # Parse JSON columns and calculate basic stuff
        # (Assuming we have a snapshot somewhere in state. If not, we can't easily join current price unless we fetch it. We will use dummy or try to get it from state)
        from ui.components import get_snapshot
        snapshot = get_snapshot()
        
        parsed_data = []
        for _, row in df.iterrows():
            sym = row["Symbol"]
            curr_price = 0
            if not snapshot.empty and sym in snapshot["Symbol"].values:
                curr_price = snapshot.loc[snapshot["Symbol"] == sym, "Close"].values[0]
                
            entry_price = row["EntryPrice"]
            ret = (curr_price - entry_price) / entry_price if entry_price and curr_price else 0.0
            
            decay_reasons = []
            if row["DecayReasons"]:
                try: decay_reasons = json.loads(row["DecayReasons"])
                except: pass
                
            original_thesis = {}
            if row.get("OriginalThesis"):
                try: original_thesis = json.loads(row["OriginalThesis"])
                except Exception: pass
            
            nifty_at_entry = original_thesis.get("NiftyAtEntry")
            nifty_rows = snapshot[snapshot["Symbol"].isin(["^NSEI", "NIFTY 50", "Nifty 50"])]
            nifty_current = float(nifty_rows["Close"].values[0]) if not nifty_rows.empty else None
            
            if nifty_at_entry and nifty_current and nifty_at_entry > 0:
                nifty_ret = (nifty_current - nifty_at_entry) / nifty_at_entry
                rel_ret = ret - nifty_ret
                rel_ret_display = f"{rel_ret:.2%}"
                nifty_ret_display = f"{nifty_ret:.2%}"
            else:
                rel_ret_display = "N/A"
                nifty_ret_display = "N/A"
                
            parsed_data.append({
                "Symbol": sym,
                "EntryDate": row["EntryDate"],
                "EntryPrice": entry_price,
                "CurrentPrice": curr_price,
                "Return": f"{ret:.2%}",
                "Nifty Return": nifty_ret_display,
                "Rel Return vs Nifty": rel_ret_display,
                "DecayState": row["DecayState"],
                "DecayReasons": ", ".join(decay_reasons) if decay_reasons else "None"
            })
            
        res_df = pd.DataFrame(parsed_data)
        st.dataframe(res_df, hide_index=True)
        
    except Exception as e:
        st.error(f"Error loading signal ledger: {e}")