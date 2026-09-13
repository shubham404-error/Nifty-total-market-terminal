import streamlit as st
import pandas as pd
from engine import download_prices, calculate_indicators, add_days_since_cross, investor_quality_gate, load_dvm_scores
from ui.components import get_snapshot, get_convergence, terminal_header, page_intro, guide, card, require_scan, ai_prefilter_note
from ui.charts import market_chart
from state import _invalidate_strategy_state, _ensure_ai_strategy_outputs, _ai_register_strategy_output, _strategy_cache_valid, _current_scan_id
from scoring import build_ai_confluence_pool, build_final_buy_list, _build_emerging_scored, build_emerging_buy_list
from constants import AI_STRATEGY_PREFILTER_SCORE, AI_FUNDAMENTAL_FETCH_LIMIT, AI_SESSION_CALL_LIMIT, AI_DEFAULT_FINAL_BUY_CONVICTION, AI_DEFAULT_FINAL_BUY_LIQUIDITY
from ai_service import _render_list_ai_terminal, _gemini_reply, _ai_consume_call

def buying_list_page():
    require_scan()

    df = get_convergence().copy()

    terminal_header(
        "Final Buy List",
        "Strict retail-investor quality filter applied after Confluence. "
        "This is a research shortlist, not an automated buy recommendation.",
    )

    with st.expander("WHAT DO THE FINAL BUY LIST COLUMNS MEAN?", expanded=False):
        st.markdown("**Investor Conviction** combines final technical and fundamental quality checks. **Technical Quality** is the stricter second-stage screen. **Confluence** is the qualifying setup score. **RS**, **Volume x**, **Liquidity** and **ATR %** provide trend, participation, tradability and volatility context. **P/E, Revenue Growth, Net Profit Margin, Debt/Equity, EV/EBITDA and Market Cap** are research context and sanity checks, not automatic buy signals.")

    guide(
        "How this list is different",
        "Confluence finds valid technical setups. This page is deliberately stricter. "
        "It keeps only candidates with strong relative strength, setup-specific confirmation, "
        "controlled risk and usable liquidity.",
        [
            "Start with the strict technical quality gate.",
            "Keep the recommended liquidity filter on for practical retail execution.",
            "Fundamentals are fetched only for the strongest technical finalists.",
            "Use the final list for research and chart review, not blind execution.",
        ],
    )

    min_score = st.slider(
        "Minimum Investor Conviction Score",
        65,
        95,
        78,
        1,
        key="buy_conviction_score",
    )

    use_liquidity = st.toggle(
        "Use liquidity filter (recommended)",
        value=True,
        key="buy_liquidity_filter",
        help="Optional. Uses the existing 20-day average traded-value threshold.",
    )

    with st.spinner("Building the Final Buy List from the current scan..."):
        final = build_final_buy_list(
            df,
            min_score=min_score,
            use_liquidity=use_liquidity,
            prefilter_score=None,
        )

    if final.empty:
        st.info(
            "No technically and fundamentally strong candidates cleared the current Final Buy List rules."
        )
        return

    technical = investor_quality_gate(df)
    if use_liquidity and not technical.empty:
        technical = technical.loc[technical["LiquidityEligible"].fillna(False)].copy()
    fundamental_fetch_limit = AI_FUNDAMENTAL_FETCH_LIMIT

    st.session_state["ai_final_buy_output"] = final.copy()
    _ai_register_strategy_output(
        "final_buy_list",
        final,
        {
            "minimum_investor_conviction": float(min_score),
            "use_liquidity_filter": bool(use_liquidity),
            "scan_id": _current_scan_id(),
            "canonical_ai_pool": False,
        },
    )

    for col in [
        "P/E",
        "Revenue Growth %",
        "Net Profit Margin %",
        "Debt/Equity",
        "EV/EBITDA", "ROE %",
    ]:
        final[col] = pd.to_numeric(
            final[col],
            errors="coerce",
        ).round(2)

    st.metric(
        "FINAL RESEARCH CANDIDATES",
        f"{len(final):,}",
    )

    if len(technical) > fundamental_fetch_limit:
        st.caption(
            f"{len(technical)} technical candidates passed the quality gate. "
            f"Fundamentals were fetched only for the top {fundamental_fetch_limit} "
            "technical finalists to limit public-data requests."
        )

    display_cols = [
        "Rank",
        "Symbol",
        "Company",
        "Setup",
        "Investor Conviction",
        "Technical Quality",
        "Confluence",
        "RS 3M %ile",
        "RS 6M %ile",
        "Volume x",
        "Liquidity",
        "RSI",
        "ATR %",
        "P/E",
        "Revenue Growth %",
        "Net Profit Margin %",
        "Debt/Equity",
        "EV/EBITDA", "ROE %",
        "Market Cap",
    ]

    display_cols = [
        col for col in display_cols
        if col in final.columns
    ]

    st.dataframe(
        final[display_cols],
        use_container_width=True,
        hide_index=True,
        height=560,
    )

    export = final.drop(
        columns=["Yahoo Symbol"],
        errors="ignore",
    )

    st.download_button(
        "EXPORT FINAL BUY LIST",
        data=export.to_csv(index=False).encode(),
        file_name="nifty_total_market_buying_list.csv",
        mime="text/csv",
    )

    _render_list_ai_terminal(
        "Final Buy List",
        final,
        "final_buy_ai_terminal",
    )

    st.divider()

    if st.toggle(
        "SHOW CHART FOR BUY LIST STOCK",
        value=False,
        key="buy_chart_toggle",
    ):
        selected = st.selectbox(
            "Stock",
            final["Symbol"].tolist(),
            key="buy_chart_stock",
        )
        row = final.loc[
            final["Symbol"] == selected
        ].iloc[0]

        frame = st.session_state["indicators"].loc[
            st.session_state["indicators"]["Yahoo Symbol"]
            == row["Yahoo Symbol"]
        ].copy()

        st.plotly_chart(
            market_chart(
                frame,
                selected,
                [
                    "EMA9",
                    "EMA21",
                    "SMA20",
                    "SMA50",
                    "SMA200",
                    "EMA255",
                ],
                rsi_col="RSI14",
                days=252,
                cross_columns=[
                    "Cross9_21",
                    "Cross20_50",
                    "Cross50_200",
                ],
                rsi_lines=[
                    (30, "RSI 30"),
                    (35, "BUY ZONE 35"),
                    (50, "RSI 50"),
                    (70, "RSI 70"),
                ],
            ),
            use_container_width=True,
            config={
                "displaylogo": False,
                "scrollZoom": True,
            },
        )


