import streamlit as st
import pandas as pd
import json
import re
from google import genai
from google.genai import types
from engine import fundamental_snapshot
from state import _ai_registered_strategy_frame
from ui.charts import _ai_chart_png

GEMINI_MODEL = 'gemini-3.5-flash-lite'
AI_SESSION_CALL_LIMIT = 25
AI_FUNDAMENTAL_FETCH_LIMIT = 25
AI_LIST_REVIEW_LIMIT = 20
AI_ACTIONS = ('STRONG BUY', 'BUY', 'ACCUMULATE', 'HOLD / MONITOR', 'WAIT FOR PULLBACK', 'WAIT FOR BREAKOUT', 'AVOID FOR NOW', 'SELL / EXIT')

def _ai_json_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp, datetime)):
        return str(value)
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def _ai_find_row(frame, symbol):
    if frame is None or not isinstance(frame, pd.DataFrame) or frame.empty:
        return None
    if "Symbol" not in frame.columns:
        return None
    rows = frame.loc[frame["Symbol"].astype(str) == str(symbol)]
    return rows.iloc[0] if not rows.empty else None


def _ai_strategy_status(symbol, snapshot_row):
    """Exact membership from the current scan. Never inferred by Gemini or navigation order."""
    _ensure_ai_strategy_outputs()
    status = {
        "confluence": {"member": False, "verified": False, "reason": None, "details": {}},
        "final_buy_list": {"member": False, "verified": False, "reason": None, "details": {}},
        "emerging_setups": {"member": False, "verified": False, "reason": None, "details": {}},
        "emerging_buy_list": {"member": False, "verified": False, "reason": None, "details": {}},
    }

    # Confluence. Prefer the exact filtered output currently shown in the app.
    confluence_frame, confluence_meta = _ai_registered_strategy_frame(
        "confluence",
        "ai_confluence_output",
    )
    row = _ai_find_row(confluence_frame, symbol)
    if row is not None:
        setup = str(row.get("Setup", "Active setup"))
        score = pd.to_numeric(row.get("ConvergenceScore"), errors="coerce")
        status["confluence"] = {
            "member": True,
            "verified": True,
            "reason": (
                f"Currently in the Confluence output. Setup: {setup}. "
                f"Confluence score: {float(score):.1f}."
            ),
            "details": {
                "setup": setup,
                "confluence_score": _ai_json_value(score),
                "minimum_score_used": confluence_meta.get("minimum_score"),
                "trend_score": _ai_json_value(row.get("TrendContinuationScore")),
                "pullback_score": _ai_json_value(row.get("PullbackScore")),
                "fresh_momentum_score": _ai_json_value(row.get("FreshMomentumScore")),
                "breakout_score": _ai_json_value(row.get("BreakoutScore")),
            },
        }

    # Final Buy List. This is the exact table, including rank and live threshold.
    final_frame, final_meta = _ai_registered_strategy_frame(
        "final_buy_list",
        "ai_final_buy_output",
    )
    row = _ai_find_row(final_frame, symbol)
    if row is not None:
        setup = str(row.get("Setup", "Current setup"))
        conviction = _ai_json_value(row.get("Investor Conviction"))
        technical_quality = _ai_json_value(row.get("Technical Quality"))
        confluence_score = _ai_json_value(row.get("Confluence"))
        rs3 = _ai_json_value(row.get("RS 3M %ile"))
        volume = _ai_json_value(row.get("Volume x"))
        liquidity = _ai_json_value(row.get("Liquidity"))

        reason_parts = [
            "Currently in the Final Buy List",
            f"Rank {row.get('Rank')}" if pd.notna(row.get("Rank")) else None,
            f"Setup: {setup}",
            f"Investor Conviction: {conviction}" if conviction is not None else None,
            f"Technical Quality: {technical_quality}" if technical_quality is not None else None,
            f"Confluence: {confluence_score}" if confluence_score is not None else None,
        ]
        reason = ". ".join(str(x) for x in reason_parts if x) + "."

        status["final_buy_list"] = {
            "member": True,
            "verified": True,
            "reason": reason,
            "details": {
                "rank": _ai_json_value(row.get("Rank")),
                "setup": setup,
                "investor_conviction": conviction,
                "technical_quality": technical_quality,
                "confluence": confluence_score,
                "rs_3m_percentile": rs3,
                "rs_6m_percentile": _ai_json_value(row.get("RS 6M %ile")),
                "volume_multiple": volume,
                "liquidity": liquidity,
                "minimum_investor_conviction_used": final_meta.get(
                    "minimum_investor_conviction"
                ),
                "liquidity_filter_used": final_meta.get("use_liquidity_filter"),
            },
        }

    # Emerging Setups.
    emerging_frame, _ = _ai_registered_strategy_frame(
        "emerging_setups",
        "ai_emerging_working",
    )
    row = _ai_find_row(emerging_frame, symbol)
    if row is not None:
        status["emerging_setups"] = {
            "member": True,
            "verified": True,
            "reason": (
                f"Currently in Emerging Setups. Setup: {row.get('Setup')}. "
                f"Emerging Score: {row.get('Emerging Score')}."
            ),
            "details": {
                "setup": _ai_json_value(row.get("Setup")),
                "emerging_score": _ai_json_value(row.get("Emerging Score")),
                "technical_score": _ai_json_value(row.get("Technical Score")),
                "fundamental_score": _ai_json_value(row.get("Fundamental Score")),
                "rs_3m_percentile": _ai_json_value(row.get("RS3MPct")),
                "fundamental_coverage": _ai_json_value(row.get("Fundamental Coverage")),
            },
        }

    # Emerging Buy List.
    emerging_buy_frame, _ = _ai_registered_strategy_frame(
        "emerging_buy_list",
        "ai_emerging_buy_output",
    )
    row = _ai_find_row(emerging_buy_frame, symbol)
    if row is not None:
        status["emerging_buy_list"] = {
            "member": True,
            "verified": True,
            "reason": (
                f"Currently in the Emerging Buy List. "
                f"Emerging Score: {row.get('Emerging Score')}."
            ),
            "details": {
                "setup": _ai_json_value(row.get("Setup")),
                "emerging_score": _ai_json_value(row.get("Emerging Score")),
                "technical_score": _ai_json_value(row.get("Technical Score")),
                "fundamental_score": _ai_json_value(row.get("Fundamental Score")),
                "fundamental_coverage": _ai_json_value(row.get("Fundamental Coverage")),
            },
        }

    return status


