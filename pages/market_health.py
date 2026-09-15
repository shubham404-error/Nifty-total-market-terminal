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
            
        current = df.iloc[0]
        st.subheader("Current Regime")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Regime", current["regime"])
        
        # Calculate days in regime
        regime_val = current["regime"]
        days_in_regime = 0
        for val in df["regime"]:
            if val == regime_val:
                days_in_regime += 1
            else:
                break
        c2.metric("Days in Regime", days_in_regime)
        c3.metric("Breadth 20", f"{current['breadth_20']:.2%}")
        c4.metric("Breadth Trend", current["breadth_trend"])
        
        c5, c6 = st.columns(2)
        c5.metric("Structural Health", f"{current['structural_health']:.2%}")
        c6.metric("Index Stage", current["index_stage"])
        
        st.subheader("Regime Transition History")
        transitions = []
        last_r = None
        start_date = None
        for idx, row in df.iloc[::-1].iterrows(): # iterate chronologically
            if row["regime"] != last_r:
                if last_r is not None:
                    transitions.append({"Transition": f"{last_r} → {row['regime']}", "Date": row["date"]})
                last_r = row["regime"]
        
        if transitions:
            t_df = pd.DataFrame(transitions[::-1])
            st.dataframe(t_df, hide_index=True)
            
        st.subheader("Raw History")
        st.dataframe(df, hide_index=True)
        
    except Exception as e:
        st.error(f"Error loading market health: {e}")