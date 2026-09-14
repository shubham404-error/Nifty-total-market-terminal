import streamlit as st
import sqlite3
import pandas as pd

def positions_at_risk_page():
    st.title("🚨 Positions at Risk (Thesis Monitoring)")
    st.markdown("Monitor decay in the original investment thesis for active signals.")
    
    try:
        with sqlite3.connect("data/signal_ledger.sqlite") as conn:
            df = pd.read_sql("SELECT * FROM signal_ledger ORDER BY SignalDate DESC", conn)
            
        if df.empty:
            st.info("No signals found in the ledger.")
            return
            
        st.dataframe(df)
        
    except Exception as e:
        st.error(f"Error loading signal ledger: {e}")