def _ai_stock_context(symbol):
    snapshot = get_snapshot()
    indicators = st.session_state.get("indicators")

    if snapshot is None or snapshot.empty:
        return None, None, None

    rows = snapshot.loc[snapshot["Symbol"].astype(str) == str(symbol)]
    if rows.empty:
        return None, None, None

    row = rows.iloc[0]
    row_data = {str(col): _ai_json_value(row[col]) for col in snapshot.columns}

    yahoo_symbol = row_data.get("Yahoo Symbol")
    history = None
    if indicators is not None and not indicators.empty and "Yahoo Symbol" in indicators.columns:
        history = indicators.loc[
            indicators["Yahoo Symbol"].astype(str) == str(yahoo_symbol)
        ].copy()

    strategy_status = _ai_strategy_status(symbol, row)

    context = {
        "symbol": str(symbol),
        "yahoo_symbol": str(yahoo_symbol) if yahoo_symbol else None,
        "data_date": str(row_data.get("Date", "")),
        "current_terminal_snapshot": row_data,
        "strategy_status": strategy_status,
        "rules": {
            "scores_are_engine_output": True,
            "ai_must_not_recalculate_or_change_scores": True,
            "missing_data_must_be_called_missing": True,
            "strategy_membership_must_come_from_strategy_status": True,
            "ai_must_not_generate_fundamentals_outside_scorecard": True,
            "ai_must_not_see_trendlyne_widgets": True,
        },
    }

    return context, history, _ai_chart_png(history, symbol)


