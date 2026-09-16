import streamlit as st
import sqlite3
import pandas as pd
from ui.components import get_snapshot, terminal_header, require_scan
import plotly.express as px

def market_structure_page():
    require_scan()
    terminal_header("Market Structure", "Global index-health dashboard showing Nifty 50 MAs, Breadth, and Stage Distribution.")
    
    try:
        from market_regime import init_regime_db
        init_regime_db()
        with sqlite3.connect("data/signal_ledger.sqlite") as conn:
            df = pd.read_sql("SELECT * FROM regime_history ORDER BY date DESC", conn)
            
        if df.empty:
            st.info("No market health history available. Run the scan engine.")
            return
            
        current = df.iloc[0]
        
        # Calculate Index MA Stack
        st.subheader("Nifty 50 Index MA Stack")
        try:
            import yfinance as yf
            nifty = yf.download("^NSEI", period="2y", progress=False, multi_level_index=False)
            if not nifty.empty and "Close" in nifty.columns:
                close = nifty["Close"].iloc[-1]
                ema21 = nifty["Close"].ewm(span=21, adjust=False).mean().iloc[-1]
                sma50 = nifty["Close"].rolling(50).mean().iloc[-1]
                sma200 = nifty["Close"].rolling(200).mean().iloc[-1]
                ema250 = nifty["Close"].ewm(span=250, adjust=False).mean().iloc[-1]
                
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("NIFTY 50", f"{close:.2f}")
                m2.metric("21 EMA", f"{ema21:.2f}", f"{(close/ema21)-1:.2%}")
                m3.metric("50 SMA", f"{sma50:.2f}", f"{(close/sma50)-1:.2%}")
                m4.metric("200 SMA", f"{sma200:.2f}", f"{(close/sma200)-1:.2%}")
                m5.metric("250 EMA", f"{ema250:.2f}", f"{(close/ema250)-1:.2%}")
                
                stack_status = []
                if close > ema21: stack_status.append("Price > 21 EMA")
                if ema21 > sma50: stack_status.append("21 EMA > 50 SMA")
                if sma50 > sma200: stack_status.append("50 SMA > 200 SMA")
                if sma200 > ema250: stack_status.append("200 SMA > 250 EMA")
                st.caption("Stack check: " + " | ".join(stack_status) if stack_status else "Broken Stack")
            else:
                st.warning("Failed to fetch Nifty 50 data.")
        except Exception as e:
            st.warning(f"Could not load Nifty MA stack: {e}")
            
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
        c3.metric("Breadth (Above 20 SMA)", f"{current['breadth_20']:.2%}")
        c4.metric("Breadth Trend", current["breadth_trend"])
        
        c5, c6 = st.columns(2)
        c5.metric("Structural Health (Above 50/200)", f"{current['structural_health']:.2%}")
        c6.metric("Index Stage", current["index_stage"])
        
        snapshot = get_snapshot()
        
        st.subheader("Stage Distribution")
        stage_counts = snapshot["Stage"].value_counts().reset_index()
        stage_counts.columns = ["Stage", "Count"]
        fig = px.bar(stage_counts, x="Stage", y="Count", title="Current Market Stage Distribution", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Regime Transition History")
        transitions = []
        last_r = None
        start_date = None
        for idx, row in df.iloc[::-1].iterrows(): # iterate chronologically
            if row["regime"] != last_r:
                if last_r is not None:
                    transitions.append({"Transition": f"{last_r} -> {row['regime']}", "Date": row["date"]})
                last_r = row["regime"]
        
        if transitions:
            t_df = pd.DataFrame(transitions[::-1])
            st.dataframe(t_df, hide_index=True)
            
    except Exception as e:
        st.error(f"Error loading market structure: {e}")