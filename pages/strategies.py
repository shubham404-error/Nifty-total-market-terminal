import streamlit as st
import pandas as pd
from engine import download_prices, calculate_indicators, add_days_since_cross, investor_quality_gate, load_dvm_scores
from ui.components import get_snapshot, get_convergence, terminal_header, page_intro, guide, card, require_scan, ai_prefilter_note
from ui.charts import market_chart
from state import _invalidate_strategy_state, _ensure_ai_strategy_outputs, _ai_register_strategy_output, _strategy_cache_valid, _current_scan_id
from scoring import build_ai_confluence_pool, build_final_buy_list, _build_emerging_scored, build_emerging_buy_list
from ai_service import _render_list_ai_terminal, _gemini_reply, _ai_consume_call

def strategy_page(strategy: str):
    require_scan()
    snapshot = get_snapshot().copy()
    indicators = st.session_state["indicators"]

    titles = {
        "regime": ("Market Regime", "Long-term trend context using 50/200 SMA."),
        "momentum": ("9/21 EMA Momentum", "Short-term direction, fresh crosses and volume confirmation."),
        "swing": ("20/50 Swing Structure", "Medium-term alignment with relative-strength context."),
        "pullback": ("EMA 255 Pullback", "Oversold price near long-term support with quality context."),
    }
    title, subtitle = titles[strategy]
    terminal_header(title, subtitle)

    explanations = {
        "regime": ("WHAT DO 50 / 200 SMA MEAN?", "The 50-day average tracks the medium-term trend and the 200-day average is a long-term trend reference. When the 50 SMA is above the 200 SMA, the app treats long-term structure as bullish. This is context, not a standalone buy signal."),
        "momentum": ("WHAT DOES 9 / 21 EMA MOMENTUM MEAN?", "The 9 EMA reacts faster than the 21 EMA. A fresh 9-above-21 cross can signal strengthening short-term momentum. Established alignment means momentum is already positive, while volume confirmation adds evidence of participation."),
        "swing": ("WHAT DOES 20 / 50 SWING STRUCTURE MEAN?", "The 20-day and 50-day simple moving averages describe medium-term trend structure. A 20 SMA above the 50 SMA indicates bullish swing alignment. Relative strength and volume provide additional quality context."),
        "pullback": ("WHAT DOES EMA 255 PULLBACK MEAN?", "EMA 255 is used as a long-term trend reference. This setup looks for oversold price action near that level. RSI below 35 and proximity to EMA 255 create the trigger, but oversold does not automatically mean buy."),
    }
    expander_title, expander_text = explanations[strategy]
    with st.expander(expander_title, expanded=False):
        st.write(expander_text)

    filter_col, liquidity_col = st.columns([2,1])
    with liquidity_col:
        liquidity_filter = st.selectbox("Liquidity", ["All","₹1 Cr+","₹5 Cr+","₹25 Cr+"], index=0, key=f"liq_{strategy}")
    if strategy == "regime":
        table=snapshot.loc[snapshot["BullRegime"]].copy()
        columns=["Symbol","Company","Close","SMA50","SMA200","DaysSince50_200","RS3MPct","AvgTradedValue20","LiquidityBucket"]
        table["State"]="BULLISH"
        columns.append("State")
    elif strategy == "momentum":
        with filter_col:
            mode=st.radio("View",["Fresh Cross","Bullish Momentum","Volume Confirmed","20D Breakout"],horizontal=True)
        masks={"Fresh Cross":snapshot["MomentumFresh"],"Bullish Momentum":snapshot["BullMomentum"],"Volume Confirmed":snapshot["VolumeConfirmedMomentum"],"20D Breakout":snapshot["Breakout20"]}
        table=snapshot.loc[masks[mode]].copy()
        columns=["Symbol","Company","Close","EMA9","EMA21","DaysSince9_21","RSI14","RS3MPct","VolumeRatio","AvgTradedValue20","LiquidityBucket","ATRPercent"]
    elif strategy == "swing":
        table=snapshot.loc[snapshot["BullSwing"]].copy()
        columns=["Symbol","Company","Close","SMA20","SMA50","DaysSince20_50","RSI14","RS3MPct","RS6MPct","VolumeRatio","AvgTradedValue20","ATRPercent"]
    else:
        table=snapshot.loc[snapshot["Pullback"]].copy()
        columns=["Symbol","Company","Close","RSI14","EMA255DistancePct","BullRegime","BullSwing","RS3MPct","VolumeRatio","AvgTradedValue20","LiquidityBucket","ATRPercent"]

    thresholds={"All":0,"₹1 Cr+":1_00_00_000,"₹5 Cr+":5_00_00_000,"₹25 Cr+":25_00_00_000}
    table=table.loc[table["AvgTradedValue20"].fillna(0)>=thresholds[liquidity_filter], columns].copy()
    st.metric("QUALIFYING STOCKS", f"{len(table):,}")

    search=st.text_input("Search",placeholder="Symbol or company",key=f"search_{strategy}")
    if search:
        table=table.loc[table["Symbol"].str.contains(search,case=False,na=False)|table["Company"].str.contains(search,case=False,na=False)]
    st.dataframe(table,use_container_width=True,hide_index=True,height=520,column_config={
        "RS3MPct":st.column_config.NumberColumn("RS 3M %ile",format="%.0f"),
        "RS6MPct":st.column_config.NumberColumn("RS 6M %ile",format="%.0f"),
        "VolumeRatio":st.column_config.NumberColumn("Volume x",format="%.2f"),
        "AvgTradedValue20":st.column_config.NumberColumn("20D Traded Value",format="₹ %.0f"),
        "ATRPercent":st.column_config.NumberColumn("ATR %",format="%.2f%%"),
    })

    st.markdown('<div class="section-kicker">Chart console</div>',unsafe_allow_html=True)
    show_chart=st.toggle("SHOW STRATEGY CHART",value=True,key=f"chart_toggle_{strategy}")
    if show_chart and not table.empty:
        c1,c2=st.columns([2,1])
        with c1: chosen=st.selectbox("Select stock",table["Symbol"].tolist(),key=f"chart_stock_{strategy}")
        with c2: chart_days=st.selectbox("Chart window",[90,180,252,365],index=1,key=f"chart_days_{strategy}")
        row=snapshot.loc[snapshot["Symbol"]==chosen].iloc[0]
        frame=indicators.loc[indicators["Yahoo Symbol"]==row["Yahoo Symbol"]].copy()
        if strategy=="regime": overlays=["SMA50","SMA200"]; crosses=["Cross50_200"]; levels=[(30,"RSI 30"),(70,"RSI 70")]
        elif strategy=="momentum": overlays=["EMA9","EMA21","EMA255"]; crosses=["Cross9_21"]; levels=[(50,"RSI 50"),(70,"RSI 70")]
        elif strategy=="swing": overlays=["SMA20","SMA50","EMA255"]; crosses=["Cross20_50"]; levels=[(50,"RSI 50"),(70,"RSI 70")]
        else: overlays=["EMA255"]; crosses=[]; levels=[(35,"BUY ZONE 35"),(50,"RSI 50"),(70,"RSI 70")]
        st.caption("Price structure, 20-day average volume and RSI are shown together.")
        st.plotly_chart(market_chart(frame,chosen,overlays,rsi_col="RSI14",days=int(chart_days),cross_columns=crosses,rsi_lines=levels),use_container_width=True,config={"displaylogo":False,"scrollZoom":True})


def regime_page():
    strategy_page("regime")


def momentum_page():
    strategy_page("momentum")


def swing_page():
    strategy_page("swing")


def pullback_page():
    strategy_page("pullback")


