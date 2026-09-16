import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import os
from pathlib import Path

st.set_page_config(page_title="Performance Terminal", page_icon="📈", layout="wide")

current_dir = Path(__file__).parent
DB_PATH = current_dir.parent / "data" / "signal_ledger.sqlite"

def load_data():
    if not DB_PATH.exists():
        st.error(f"Database not found at {DB_PATH}")
        return pd.DataFrame()
        
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql("""
            SELECT l.Symbol, l.SignalDate, l.EntryDate, l.EntryPrice, l.Status, l.CloseReason, l.DataStatus,
                   p.CurrentPrice, p.ReturnFromEntry, p.RunningMFE, p.RunningMAE, p.DaysHeld, p.NiftyReturn,
                   l.OriginalThesis
            FROM signal_ledger l
            LEFT JOIN signal_performance p ON l.SignalID = p.SignalID
        """, conn)
    return df

st.title("Performance Terminal")

df = load_data()

if df.empty:
    st.info("No performance data available.")
    st.stop()

active = df[df["Status"] == "ACTIVE"]
closed = df[df["Status"] == "CLOSED"]
legacy = df[df["DataStatus"] == "LEGACY"]

c1, c2, c3 = st.columns(3)
c1.metric("Active Signals", len(active))
c2.metric("Closed Signals", len(closed))
c3.metric("Legacy Signals Migrated", len(legacy))

st.subheader("Performance Distribution")
returns = df["ReturnFromEntry"].dropna() * 100
if not returns.empty:
    fig = px.histogram(returns, nbins=50, title="Return from Entry (%)", text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

st.subheader("MFE / MAE Bounds")
perf_df = df.dropna(subset=["RunningMFE", "RunningMAE", "ReturnFromEntry"]).copy()
if not perf_df.empty:
    perf_df["ReturnFromEntry"] *= 100
    perf_df["RunningMFE"] *= 100
    perf_df["RunningMAE"] *= 100
    
    # Sort for better visualization
    perf_df = perf_df.sort_values("ReturnFromEntry", ascending=False)
    
    fig2 = go.Figure()
    
    fig2.add_trace(go.Bar(
        x=perf_df["Symbol"],
        y=perf_df["ReturnFromEntry"],
        name="Return (%)",
        marker_color="blue"
    ))
    
    fig2.add_trace(go.Scatter(
        x=perf_df["Symbol"],
        y=perf_df["RunningMFE"],
        name="MFE (%)",
        mode="markers",
        marker_color="green"
    ))
    
    fig2.add_trace(go.Scatter(
        x=perf_df["Symbol"],
        y=perf_df["RunningMAE"],
        name="MAE (%)",
        mode="markers",
        marker_color="red"
    ))
    
    fig2.update_layout(title="Performance with MFE/MAE Bounds", barmode="overlay")
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Signal Data")
st.dataframe(df, use_container_width=True, hide_index=True)