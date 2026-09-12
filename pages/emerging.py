import streamlit as st
import pandas as pd
from engine import download_prices, calculate_indicators, add_days_since_cross, investor_quality_gate, load_dvm_scores
from ui.components import get_snapshot, get_convergence, terminal_header, page_intro, guide, card, require_scan, ai_prefilter_note
from ui.charts import market_chart
from state import _invalidate_strategy_state, _ensure_ai_strategy_outputs, _ai_register_strategy_output, _strategy_cache_valid, _current_scan_id
from scoring import build_ai_confluence_pool, build_final_buy_list, _build_emerging_scored, build_emerging_buy_list
from ai_service import _render_list_ai_terminal, _gemini_reply, _ai_consume_call

def emerging_setups_page():
    """
    Emerging Setups is an app.py-only discovery screen.

    It deliberately uses the existing market snapshot and DataQualityStatus
    classification. No market-data download, bars calculation, merge, or
    engine.py modification is performed here.
    """
    require_scan()

    snapshot = get_snapshot()
    indicators = st.session_state.get("indicators")
    if snapshot is None or snapshot.empty:
        st.warning("RUN A MARKET SCAN")
        return

    df = snapshot.copy()
    if "DataQualityStatus" not in df.columns:
        st.error(
            "The current market snapshot does not contain DataQualityStatus. "
            "Please run the current Scan Engine."
        )
        return

    # Source of truth for this page. Do not reconstruct history eligibility.
    working = df.loc[
        df["DataQualityStatus"].astype(str).str.strip().eq("Insufficient history")
    ].copy()

    terminal_header(
        "Emerging Setups",
        "Early-stage research for newer stocks. A separate scoring lane for names that do not yet qualify for the full long-term strategy suite.",
    )

    with st.expander("WHAT IS EMERGING SETUPS?", expanded=False):
        st.markdown(
            """
**Emerging Setups** is the early-discovery lane for stocks that the existing
scanner has already classified as **Insufficient history**.

It intentionally does **not** require **SMA 200** or **EMA 255**. Those
long-term indicators belong to the normal strategy suite once sufficient
history exists.

The page combines the shorter-history technical evidence already present in
the market snapshot with public fundamentals when available. It is designed
to find promising names early, not to bypass the stricter normal scanner.
"""
        )

    with st.expander("HOW TO USE THIS PAGE AS A RETAIL INVESTOR", expanded=False):
        st.markdown(
            """
1. **Start with Emerging Score**, then inspect the individual components.
2. **Prefer trend agreement**. 9 EMA above 21 EMA and 20 SMA above 50 SMA are stronger together than either alone.
3. **Look for participation**. Volume confirmation and a 20-day breakout make price strength more credible.
4. **Check relative strength**. A high 3-month percentile means the stock is outperforming much of the scanned universe.
5. **Use fundamentals as a second filter**, not as a replacement for the chart. Growth, profitability, leverage and valuation can improve or weaken the case.
6. **Use the Emerging Buy List only as a research shortlist**. Confirm the chart, liquidity, valuation, business quality and your own risk before investing.
"""
        )

    with st.expander("WHAT DO THESE INDICATORS AND SCORES MEAN?", expanded=False):
        st.markdown(
            """
### Emerging Score. 100 points

| Component | Points | What it rewards |
|---|---:|---|
| Bull Momentum | 15 | 9 EMA above 21 EMA |
| Bull Swing | 15 | 20 SMA above 50 SMA |
| Fresh Momentum | 10 | Recent 9/21 bullish momentum change |
| Volume Confirmation | 10 | Momentum supported by stronger participation |
| 20D Breakout | 10 | Recent breakout signal from the existing scanner |
| Relative Strength | 15 | 3-month percentile versus the scanned universe |
| RSI Context | 5 | Constructive momentum without blindly rewarding extreme RSI |
| Fundamentals | 20 | Growth, profitability, leverage and valuation when available |

**Technical score = 80. Fundamental score = 20.** Missing public fundamentals are
neutral, but the page reports fundamental coverage so a high score cannot be
mistaken for fully researched financial quality.

The score is a **ranking and discovery tool**, not a probability of return and
not a guaranteed buy signal.
"""
        )

    if working.empty:
        st.info(
            "There are currently no stocks classified as Insufficient history in the latest market snapshot."
        )
        return

    with st.spinner("Scoring emerging candidates from the current scan..."):
        working = _build_emerging_scored(snapshot)

    if working.empty:
        st.info("There are currently no emerging candidates after scoring the latest market snapshot.")
        return

    st.session_state["ai_emerging_working"] = working.copy()
    _ai_register_strategy_output(
        "emerging_setups",
        working,
        {"scan_id": _current_scan_id()},
    )

    def numeric_series(frame, column):
        if column in frame.columns:
            return pd.to_numeric(frame[column], errors="coerce")
        return pd.Series(float("nan"), index=frame.index)

    # -----------------------------
    # Controls.
    # -----------------------------
    c1, c2, c3 = st.columns([1.4, 1, 1])
    with c1:
        min_score = st.slider(
            "Minimum Emerging Score", 0, 100, 60, 5,
            key="emerging_min_score_v2",
        )
    with c2:
        liquidity_filter = st.selectbox(
            "Liquidity", ["All", "₹1 Cr+", "₹5 Cr+", "₹25 Cr+"],
            key="emerging_liquidity_v2",
        )
    with c3:
        bullish_only = st.toggle(
            "Prefer bullish structure", value=True,
            key="emerging_bullish_structure_v2",
        )

    liquidity_thresholds = {
        "All": 0,
        "₹1 Cr+": 1_00_00_000,
        "₹5 Cr+": 5_00_00_000,
        "₹25 Cr+": 25_00_00_000,
    }

    filtered = working.loc[working["Emerging Score"] >= min_score].copy()
    if bullish_only:
        bullish_mask = (
            filtered.get("BullMomentum", pd.Series(False, index=filtered.index)).fillna(False).astype(bool)
            | filtered.get("BullSwing", pd.Series(False, index=filtered.index)).fillna(False).astype(bool)
        )
        filtered = filtered.loc[bullish_mask].copy()

    traded_value = numeric_series(filtered, "AvgTradedValue20").fillna(0)
    filtered = filtered.loc[
        traded_value >= liquidity_thresholds[liquidity_filter]
    ].copy()

    filtered = filtered.sort_values(
        ["Emerging Score", "Technical Score", "RS3MPct", "Fundamental Score"],
        ascending=False,
        na_position="last",
    )

    # -----------------------------
    # Summary cards.
    # -----------------------------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("INSUFFICIENT-HISTORY STOCKS", f"{len(working):,}")
    c2.metric("PASSING SCREEN", f"{len(filtered):,}")
    c3.metric(
        "EMERGING SCORE 75+",
        f"{int((working['Emerging Score'] >= 75).sum()):,}",
    )
    c4.metric(
        "BULLISH STRUCTURE",
        f"{int(((working.get('BullMomentum', False).fillna(False).astype(bool)) & (working.get('BullSwing', False).fillna(False).astype(bool))).sum()):,}",
    )

    st.caption(
        "Source of history eligibility: DataQualityStatus from the existing Nifty Market Snapshot. "
        "SMA 200 and EMA 255 are intentionally not required."
    )

    # -----------------------------
    # Compact discovery table.
    # -----------------------------
    st.markdown('<div class="section-title">Emerging Research Candidates</div>', unsafe_allow_html=True)
    display_cols = [
        "Symbol", "Company", "Close", "Emerging Score", "Technical Score",
        "Fundamental Score", "Setup", "RS3MPct", "RSI14", "VolumeRatio",
        "LiquidityBucket", "Fundamental Coverage",
    ]
    display_cols = [c for c in display_cols if c in filtered.columns]
    st.dataframe(
        filtered[display_cols],
        use_container_width=True,
        hide_index=True,
        height=500,
        column_config={
            "Close": st.column_config.NumberColumn("Price", format="₹ %.2f"),
            "Emerging Score": st.column_config.NumberColumn("Score", format="%.1f"),
            "Technical Score": st.column_config.NumberColumn("Technical", format="%.1f"),
            "Fundamental Score": st.column_config.NumberColumn("Fundamentals", format="%.1f"),
            "RS3MPct": st.column_config.NumberColumn("RS 3M %ile", format="%.0f"),
            "RSI14": st.column_config.NumberColumn("RSI", format="%.1f"),
            "VolumeRatio": st.column_config.NumberColumn("Volume x", format="%.2f"),
            "Fundamental Coverage": st.column_config.NumberColumn("Fund. Coverage", format="%d/5"),
        },
    )

    st.download_button(
        "EXPORT EMERGING SETUPS CSV",
        data=filtered.to_csv(index=False).encode(),
        file_name="emerging_setups.csv",
        mime="text/csv",
    )

    # -----------------------------
    # Actionable research shortlist.
    # -----------------------------
    st.markdown('<div class="section-title">Emerging Buy List</div>', unsafe_allow_html=True)
    st.caption(
        "Strict research shortlist. This is deliberately harder to pass than the discovery table and is not an automated investment recommendation."
    )

    buy = build_emerging_buy_list(working)
    st.session_state["ai_emerging_buy_output"] = buy.copy()
    _ai_register_strategy_output(
        "emerging_buy_list",
        buy,
        {"scan_id": _current_scan_id()},
    )

    b1, b2, b3 = st.columns(3)
    b1.metric("EMERGING BUY CANDIDATES", f"{len(buy):,}")
    b2.metric("MIN SCORE", "75")
    b3.metric("MIN RS", "70th %ile")

    if buy.empty:
        st.info(
            "No emerging stock currently clears the strict Emerging Buy List. "
            "That is intentional. The screen does not force a buy candidate."
        )
    else:
        buy_cols = [
            "Symbol", "Company", "Close", "Emerging Score", "Setup",
            "Technical Score", "Fundamental Score", "Fundamental Coverage",
            "RS3MPct", "VolumeRatio", "LiquidityBucket", "Revenue Growth %",
            "Profit Margin %", "Debt/Equity", "P/E", "EV/EBITDA", "ROE %",
        ]
        buy_cols = [c for c in buy_cols if c in buy.columns]
        st.dataframe(
            buy[buy_cols],
            use_container_width=True,
            hide_index=True,
            height=360,
            column_config={
                "Close": st.column_config.NumberColumn("Price", format="₹ %.2f"),
                "Emerging Score": st.column_config.NumberColumn("Score", format="%.1f"),
                "Technical Score": st.column_config.NumberColumn("Technical", format="%.1f"),
                "Fundamental Score": st.column_config.NumberColumn("Fundamentals", format="%.1f"),
                "Fundamental Coverage": st.column_config.NumberColumn("Fund. Coverage", format="%d/5"),
                "RS3MPct": st.column_config.NumberColumn("RS 3M %ile", format="%.0f"),
                "VolumeRatio": st.column_config.NumberColumn("Volume x", format="%.2f"),
                "Revenue Growth %": st.column_config.NumberColumn("Revenue Growth", format="%.1f%%"),
                "Profit Margin %": st.column_config.NumberColumn("Margin", format="%.1f%%"),
                "Debt/Equity": st.column_config.NumberColumn("D/E", format="%.2f"),
                "P/E": st.column_config.NumberColumn("P/E", format="%.1f"),
                "EV/EBITDA": st.column_config.NumberColumn("EV/EBITDA", format="%.1f"),
                "ROE %": st.column_config.NumberColumn("ROE %", format="%.1f"),
            },
        )
        st.download_button(
            "EXPORT EMERGING BUY LIST",
            data=buy.to_csv(index=False).encode(),
            file_name="emerging_buy_list.csv",
            mime="text/csv",
        )

    # -----------------------------
    # Chart console. Uses already downloaded indicator history only.
    # -----------------------------
    st.markdown('<div class="section-title">Emerging Chart Console</div>', unsafe_allow_html=True)
    if indicators is not None and not filtered.empty:
        show_chart = st.toggle(
            "SHOW MOVING-AVERAGE CHART",
            value=True,
            key="emerging_chart_toggle_v2",
        )
        if show_chart:
            chart_symbols = filtered["Symbol"].tolist()
            selected = st.selectbox(
                "Select stock",
                chart_symbols,
                key="emerging_chart_stock_v2",
            )
            row = filtered.loc[filtered["Symbol"] == selected].iloc[0]
            frame = indicators.loc[
                indicators["Yahoo Symbol"] == row["Yahoo Symbol"]
            ].copy()
            if not frame.empty:
                overlays = [c for c in ["EMA9", "EMA21", "SMA20", "SMA50"] if c in frame.columns]
                st.caption("Price, 9/21 EMA, 20/50 SMA, 20-day average volume and RSI. Long-term SMA 200 and EMA 255 are intentionally excluded from this screen.")
                st.plotly_chart(
                    market_chart(
                        frame,
                        selected,
                        overlays,
                        rsi_col="RSI14",
                        days=252,
                        cross_columns=[c for c in ["Cross9_21", "Cross20_50"] if c in frame.columns],
                        rsi_lines=[(40, "RSI 40"), (50, "RSI 50"), (70, "RSI 70")],
                    ),
                    use_container_width=True,
                    config={"displaylogo": False, "scrollZoom": True},
                )
            else:
                st.info("No indicator history is available for the selected stock.")

    with st.expander("IMPORTANT: WHAT THIS PAGE DOES NOT MEAN", expanded=False):
        st.markdown(
            """
A high Emerging Score is **not** equivalent to a normal Confluence score.

The Emerging Buy List is intentionally strict, but it remains a **research
shortlist** because these stocks do not yet have the long-term history required
by the main strategy suite. As history builds, the stock can graduate into the
normal scanner and be evaluated by the full Confluence and Final Buy List logic.
"""
        )