def _ai_compact_context(context):
    """Fixed-size factual packet. Interpretation is left to Gemini."""
    snapshot = context.get("current_terminal_snapshot", {})
    preferred = [
        "Symbol", "Company", "Date", "Close", "Price", "Last Price",
        "RSI14", "EMA9", "EMA21", "SMA20", "SMA50", "SMA200", "EMA255",
        "RS3MPct", "RS6MPct", "VolumeRatio", "Volume", "AvgVolume",
        "AvgTradedValue20", "LiquidityBucket", "ATRPercent",
        "DataQualityStatus", "Fundamental Coverage",
        "BullMomentum", "BullSwing", "Breakout20", "VolumeConfirmedMomentum",
    ]
    lower_lookup = {str(k).lower(): k for k in snapshot.keys()}
    compact = {}
    for wanted in preferred:
        actual = lower_lookup.get(wanted.lower())
        if actual is not None:
            compact[str(actual)] = snapshot[actual]

    return {
        "symbol": context.get("symbol"),
        "data_date": context.get("data_date"),
        "strategy_status": context.get("strategy_status", {}),
        "technical_snapshot": compact,
    }


def _ai_question_needs_fundamentals(question):
    q = str(question).lower()
    terms = [
        "fundamental", "valuation", "value", "expensive", "cheap", "overvalued",
        "undervalued", "company", "business", "revenue", "sales", "earnings",
        "profit", "margin", "debt", "balance sheet", "cash flow", "roe", "roa",
        "financial", "long term", "1 year", "2 year", "3 year", "investment",
        "hold", "quality company", "growth"
    ]
    return any(term in q for term in terms)


def _ai_question_is_clearly_fundamental_only(question):
    q = str(question).lower()
    fundamental = _ai_question_needs_fundamentals(q)
    technical_terms = [
        "entry", "buy now", "technical", "chart", "setup", "rsi", "ema", "sma",
        "support", "resistance", "breakout", "trend", "price action", "pullback",
        "momentum", "extended", "volume", "stop loss"
    ]
    return fundamental and not any(term in q for term in technical_terms)


def _ai_fetch_fundamental_packet(context):
    """Fetch and cache a richer Yahoo Finance packet for AI research questions."""
    ticker = context.get("yahoo_symbol")
    if not ticker:
        return {"available": False, "reason": "Yahoo Finance symbol is unavailable."}

    scan_id = _current_scan_id() or "no-scan"
    cache = st.session_state.setdefault("ai_fundamental_cache", {})
    cache_key = f"{scan_id}::{ticker}"
    if cache_key in cache:
        return cache[cache_key]

    fields = {
        "company": ["longName", "shortName", "sector", "industry"],
        "valuation": ["marketCap", "trailingPE", "forwardPE", "priceToBook", "enterpriseToEbitda"],
        "growth": ["revenueGrowth", "earningsGrowth", "earningsQuarterlyGrowth"],
        "profitability": ["profitMargins", "operatingMargins", "returnOnEquity", "returnOnAssets"],
        "balance_sheet": ["totalCash", "totalDebt", "debtToEquity", "currentRatio", "quickRatio"],
        "cash_flow": ["operatingCashflow", "freeCashflow"],
        "share_statistics": ["sharesOutstanding", "floatShares", "heldPercentInsiders", "heldPercentInstitutions"],
    }
    pct_fields = {"revenueGrowth", "earningsGrowth", "earningsQuarterlyGrowth", "profitMargins", "operatingMargins", "returnOnEquity", "returnOnAssets", "heldPercentInsiders", "heldPercentInstitutions"}
    try:
        info = yf.Ticker(ticker).info or {}
        packet = {"available": bool(info), "source": "Yahoo Finance", "ticker": ticker}
        for section, names in fields.items():
            values = {}
            for name in names:
                value = info.get(name)
                if value is not None:
                    if name in pct_fields and isinstance(value, (int, float)):
                        value = value * 100
                    values[name] = _ai_json_value(value)
            packet[section] = values
        if not info:
            packet["reason"] = "Yahoo Finance returned no usable fundamental snapshot."
    except Exception as exc:
        packet = {"available": False, "source": "Yahoo Finance", "ticker": ticker, "reason": str(exc)[:180]}

    cache[cache_key] = packet
    return packet


