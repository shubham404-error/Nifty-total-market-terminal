import streamlit as st
import pandas as pd
from engine import download_prices, calculate_indicators, add_days_since_cross, investor_quality_gate, load_dvm_scores
from ui.components import get_snapshot, get_convergence, terminal_header, page_intro, guide, card, require_scan, ai_prefilter_note
from ui.charts import market_chart
from state import _invalidate_strategy_state, _ensure_ai_strategy_outputs, _ai_register_strategy_output, _strategy_cache_valid, _current_scan_id
from scoring import build_ai_confluence_pool, build_final_buy_list, _build_emerging_scored, build_emerging_buy_list
from constants import AI_STRATEGY_PREFILTER_SCORE, AI_FUNDAMENTAL_FETCH_LIMIT, AI_SESSION_CALL_LIMIT, AI_DEFAULT_FINAL_BUY_CONVICTION, AI_DEFAULT_FINAL_BUY_LIQUIDITY
from ai_service import _render_list_ai_terminal, _gemini_reply, _ai_consume_call

def nifty_ai_page():
    require_scan()
    terminal_header(
        "Nifty AI Analyst",
        "Ask questions about the current scan, chart, strategy status, and available fundamentals.",
        show_logo=True,
    )
    ai_prefilter_note()

    snapshot = get_snapshot()
    if snapshot is None or snapshot.empty:
        st.warning("RUN A MARKET SCAN")
        return

    if "Symbol" not in snapshot.columns:
        st.error("The current scan does not contain a Symbol column.")
        return

    st.caption(
        "Read-only AI interpretation of the current terminal scan. "
        "The existing engine and scores remain the source of truth."
    )

    symbols = sorted(snapshot["Symbol"].dropna().astype(str).unique().tolist())
    selected = st.selectbox("Select stock", symbols, key="nifty_ai_selected_stock")

    context, frame, chart_png = _ai_stock_context(selected)
    if context is None:
        st.error("Unable to build AI context for the selected stock.")
        return

    left, right = st.columns([1.65, 1])

    with left:
        if frame is not None and not frame.empty:
            st.plotly_chart(
                market_chart(
                    frame,
                    selected,
                    ["EMA9", "EMA21", "SMA20", "SMA50", "SMA200", "EMA255"],
                    rsi_col="RSI14",
                    days=252,
                    cross_columns=[
                        c for c in ["Cross9_21", "Cross20_50", "Cross50_200"]
                        if c in frame.columns
                    ],
                    rsi_lines=[(30, "RSI 30"), (50, "RSI 50"), (70, "RSI 70")],
                ),
                use_container_width=True,
                config={"displaylogo": False, "scrollZoom": True},
            )
        else:
            st.info("No indicator history is available for the selected stock.")

    with right:
        st.subheader("Current terminal snapshot")
        st.caption("Yahoo Finance fundamentals are fetched on demand for questions about valuation, business quality, growth, profitability, debt, cash flow, or longer-term investing.")
        # Streamlit/PyArrow requires a consistent type within each DataFrame column.
        # Terminal snapshot values can legitimately mix strings, ints, floats and bools.
        preview = pd.DataFrame(
            {
                "Metric": [
                    str(key)
                    for key in context["current_terminal_snapshot"].keys()
                ],
                "Value": [
                    "N/A" if pd.isna(value) else str(value)
                    for value in context["current_terminal_snapshot"].values()
                ],
            }
        )
        st.dataframe(preview, use_container_width=True, height=520, hide_index=True)

    strategy_status = context.get("strategy_status", {})
    active_memberships = [
        ("Final Buy List", strategy_status.get("final_buy_list", {})),
        ("Emerging Buy List", strategy_status.get("emerging_buy_list", {})),
        ("Confluence", strategy_status.get("confluence", {})),
        ("Emerging Setups", strategy_status.get("emerging_setups", {})),
    ]
    active_memberships = [
        (name, item) for name, item in active_memberships
        if item.get("member") and item.get("verified")
    ]
    if active_memberships:
        labels = "  •  ".join(name for name, _ in active_memberships)
        st.success(f"Current verified strategy membership: {labels}")

    if IS_BETA:
        st.divider()
        render_trendlyne_widgets(selected)

    chat_key = f"nifty_ai_chat::{selected}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    st.divider()
    st.subheader(f"Chat about {selected}")

    quick_prompts = [
        ("Why is it here?", "Tell me exactly which current list or strategy this stock belongs to and explain in simple language why it qualified."),
        ("What does it mean?", "Explain what the current result means for a retail investor. Keep it simple and avoid technical jargon."),
        ("Biggest risk", "What is the biggest reason to be careful with this stock right now? Explain simply."),
        ("What next?", "What should a retail investor monitor next before becoming more confident about this setup?"),
    ]

    selected_quick = None
    cols = st.columns(4)
    for col, (label, prompt) in zip(cols, quick_prompts):
        with col:
            if st.button(label, key=f"ai_quick::{selected}::{label}", use_container_width=True):
                selected_quick = prompt

    for message in st.session_state[chat_key]:
        with st.chat_message(
            message["role"],
            avatar=_ai_avatar_source() if message["role"] == "assistant" else None,
        ):
            display, action = _split_ai_action(message["content"])
            if action:
                _render_ai_action(action)
            st.markdown(display)

    typed_prompt = st.chat_input(f"Ask Nifty AI about {selected}...")
    prompt = selected_quick or typed_prompt

    if prompt:
        st.session_state[chat_key].append({"role": "user", "content": prompt})
        st.session_state[chat_key] = st.session_state[chat_key][-20:]
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar=_ai_avatar_source()):
            with st.spinner("Analysing current terminal data..."):
                try:
                    answer = _gemini_reply(
                        prompt,
                        context,
                        chart_png,
                        st.session_state[chat_key][:-1],
                    )
                    display, action = _split_ai_action(answer)
                    if action:
                        _render_ai_action(action)
                    st.markdown(display)
                    st.session_state[chat_key].append(
                        {"role": "assistant", "content": answer}
                    )
                    st.session_state[chat_key] = st.session_state[chat_key][-20:]
                except Exception as exc:
                    st.error(f"AI request failed: {exc}")

    remaining = AI_SESSION_CALL_LIMIT - int(st.session_state.get("ai_call_count", 0))
    st.caption(
        f"Model: {GEMINI_MODEL}. Every AI response now ends with an explicit action classification. "
        f"Technical chart context is included by default, while Yahoo Finance fundamentals are fetched when relevant. "
        f"Strategy verification uses the {AI_STRATEGY_PREFILTER_SCORE}+ high-conviction candidate pool and does not alter the terminal's visible strategy rules. "
        f"AI session calls remaining: {max(0, remaining)}."
    )


