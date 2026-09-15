import streamlit as st
import sqlite3
import pandas as pd
import json

def positions_at_risk_page():
    st.title("🚨 Positions at Risk (Thesis Monitoring)")
    st.markdown("Monitor decay in the original investment thesis for active signals.")
    
    try:
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
                
            parsed_data.append({
                "Symbol": sym,
                "EntryDate": row["EntryDate"],
                "EntryPrice": entry_price,
                "CurrentPrice": curr_price,
                "Return": f"{ret:.2%}",
                "DecayState": row["DecayState"],
                "DecayReasons": ", ".join(decay_reasons) if decay_reasons else "None"
            })
            
        res_df = pd.DataFrame(parsed_data)
        st.dataframe(res_df, hide_index=True)
        
    except Exception as e:
        st.error(f"Error loading signal ledger: {e}")