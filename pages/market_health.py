import streamlit as st
import sqlite3
import pandas as pd

def market_health_page():
    st.title("🩺 Market Health")
    st.markdown("Monitor broad market participation and trend.")
    
    try:
        with sqlite3.connect("data/signal_ledger.sqlite") as conn:
            df = pd.read_sql("SELECT * FROM regime_history ORDER BY date DESC", conn)
            
        if df.empty:
            st.info("No market health history available. Run the scan engine.")
            return
            
        st.dataframe(df)
        
    except Exception as e:
        st.error(f"Error loading market health: {e}")