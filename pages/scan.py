import streamlit as st
import pandas as pd
from engine import download_prices, calculate_indicators, add_days_since_cross, investor_quality_gate, load_dvm_scores
from ui.components import get_snapshot, get_convergence, terminal_header, page_intro, guide, card, require_scan, ai_prefilter_note
from ui.charts import market_chart
from state import _invalidate_strategy_state, _ensure_ai_strategy_outputs, _ai_register_strategy_output, _strategy_cache_valid, _current_scan_id
from scoring import build_ai_confluence_pool, build_final_buy_list, _build_emerging_scored, build_emerging_buy_list
from ai_service import _render_list_ai_terminal, _gemini_reply, _ai_consume_call

def scan_page():
    terminal_header(
        "Scan Engine",
        "Run one shared scan and reuse it everywhere else",
    )

    page_intro(
        "Scan the market once.",
        "Choose your universe and history. The scanner downloads daily market data "
        "and calculates the indicators used by every strategy. You do not need to "
        "repeat the download for each page.",
    )

    guide(
        "Recommended setup",
        "For normal use, keep the defaults. A 4-year history gives enough context "
        "for the long moving averages while keeping the scan practical on free hosting.",
        [
            "Select Nifty Total Market for the broadest current universe.",
            "Keep 4 years of history.",
            "Click Run Market Scan and wait for the data-quality result.",
        ],
    )

    c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])

    with c1:
        universe_name = st.selectbox(
            "Stock universe",
            ["NIFTY TOTAL MARKET", "NIFTY 500", "NIFTY 200", "NIFTY 50"],
            index=0,
            help="Nifty 50: focused large-cap. Nifty 200: large + mid-cap. Nifty 500: broad. Nifty Total Market: broadest.",
        )

    with c2:
        history_years = st.selectbox(
            "Price history",
            [3, 4, 5],
            index=1,
        )

    with c3:
        batch_size = st.select_slider(
            "Download chunk",
            options=[50, 75, 100],
            value=75,
            help="Smaller chunks can be more resilient to public-data limits.",
        )

    with c4:
        run_scan = st.button(
            "RUN MARKET SCAN",
            type="primary",
            use_container_width=True,
        )

    if run_scan:
        try:
            with st.spinner("Loading the current stock universe..."):
                universe = load_universe(universe_name)

            progress = st.progress(0)
            status = st.empty()

            def update(batch, total, failures):
                progress.progress(batch / total)
                status.write(
                    f"Downloading market data: {batch}/{total} · "
                    f"unresolved symbols: {failures}"
                )

            if IS_BETA:
                st.info("BETA MODE: Loading offline data (Zero Live Compute)")
                import os
                if os.path.exists("cache.parquet"):
                    prices = pd.read_parquet("cache.parquet")
                    failures = []
                else:
                    st.error("Offline cache.parquet not found. Run build_cache.py")
                    st.stop()
            else:
                prices, failures = download_prices(
                    universe,
                    years=history_years,
                    batch_size=batch_size,
                    _progress_callback=update,
                )

            if prices.empty:
                st.error("No usable market data was returned.")
                st.stop()

            status.write("Calculating indicators...")
            indicators = calculate_indicators(prices)
            snapshot = latest_snapshot(indicators, universe)
            snapshot = add_days_since_cross(indicators, snapshot)
            convergence = convergence_table(snapshot, version="v1")
            convergence_v2 = convergence_table(snapshot, version="v2")
            
            if IS_BETA:
                dvm = load_dvm_scores()
                if not dvm.empty:
                    snapshot = snapshot.merge(dvm, on="Yahoo Symbol", how="left")
                    convergence = convergence.merge(dvm, on="Yahoo Symbol", how="left")
                    convergence_v2 = convergence_v2.merge(dvm, on="Yahoo Symbol", how="left")
                    
                    mask = (snapshot["valuation_confidence"] == "Low") | (snapshot["durability_confidence"] == "Low")
                    snapshot.loc[mask, "Symbol"] = "⚠️ " + snapshot.loc[mask, "Symbol"].astype(str)
            
            st.session_state["universe"] = universe
            st.session_state["prices"] = prices
            st.session_state["indicators"] = indicators
            st.session_state["snapshot"] = snapshot
            st.session_state["convergence"] = convergence
            st.session_state["convergence_v2"] = convergence_v2
            st.session_state["failures"] = failures
            st.session_state["scan_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            scan_basis = snapshot[[c for c in ["Symbol", "Date", "Close"] if c in snapshot.columns]].copy()
            scan_id = "scan-" + hashlib.sha256(scan_basis.to_csv(index=False).encode()).hexdigest()[:16]
            _invalidate_strategy_state(scan_id)
            st.session_state["scan_id"] = scan_id

            progress.empty()
            status.empty()

            st.success(
                f"Scan complete. {len(snapshot):,} stocks have usable daily history."
            )

        except Exception as exc:
            st.error(
                "The market scan could not be completed. "
                "Try again or reduce the download chunk."
            )
            with st.expander("Technical details"):
                st.exception(exc)

    if "snapshot" in st.session_state:
        snapshot = get_snapshot()
        failures = st.session_state.get("failures", [])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Universe", f"{len(st.session_state['universe']):,}")
        c2.metric("Usable price histories", f"{len(snapshot):,}")
        c3.metric("Bullish long-term trend", f"{int(snapshot['BullRegime'].sum()):,}")
        c4.metric("Oversold pullbacks", f"{int(snapshot['Pullback'].sum()):,}")

        st.markdown('<div class="section-title">Data quality</div>', unsafe_allow_html=True)

        q1, q2, q3 = st.columns(3)
        q1.metric(
            "Coverage",
            f"{len(snapshot) / max(len(st.session_state['universe']), 1) * 100:.1f}%",
        )
        q2.metric(
            "Latest market date",
            pd.to_datetime(snapshot["Date"]).max().strftime("%d %b %Y"),
        )
        q3.metric("Unresolved symbols", f"{len(failures):,}")

        if failures:
            st.warning(
                f"{len(failures)} symbols did not return usable history and were excluded."
            )

        st.download_button(
            "EXPORT MARKET SNAPSHOT",
            data=snapshot.to_csv(index=False).encode(),
            file_name="nifty_market_snapshot.csv",
            mime="text/csv",
        )

        guide(
            "You're ready",
            "Your market scan is complete. If some stocks have insufficient history for the full strategy suite, review them in Emerging Setups below."
        )

        st.markdown(
            "[**→ OPEN EMERGING SETUPS**](/emerging-setups)",
            unsafe_allow_html=True,
        )


