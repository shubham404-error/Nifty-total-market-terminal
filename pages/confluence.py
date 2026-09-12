import streamlit as st
import pandas as pd
from engine import download_prices, calculate_indicators, add_days_since_cross, investor_quality_gate, load_dvm_scores
from ui.components import get_snapshot, get_convergence, terminal_header, page_intro, guide, card, require_scan, ai_prefilter_note
from ui.charts import market_chart
from state import _invalidate_strategy_state, _ensure_ai_strategy_outputs, _ai_register_strategy_output, _strategy_cache_valid, _current_scan_id
from scoring import build_ai_confluence_pool, build_final_buy_list, _build_emerging_scored, build_emerging_buy_list
from ai_service import _render_list_ai_terminal, _gemini_reply, _ai_consume_call

def convergence_page():
    require_scan()
    df=get_convergence().copy()
    terminal_header("Confluence","Setup-aware ranking. Trend, pullback, fresh momentum and breakout paths are evaluated separately.")

    with st.expander("WHAT DO THESE COLUMNS MEAN?", expanded=False):
        st.markdown("**Setup** is the qualifying strategy path. **Convergence Score** measures that path strength. **RS 3M %ile** compares strength within the scanned universe. **Volume x** compares current participation with normal volume. **Liquidity** uses 20-day average traded value. **ATR %** is volatility.")

    c1,c2,c3,c4=st.columns(4)
    c1.metric("ACTIVE SETUPS",f"{int((df['Setup']!='No active setup').sum()):,}")
    c2.metric("SCORE 80+",f"{int((df['ConvergenceScore']>=80).sum()):,}")
    c3.metric("VOLUME BREAKOUTS",f"{int(df['Breakout20'].sum()):,}")
    c4.metric("LIQUID",f"{int(df['LiquidityEligible'].sum()):,}")

    st.toggle("Use Confluence v2 (Shadow Mode - RSI fix)", value=False, key="use_confluence_v2")

    f1,f2=st.columns(2)
    with f1: min_score=st.slider("Minimum setup score",0,100,60,5)
    with f2: setup_filter=st.selectbox("Setup type",["All"]+sorted([x for x in df['Setup'].dropna().unique() if x!='No active setup']))
    output=df.loc[(df["ConvergenceScore"]>=min_score)&(df["Setup"]!="No active setup")].copy()
    if setup_filter!="All": output=output.loc[output["Setup"]==setup_filter]
    st.session_state["ai_confluence_output"] = output.copy()
    _ai_register_strategy_output(
        "confluence",
        output,
        {
            "minimum_score": float(min_score),
            "setup_filter": setup_filter,
        },
    )
    cols=["Symbol","Company","Setup","Close","ConvergenceScore","TrendContinuationScore","PullbackScore","FreshMomentumScore","BreakoutScore","RS3MPct","VolumeRatio","LiquidityBucket","ATRPercent","RSI14","EMA255DistancePct"]
    output=output[cols].copy().reset_index(drop=True)
    output.insert(0,"Rank",range(1,len(output)+1))
    st.dataframe(output,use_container_width=True,hide_index=True,height=560)
    st.download_button("EXPORT CONFLUENCE CSV",data=output.to_csv(index=False).encode(),file_name="nifty_total_market_confluence.csv",mime="text/csv")

    _render_list_ai_terminal(
        "Confluence",
        output,
        "confluence_ai_terminal",
    )

    st.markdown('<div class="section-kicker">Confluence chart</div>',unsafe_allow_html=True)
    if st.toggle("SHOW CONVERGENCE CHART",value=True,key="chart_toggle_convergence") and not output.empty:
        selected=st.selectbox("Select stock",output["Symbol"].tolist(),key="chart_stock_convergence")
        row=df.loc[df["Symbol"]==selected].iloc[0]
        frame=st.session_state["indicators"].loc[st.session_state["indicators"]["Yahoo Symbol"]==row["Yahoo Symbol"]].copy()
        st.plotly_chart(market_chart(frame,selected,["EMA9","EMA21","SMA20","SMA50","SMA200","EMA255"],rsi_col="RSI14",days=252,cross_columns=["Cross9_21","Cross20_50","Cross50_200"],rsi_lines=[(30,"RSI 30"),(35,"BUY ZONE 35"),(50,"RSI 50"),(70,"RSI 70")]),use_container_width=True,config={"displaylogo":False,"scrollZoom":True})