def _ai_question_needs_chart(question):
    """Default to chart context. Skip only for clearly fundamental-only questions."""
    return not _ai_question_is_clearly_fundamental_only(question)


def _ai_consume_call():
    """Hard per-session guard for the free-tier AI integration."""
    count = int(st.session_state.get("ai_call_count", 0))
    if count >= AI_SESSION_CALL_LIMIT:
        raise RuntimeError(
            f"AI session limit reached ({AI_SESSION_CALL_LIMIT} calls). "
            "Start a new session or try again later."
        )
    st.session_state["ai_call_count"] = count + 1
    return AI_SESSION_CALL_LIMIT - count - 1


def _extract_ai_action(answer):
    """Read the model's explicit final action without inventing one."""
    if not isinstance(answer, str):
        return None
    upper = answer.upper()
    for action in AI_ACTIONS:
        pattern = rf'(?:FINAL[_\s-]*ACTION|AI[_\s-]*ACTION|ACTION)\s*:\s*{re.escape(action)}\b'
        if re.search(pattern, upper):
            return action
    return None


def _split_ai_action(answer):
    """Return display text and the explicit model action separately."""
    action = _extract_ai_action(answer)
    if not action:
        return answer, None
    cleaned = re.sub(
        r'\n*(?:FINAL[_\s-]*ACTION|AI[_\s-]*ACTION|ACTION)\s*:\s*'
        + re.escape(action)
        + r'\s*',
        '\n',
        answer,
        flags=re.IGNORECASE,
    ).strip()
    return cleaned, action


def _render_ai_action(action):
    if not action:
        return
    label = f"AI FINAL ACTION: {action}"
    if action in {"STRONG BUY", "BUY", "ACCUMULATE"}:
        st.success(label)
    elif action in {"WAIT FOR PULLBACK", "WAIT FOR BREAKOUT", "HOLD / MONITOR"}:
        st.warning(label)
    else:
        st.error(label)


def _list_ai_packet(frame, list_name):
    """Compact, bounded candidate packet for a single AI ranking call."""
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return []

    work = frame.copy()
    if "Rank" not in work.columns:
        work = work.reset_index(drop=True)
        work.insert(0, "Rank", range(1, len(work) + 1))

    preferred = [
        "Rank", "Symbol", "Company", "Setup", "Close",
        "ConvergenceScore", "Confluence", "Investor Conviction",
        "Technical Quality", "RS 3M %ile", "RS 6M %ile",
        "RS3MPct", "RS6MPct", "Volume x", "VolumeRatio",
        "Liquidity", "LiquidityBucket", "RSI", "RSI14",
        "ATR %", "ATRPercent", "Gap %", "GapPct",
        "TrendContinuationScore", "PullbackScore",
        "FreshMomentumScore", "BreakoutScore",
        "P/E", "Revenue Growth %", "Net Profit Margin %",
        "Debt/Equity", "EV/EBITDA", "ROE %", "Market Cap",
    ]
    cols = [c for c in preferred if c in work.columns]
    work = work.loc[:, cols].head(AI_LIST_REVIEW_LIMIT)

    records = []
    for _, row in work.iterrows():
        record = {}
        for col, value in row.items():
            converted = _ai_json_value(value)
            if converted is not None:
                record[col] = converted
        records.append(record)
    return records


