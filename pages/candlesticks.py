import streamlit as st
import pandas as pd
from ui.components import get_snapshot, terminal_header, require_scan
from ui.charts import market_chart

def candlesticks_page():
    require_scan()
    snapshot = get_snapshot().copy()
    indicators = st.session_state["indicators"]

    terminal_header("Candlestick Scanner", "Independent geometric pattern detection.")

    filter_col, mode_col, rs_col = st.columns([2, 1, 1])
    with mode_col:
        mode = st.radio("Mode", ["Research (All)", "Production (Valid Entry)"])
    with filter_col:
        all_patterns = ["All Detected Patterns", "Hammer", "Bullish Engulfing", "Morning Star", "Strong Breakout Candle", "Inside Bar Breakout", "Inverted Hammer", "Harami"]
        selected_pattern = st.selectbox("Candlestick Pattern", all_patterns, index=0)
    with rs_col:
        require_rs = st.checkbox("Require RS > 70 (Optional)", value=False)
        require_stage = st.checkbox("Require Stage 2 (Optional)", value=False)

    table = snapshot.copy()
    
    if mode == "Production (Valid Entry)":
        table = table[table["EntryPattern"].notna() & (table["EntryPattern"] != "None")]
    else:
        table = table[table["Pattern"].notna() & (table["Pattern"] != "None")]

    if selected_pattern != "All Detected Patterns":
        table = table[table["Pattern"] == selected_pattern]

    if require_rs:
        table = table[table["RS_Rating"] >= 70]
    if require_stage:
        table = table[table["Stage"] == 2]

    columns=["Symbol","Company","Close","Pattern","EntryPattern","VolumeRatio","AvgTradedValue20","Stage","RS_Rating"]
    valid_cols = [c for c in columns if c in table.columns]
    table = table[valid_cols]
    
    st.metric("QUALIFYING STOCKS", f"{len(table):,}")

    search=st.text_input("Search",placeholder="Symbol or company",key="search_candles")
    if search:
        table=table.loc[table["Symbol"].str.contains(search,case=False,na=False)|table["Company"].str.contains(search,case=False,na=False)]
    st.dataframe(table,use_container_width=True,hide_index=True,height=520,column_config={
        "VolumeRatio":st.column_config.NumberColumn("Volume x",format="%.2f"),
        "AvgTradedValue20":st.column_config.NumberColumn("20D Traded Value",format=",1 %.0f"),
        "RS_Rating":st.column_config.NumberColumn("RS Rating",format="%.0f"),
    })

    st.markdown('<div class="section-kicker">Chart console</div>',unsafe_allow_html=True)
    if not table.empty:
        c1,c2=st.columns([2,1])
        with c1: chosen=st.selectbox("Select stock",table["Symbol"].tolist(),key="chart_stock_candles")
        with c2: chart_days=st.selectbox("Chart window",[30, 90,180],index=0,key="chart_days_candles")
        row=snapshot.loc[snapshot["Symbol"]==chosen].iloc[0]
        frame=indicators.loc[indicators["Yahoo Symbol"]==row["Yahoo Symbol"]].copy()
        overlays=["SMA20"]; crosses=[]; levels=[(50,"RSI 50")]
        st.plotly_chart(market_chart(frame,chosen,overlays,rsi_col="RSI14",days=int(chart_days),cross_columns=crosses,rsi_lines=levels),use_container_width=True,config={"displaylogo":False,"scrollZoom":True})
