from __future__ import annotations

import streamlit as st
from pathlib import Path
from styles import inject_styles
from ui.components import render_sidebar_brand, render_terminal_footer
from pages.home import home_page
from pages.scan import scan_page
from pages.emerging import emerging_setups_page
from pages.strategies import pullback_page
from pages.ai_analyst import nifty_ai_page
from pages.confluence import convergence_page
from pages.buying_list import buying_list_page
from pages.market_structure import market_structure_page
from pages.candlesticks import candlesticks_page
from pages.rs_and_stage import rs_and_stage_page
from pages.signal_ledger import signal_ledger_page

# Paths for setup
APP_FAVICON_PATH = Path("assets/nifty_favicon.png")
IS_BETA = st.query_params.get('beta') == 'true'

st.set_page_config(
    page_title="Nifty Market Terminal",
    page_icon=str(APP_FAVICON_PATH) if APP_FAVICON_PATH.is_file() else "📈",
    layout="wide",
    initial_sidebar_state="auto",
)

inject_styles()

pages = {
    "MARKET": [
        st.Page(
            home_page,
            title="User Guide",
            icon="📖",
            url_path="home",
            default=True,
        ),
        st.Page(
            scan_page,
            title="Scan Engine",
            icon="📡",
            url_path="scan-engine",
        ),
        st.Page(
            market_structure_page,
            title="Market Structure",
            icon="📊",
            url_path="market-structure"
        ),
    ],
    "SIGNALS": [
        st.Page(
            candlesticks_page,
            title="Candlestick Scanner",
            icon="🕯️",
            url_path="candlesticks",
        ),
        st.Page(
            rs_and_stage_page,
            title="RS & Stage",
            icon="🚀",
            url_path="rs-and-stage",
        ),
        st.Page(
            pullback_page,
            title="EMA 255 Pullback",
            icon="🧲",
            url_path="ema-255-pullback",
        ),
    ],
    "ANALYSIS": [
        st.Page(
            convergence_page,
            title="Confluence Builder",
            icon="🧪",
            url_path="confluence",
        ),
        st.Page(
            nifty_ai_page,
            title="Nifty AI Analyst",
            icon="🤖",
            url_path="nifty-ai",
        ),
    ],
    "TRACKING": [
        st.Page(
            buying_list_page,
            title="Final Buy List",
            icon="🛒",
            url_path="final-buy-list",
        ),
        st.Page(
            signal_ledger_page,
            title="Signal Ledger",
            icon="📓",
            url_path="signal-ledger"
        ),
    ],
}

with st.sidebar:
    render_sidebar_brand()
    st.divider()

pg = st.navigation(
    pages,
    position="sidebar",
)

with st.sidebar:
    st.markdown(
        """
<div class="section-kicker">Quick start</div>
<div class="small-note">
<b>1.</b> Run Scan Engine<br>
<b>2.</b> Explore a setup<br>
<b>3.</b> Check the chart<br>
<b>4.</b> Open Confluence<br>
<b>5.</b> Open Final Buy List<br>
<b>6.</b> Ask Nifty AI Analyst why a shortlisted stock qualified<br>
<b>Optional.</b> Check Emerging Setups for newer stocks
</div>
""",
        unsafe_allow_html=True,
    )

    if "snapshot" in st.session_state:
        st.success("SCAN READY")
    else:
        st.warning("RUN A MARKET SCAN")

    st.divider()
    
    st.toggle(
        "Global Liquidity Filter", 
        value=False, 
        key="global_liquidity_filter", 
        help="Filter entire app to only show stocks with ₹1Cr+ 20-day average traded value."
    )
    
    st.toggle(
        "Use Confluence v2", 
        value=True, 
        key="use_confluence_v2", 
        help="Use version 2 of the confluence scoring engine."
    )
    
    st.divider()

    st.caption(
        "Built for research. Public market data. "
        "No broker API key required."
    )

pg.run()

render_terminal_footer()