def _gemini_list_reply(question, frame, list_name, history):
    """AI second-stage review of candidates already selected by deterministic rules."""
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it in Streamlit Secrets.")

    candidates = _list_ai_packet(frame, list_name)
    if not candidates:
        raise RuntimeError(f"No usable candidates are available for AI review in {list_name}.")

    _ai_consume_call()

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=30000),
    )

    instruction = f"""
You are the second-stage investment research analyst for Nifty Market Terminal.

The deterministic scanner has already placed these stocks in the {list_name}.
Your job is NOT to repeat the scanner or assume every listed stock deserves an immediate buy.

Act as a disciplined investment committee:
1. Compare candidates against each other.
2. Penalize poor entry timing, excessive extension, weak risk/reward, deteriorating momentum,
   low-quality confirmation, contradictory metrics, and material data gaps.
3. Distinguish a strong setup from a strong setup at a bad entry price.
4. Do not invent news, earnings, targets, support levels, or facts not present in the packet.
5. Fundamentals are only available when included in the supplied candidate data.
6. Never remove a stock from the application's rules-based list. You are adding a second opinion.

For every candidate you discuss, assign exactly one action from:
{", ".join(AI_ACTIONS)}

When asked for the best opportunities, rank at most {AI_LIST_TOP_N} names.
A Top 3 ranking means "best risk-adjusted setups from this supplied list right now", not a
guarantee and not personalised financial advice.

Use plain English for a retail investor. Be decisive, but explain uncertainty.

End every response with exactly one line in this format when the response has an overall list-level
recommendation:
FINAL_ACTION: <one of the allowed actions>
"""

    payload = {
        "list_name": list_name,
        "candidate_count_shown_to_ai": len(candidates),
        "candidates": candidates,
        "question": question,
        "recent_conversation": [
            {"role": item["role"], "content": item["content"]}
            for item in history[-6:]
        ],
    }

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Part.from_text(text=instruction),
                types.Part.from_text(
                    text="Candidate packet:\n"
                    + json.dumps(payload, default=str, ensure_ascii=False)
                ),
            ],
        )
    except Exception as exc:
        details = str(exc)
        if "429" in details or "quota" in details.lower() or "rate" in details.lower():
            raise RuntimeError("Gemini free-tier quota or rate limit reached. Try again later.") from exc
        raise RuntimeError(f"Gemini list review failed: {details}") from exc

    answer = getattr(response, "text", None)
    if not answer:
        raise RuntimeError("Gemini returned no usable list review.")
    return answer


