import streamlit as st
import pandas as pd
from engine import calculate_indicators, add_days_since_cross, investor_quality_gate, load_dvm_scores
from ui.components import get_snapshot, terminal_header, page_intro, require_scan
from ui.charts import market_chart
from decision_config import V4_CONFIG

def pullback_page():
    require_scan()
    snapshot = get_snapshot().copy()
    indicators = st.session_state["indicators"]

    terminal_header("EMA 255 Pullback", "Oversold price near long-term support with quality context.")
    with st.expander("WHAT DOES EMA 255 PULLBACK MEAN?", expanded=False):
        st.write("EMA 255 is used as a long-term trend reference. This setup looks for oversold price action near that level. RSI below 35 and proximity to EMA 255 create the trigger, but oversold does not automatically mean buy.")

    filter_col, liquidity_col = st.columns([2,1])
    with liquidity_col:
        liquidity_filter = st.selectbox("Liquidity", ["All",",11 Cr+",",15 Cr+",",125 Cr+"], index=0, key="liq_pullback")

    table=snapshot.loc[snapshot.get("Pullback", pd.Series(False, index=snapshot.index))].copy()
    columns=["Symbol","Company","Close","RSI14","EMA255DistancePct","BullRegime","BullSwing","RS3MPct","VolumeRatio","AvgTradedValue20","LiquidityBucket","ATRPercent"]

    thresholds={"All":0,",11 Cr+":V4_CONFIG["LIQUIDITY_THRESHOLD"],",15 Cr+":5_00_00_000,",125 Cr+":25_00_00_000}
    table=table.loc[table["AvgTradedValue20"].fillna(0)>=thresholds[liquidity_filter]].copy()
    
    # Check if columns exist before subsetting
    valid_cols = [c for c in columns if c in table.columns]
    table = table[valid_cols]

    st.metric("QUALIFYING STOCKS", f"{len(table):,}")

    search=st.text_input("Search",placeholder="Symbol or company",key="search_pullback")
    if search:
        table=table.loc[table["Symbol"].str.contains(search,case=False,na=False)|table["Company"].str.contains(search,case=False,na=False)]
    st.dataframe(table,use_container_width=True,hide_index=True,height=520,column_config={
        "RS3MPct":st.column_config.NumberColumn("RS 3M %ile",format="%.0f"),
        "RS6MPct":st.column_config.NumberColumn("RS 6M %ile",format="%.0f"),
        "VolumeRatio":st.column_config.NumberColumn("Volume x",format="%.2f"),
        "AvgTradedValue20":st.column_config.NumberColumn("20D Traded Value",format=",1 %.0f"),
        "ATRPercent":st.column_config.NumberColumn("ATR %",format="%.2f%%"),
    })

    st.markdown('<div class="section-kicker">Chart console</div>',unsafe_allow_html=True)
    show_chart=st.toggle("SHOW STRATEGY CHART",value=True,key="chart_toggle_pullback")
    if show_chart and not table.empty:
        c1,c2=st.columns([2,1])
        with c1: chosen=st.selectbox("Select stock",table["Symbol"].tolist(),key="chart_stock_pullback")
        with c2: chart_days=st.selectbox("Chart window",[90,180,252,365],index=1,key="chart_days_pullback")
        row=snapshot.loc[snapshot["Symbol"]==chosen].iloc[0]
        frame=indicators.loc[indicators["Yahoo Symbol"]==row["Yahoo Symbol"]].copy()
        overlays=["EMA255"]; crosses=[]; levels=[(35,"BUY ZONE 35"),(50,"RSI 50"),(70,"RSI 70")]
        st.caption("Price structure, 20-day average volume and RSI are shown together.")
        st.plotly_chart(market_chart(frame,chosen,overlays,rsi_col="RSI14",days=int(chart_days),cross_columns=crosses,rsi_lines=levels),use_container_width=True,config={"displaylogo":False,"scrollZoom":True})