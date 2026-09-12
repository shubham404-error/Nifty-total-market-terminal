import streamlit as st
import pandas as pd
from engine import download_prices, calculate_indicators, add_days_since_cross, investor_quality_gate, load_dvm_scores
from ui.components import get_snapshot, get_convergence, terminal_header, page_intro, guide, card, require_scan, ai_prefilter_note
from ui.charts import market_chart
from state import _invalidate_strategy_state, _ensure_ai_strategy_outputs, _ai_register_strategy_output, _strategy_cache_valid, _current_scan_id
from scoring import build_ai_confluence_pool, build_final_buy_list, _build_emerging_scored, build_emerging_buy_list
from ai_service import _render_list_ai_terminal, _gemini_reply, _ai_consume_call

def home_page():
    terminal_header(
        "Home",
        "A guided workspace for finding and researching Indian equity setups",
        show_logo=True,
    )

    page_intro(
        "Find the signal. Check the context. Do your homework.",
        "Start with one market scan, explore a setup that matches your style, "
        "inspect the chart, and then move to the shortlist. You do not need to "
        "understand every indicator to use the app.",
    )

    st.info("MARKET TIMING NOTICE. This terminal is designed for after-market-hours research using completed daily candles. Run the scan after the NSE market has closed and use the results to prepare your research or watchlist for the next session. It is not a live intraday scanner.")

    guide(
        "Start here. Let's scan.",
        "The workflow is simple. The analysis underneath it is not.",
        [
            "Scan the market once. The result is reused across the app.",
            "Explore Market Health, Momentum, Swing, Pullback, or Emerging Setups.",
            "Check the stock's chart and then use Confluence and Final Buy List to narrow your research list.",
            "Use the new Nifty AI Analyst to ask, in plain English, why a stock qualified, what it means, and what to watch next.",
        ],
    )

    snapshot = get_snapshot()
    conv = get_convergence()
    universe_count = len(st.session_state.get("universe", []))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stocks in universe", f"{universe_count:,}" if universe_count else "—")
    c2.metric("Stocks scanned", f"{len(snapshot):,}" if not snapshot.empty else "—")
    c3.metric(
        "Bullish long-term trend",
        f"{int(snapshot['BullRegime'].sum()):,}" if not snapshot.empty else "—",
    )
    c4.metric(
        "High-conviction candidates",
        f"{int((conv['ConvergenceScore'] >= 65).sum()):,}" if not conv.empty else "—",
    )

    st.markdown('<div class="section-title">What each section means</div>', unsafe_allow_html=True)

    cards = st.columns(4)
    sections = [
        (
            "Market Health",
            "The big-picture filter. Tells you whether the long-term trend is helping or fighting you.",
        ),
        (
            "Momentum",
            "Fast money, fast signals. Spots fresh short-term momentum using the 9/21 EMA.",
        ),
        (
            "Swing",
            "The calmer setup. Looks for multi-week trend alignment using the 20/50 averages.",
        ),
        (
            "Pullback",
            "Hunting the pullback. Finds oversold names sitting close to their long-term EMA 255.",
        ),
    ]

    for col, (title, text) in zip(cards, sections):
        with col:
            card(title, text)

    st.markdown('<div class="section-title">New. Nifty AI Analyst</div>', unsafe_allow_html=True)

    ai_col, ai_note_col = st.columns([2.2, 1])
    with ai_col:
        card(
            "Ask why a stock qualified",
            "Nifty AI Analyst is integrated into the terminal so you can select a stock and ask why it appeared in a strategy, what the setup means in plain English, what looks positive, and what to monitor next. It uses the terminal's current strategy and market context rather than acting as a separate stock-picking engine.",
        )
    with ai_note_col:
        st.info(
            f"AI verification uses a {AI_STRATEGY_PREFILTER_SCORE}+ high-conviction "
            "candidate pool for Confluence and buy-list checks. This improves efficiency "
            "without changing the visible strategy rules or rankings."
        )

    st.markdown('<div class="section-title">How to read a stock</div>', unsafe_allow_html=True)

    read = st.columns(3)
    with read[0]:
        card("Signal", "The rule that made the stock qualify.")
    with read[1]:
        card("Chart", "The price action that tells you whether the signal looks healthy or weak.")
    with read[2]:
        card("Fundamentals", "Valuation and business-quality fields to review after technical screening.")


    with st.expander("WHAT IS EMERGING SETUPS?", expanded=False):
        st.markdown(
            """
**Emerging Setups** is a separate discovery screen for newer stocks that do not yet
have enough trading history for the full long-term strategy suite.

It does **not** weaken the main scanner and it does **not** replace the 200-day SMA
or 255-day EMA requirements. Instead, it asks a different question:

> *"Does this newer stock already show promising short- and medium-term behaviour?"*

It uses indicators that can be assessed without SMA 200 or EMA 255, such as
**9/21 EMA momentum, 20/50 swing structure, RSI, relative strength, volume,
ATR and liquidity**.

Use it as an **early research/watchlist tool**, not as a replacement for the
Confluence or Final Buy List. A stock can graduate into the normal strategy suite
once enough history becomes available.
"""
        )

    st.caption(
        "Research tool only. Signals are not investment recommendations and are not guarantees of future returns."
    )