def _render_list_ai_terminal(list_name, frame, key_prefix):
    """Reusable AI research terminal with chat and single-answer modes."""
    st.divider()
    st.subheader(f"AI Investment Committee. {list_name}")

    if not isinstance(frame, pd.DataFrame) or frame.empty:
        st.info("No candidates are available for AI review.")
        return

    shown = min(len(frame), AI_LIST_REVIEW_LIMIT)
    st.caption(
        f"AI reviews the top {shown} candidates currently visible on this list. "
        "The rules-based list remains unchanged. AI ranks and deprioritises setups based on "
        "entry timing, confirmation, risk/reward and available fundamentals."
    )

    scan_id = _current_scan_id()
    history_key = f"ai_list_chat::{key_prefix}::{scan_id}"
    latest_key = f"ai_list_latest::{key_prefix}::{scan_id}"
    mode_key = f"{key_prefix}::display_mode"

    if history_key not in st.session_state:
        st.session_state[history_key] = []

    st.radio(
        "AI response view",
        options=["ONE ANSWER AT A TIME", "CHAT WINDOW"],
        key=mode_key,
        horizontal=True,
        label_visibility="collapsed",
    )
    answer_mode = st.session_state[mode_key]

    quick_cols = st.columns([1, 1, 1])
    with quick_cols[0]:
        top3_clicked = st.button(
            "AI TOP 3 NOW",
            key=f"{key_prefix}::top3",
            use_container_width=True,
        )
    with quick_cols[1]:
        risk_clicked = st.button(
            "WEAKEST SIGNALS",
            key=f"{key_prefix}::weak",
            use_container_width=True,
        )
    with quick_cols[2]:
        entry_clicked = st.button(
            "BEST ENTRY CONDITIONS",
            key=f"{key_prefix}::entry",
            use_container_width=True,
        )

    quick_prompt = None
    if top3_clicked:
        quick_prompt = (
            "Rank the best 3 opportunities from this list right now. For each, give the action, "
            "why it ranks here, the biggest risk, and what would make the setup better or invalidate the case. "
            "Also name candidates you would deliberately deprioritise despite the rules-based qualification."
        )
    elif risk_clicked:
        quick_prompt = (
            "Which candidates are the weakest or least attractive right now despite appearing on this list? "
            "Explain exactly what weakens the setup and assign an action to each."
        )
    elif entry_clicked:
        quick_prompt = (
            "Compare the candidates specifically on entry timing. Identify which are actionable now, "
            "which need a pullback, which need a breakout confirmation, and which should simply be monitored."
        )

    if answer_mode == "CHAT WINDOW":
        clear_col, _ = st.columns([1, 4])
        with clear_col:
            if st.button("CLEAR CHAT", key=f"{key_prefix}::clear_chat"):
                st.session_state[history_key] = []
                st.rerun()

        for message in st.session_state[history_key]:
            with st.chat_message(
                message["role"],
                avatar=_ai_avatar_source() if message["role"] == "assistant" else None,
            ):
                display, action = _split_ai_action(message["content"])
                if action:
                    _render_ai_action(action)
                st.markdown(display)

        typed = st.chat_input(
            f"Ask AI to compare the current {list_name} candidates...",
            key=f"{key_prefix}::chat_input",
        )
        prompt = quick_prompt or typed

        if prompt:
            st.session_state[history_key].append({"role": "user", "content": prompt})
            st.session_state[history_key] = st.session_state[history_key][-20:]

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant", avatar=_ai_avatar_source()):
                with st.spinner("AI is comparing the current candidates..."):
                    try:
                        answer = _gemini_list_reply(
                            prompt,
                            frame,
                            list_name,
                            st.session_state[history_key][:-1],
                        )
                        display, action = _split_ai_action(answer)
                        if action:
                            _render_ai_action(action)
                        st.markdown(display)
                        st.session_state[history_key].append(
                            {"role": "assistant", "content": answer}
                        )
                        st.session_state[history_key] = st.session_state[history_key][-20:]
                    except Exception as exc:
                        st.error(f"AI review failed: {exc}")

    else:
        st.caption(
            "Each new request replaces the previous AI result. "
            "Use Chat Window when you want follow-up conversation."
        )

        question_col, send_col, clear_col = st.columns([6, 1.2, 1.2])
        with question_col:
            typed = st.text_input(
                f"Ask about the current {list_name} candidates...",
                key=f"{key_prefix}::single_question",
                placeholder="Example: Which setup has the best risk-reward right now?",
            )
        with send_col:
            send_clicked = st.button(
                "ANALYSE",
                key=f"{key_prefix}::single_send",
                use_container_width=True,
            )
        with clear_col:
            if st.button(
                "CLEAR",
                key=f"{key_prefix}::single_clear",
                use_container_width=True,
            ):
                st.session_state.pop(latest_key, None)
                st.rerun()

        prompt = quick_prompt or (typed.strip() if send_clicked and typed else None)

        if prompt:
            with st.spinner("AI is reviewing the current candidates..."):
                try:
                    # Single-answer mode is intentionally stateless. Each request gets a
                    # fresh review so the visible page stays compact and easy to replace.
                    answer = _gemini_list_reply(
                        prompt,
                        frame,
                        list_name,
                        [],
                    )
                    st.session_state[latest_key] = {
                        "question": prompt,
                        "answer": answer,
                    }
                except Exception as exc:
                    st.error(f"AI review failed: {exc}")

        latest = st.session_state.get(latest_key)
        if latest:
            st.markdown("#### Latest AI Review")
            st.caption(f"Question: {latest['question']}")
            display, action = _split_ai_action(latest["answer"])
            if action:
                _render_ai_action(action)
            st.markdown(display)

    remaining = AI_SESSION_CALL_LIMIT - int(st.session_state.get("ai_call_count", 0))
    st.caption(
        f"AI session calls remaining: {max(0, remaining)}. "
        f"Candidate review is capped at {AI_LIST_REVIEW_LIMIT} names per call."
    )


