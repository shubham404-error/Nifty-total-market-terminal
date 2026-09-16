import streamlit as st
import pandas as pd
from ui.components import get_snapshot, terminal_header, require_scan
from engine import historical_snapshot
import plotly.express as px

def rs_and_stage_page():
    require_scan()
    snapshot = get_snapshot().copy()
    indicators = st.session_state["indicators"]
    universe = st.session_state["universe"]
    scan_date = st.session_state.get("scan_date")

    terminal_header("RS & Stage Analysis", "Momentum screener and relative strength leaderboards.")

    if not scan_date:
        st.error("Missing scan date. Run Scan Engine again.")
        return

    # Calculate T-5 changes
    with st.spinner("Calculating 5-day RS transition..."):
        try:
            t_minus_5 = historical_snapshot(indicators, universe, scan_date, 5)
            t_minus_5 = t_minus_5[["Symbol", "Raw_RS_Rating", "Stage"]].rename(
                columns={"Raw_RS_Rating": "RS_T5", "Stage": "Stage_T5"}
            )
            snapshot = snapshot.merge(t_minus_5, on="Symbol", how="left")
            snapshot["RS_Change_5D"] = snapshot["Raw_RS_Rating"] - snapshot["RS_T5"]
        except Exception as e:
            st.warning(f"Could not calculate 5-day transition (need more historical data): {e}")

    # Layout
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("RS Rating Distribution")
        fig = px.histogram(snapshot, x="Raw_RS_Rating", nbins=50, title="RS Rating Histogram")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Stage Distribution")
        stage_counts = snapshot["Stage"].value_counts().reset_index()
        stage_counts.columns = ["Stage", "Count"]
        fig2 = px.pie(stage_counts, values="Count", names="Stage", title="Stage Distribution")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Top Rising RS (5-Day Momentum)")
    if "RS_Change_5D" in snapshot.columns:
        rising = snapshot.sort_values("RS_Change_5D", ascending=False).head(50)
        st.dataframe(rising[["Symbol", "Company", "Close", "Stage", "Raw_RS_Rating", "RS_T5", "RS_Change_5D"]], use_container_width=True)
    else:
        st.info("RS transition data not available.")