def _gemini_reply(question, context, chart_png, history):
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it in Streamlit Secrets.")

    _ai_consume_call()

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=30000),
    )

    conversation = [
        {"role": item["role"], "content": item["content"]}
        for item in history[-6:]
    ]

    fundamental_packet = None
    if _ai_question_needs_fundamentals(question):
        fundamental_packet = _ai_fetch_fundamental_packet(context)

    instruction = """
You are Nifty AI, a practical research copilot inside a retail-focused Indian market terminal.

You are given factual terminal data. Treat strategy membership, rank, setup names, and numerical
scores as facts from the application. Do not invent or alter those facts.

Beyond those facts, reason independently. You may discuss the relationship between momentum,
entry timing, valuation, business quality, growth, profitability, leverage, and risk. Do not force
your answer to mechanically repeat the scanner's conclusion.

Important distinction:
- Strategy status answers whether the stock currently qualifies under a terminal strategy.
- Entry timing answers whether the current price appears attractive, extended, or risky.
These can point in different directions without contradiction. Explain that distinction naturally
when it matters instead of treating either one as automatically decisive.

Use the strongest verified strategy membership first when the user asks about qualification:
Final Buy List, Emerging Buy List, Confluence, then Emerging Setups.
Do not guess membership. If a field is missing, unavailable, or unsupported by the supplied data,
say so plainly.

Fundamental data, when supplied, is a Yahoo Finance snapshot. Use it as context, not as a
substitute for audited filings. Avoid pretending a single ratio proves that a company is good or bad.
If fundamentals and technicals tell different stories, explain the disagreement.

Answer for a reasonably informed retail investor:
- Be direct and conversational.
- Prefer plain English.
- Explain jargon briefly when useful.
- Do not dump every available metric.
- Use short sections and bullets only when they improve clarity.
- Do not invent news, events, targets, support levels, or financial figures not present in the data.
- Do not guarantee returns or give personalised financial advice.

Do not blindly apply generic heuristics such as 'RSI above 70 means do not buy'. Interpret the
indicator in the context of the supplied strategy, chart, and other evidence.

Every answer must finish with exactly one explicit final action selected from:
STRONG BUY, BUY, ACCUMULATE, HOLD / MONITOR, WAIT FOR PULLBACK, WAIT FOR BREAKOUT,
AVOID FOR NOW, SELL / EXIT.

The final line must be exactly:
FINAL_ACTION: <one allowed action>

This is an evidence-based action classification for the current supplied data, not a guarantee.
"""

    payload = {
        "question": str(question),
        "research_packet": _ai_compact_context(context),
        "fundamentals": fundamental_packet,
        "recent_conversation": conversation,
    }

    parts = [
        types.Part.from_text(text=instruction),
        types.Part.from_text(
            text="Research packet:\n" + json.dumps(payload, default=str, ensure_ascii=False)
        ),
    ]

    if chart_png and _ai_question_needs_chart(question):
        parts.append(types.Part.from_bytes(data=chart_png, mime_type="image/png"))

    import time
    delay = 2.0
    for attempt in range(3):
        try:
            response = client.models.generate_content(model=GEMINI_MODEL, contents=parts)
            break
        except Exception as exc:
            details = str(exc)
            if "429" in details or "quota" in details.lower() or "rate" in details.lower():
                raise RuntimeError("Gemini free-tier quota or rate limit reached. Try again later.") from exc
            if attempt == 2:
                raise RuntimeError(
                    "Gemini did not respond within 30 seconds or the request was rejected. "
                    f"Details: {details}"
                ) from exc
            time.sleep(delay)
            delay *= 2

    answer = getattr(response, "text", None)
    if not answer:
        raise RuntimeError("Gemini returned no usable text. Try a shorter question.")
    return answer


