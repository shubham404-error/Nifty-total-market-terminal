import streamlit as st
import pandas as pd
import base64
from pathlib import Path
from state import _current_scan_id
from engine import latest_snapshot, convergence_table

APP_LOGO_PATH = Path('assets/nifty_market_terminal_logo.png')
APP_AVATAR_PATH = Path('assets/nifty_market_terminal_avatar.png')
APP_WORDMARK_PATH = Path('assets/nifty_market_terminal_wordmark.png')
APP_LOGO_FALLBACK = '📈'
AI_AVATAR_FALLBACK = '🤖'

def get_snapshot() -> pd.DataFrame:
    df = st.session_state.get("snapshot", pd.DataFrame())
    if not df.empty and st.session_state.get("global_liquidity_filter"):
        df = df[df["LiquidityEligible"].fillna(False)].copy()
    return df


def get_convergence() -> pd.DataFrame:
    if st.session_state.get("use_confluence_v2"):
        df = st.session_state.get("convergence_v2", pd.DataFrame())
    else:
        df = st.session_state.get("convergence", pd.DataFrame())
        
    if not df.empty and st.session_state.get("global_liquidity_filter"):
        df = df[df["LiquidityEligible"].fillna(False)].copy()
    return df


def _logo_exists() -> bool:
    return APP_LOGO_PATH.is_file()


def _avatar_exists() -> bool:
    return APP_AVATAR_PATH.is_file()


def _wordmark_exists() -> bool:
    return APP_WORDMARK_PATH.is_file()


def _logo_source():
    return str(APP_LOGO_PATH) if _logo_exists() else APP_LOGO_FALLBACK


def _ai_avatar_source():
    return str(APP_AVATAR_PATH) if _avatar_exists() else (
        str(APP_LOGO_PATH) if _logo_exists() else AI_AVATAR_FALLBACK
    )


def render_sidebar_brand():
    """Compact top-of-sidebar brand lockup: icon + terminal name."""
    logo_col, text_col = st.columns([0.24, 1], gap="small")

    with logo_col:
        if _logo_exists():
            st.image(str(APP_LOGO_PATH), width=44)
        else:
            st.markdown("### 📈")

    with text_col:
        st.markdown(
            """
<div class="brand-lockup-name">Nifty Total<br>Market Terminal</div>
<div class="brand-lockup-sub">Research terminal</div>
""",
            unsafe_allow_html=True,
        )


def terminal_header(page_title: str, subtitle: str, show_logo: bool = False):
    universe_count = len(st.session_state.get("universe", []))
    scan_date = st.session_state.get("scan_date", "Not run")

    if show_logo:
        logo_col, header_col = st.columns([0.08, 1], gap="small")
        with logo_col:
            if _logo_exists():
                st.image(str(APP_LOGO_PATH), width=54)
            else:
                st.markdown("### 📈")
        with header_col:
            st.markdown(
                f"""
<div class="terminal-topbar">
  <div class="terminal-kicker">NIFTY MARKET TERMINAL</div>
  <div class="terminal-brand">{page_title}</div>
  <div class="terminal-sub">{subtitle}</div>
</div>
""",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            f"""
<div class="terminal-topbar">
  <div class="terminal-kicker">NIFTY MARKET TERMINAL</div>
  <div class="terminal-brand">{page_title}</div>
  <div class="terminal-sub">{subtitle}</div>
</div>
""",
            unsafe_allow_html=True,
        )

    if "snapshot" in st.session_state:
        status = '<span class="status-chip green">SCAN READY</span>'
    else:
        status = '<span class="status-chip orange">RUN A SCAN FIRST</span>'

    st.markdown(
        f"""
<div>
  {status}
  <span class="status-chip">Universe: {universe_count or "Not scanned"}</span>
  <span class="status-chip">Last scan: {scan_date}</span>
</div>
""",
        unsafe_allow_html=True,
    )


def ai_prefilter_note():
    st.caption(
        f"AI verification note. To keep strategy checks focused and efficient, "
        f"the AI uses a high-conviction candidate pool of {AI_STRATEGY_PREFILTER_SCORE}+ "
        f"before running its list verification. This does not change the visible "
        f"Confluence, Final Buy List, or Emerging strategy rules."
    )


def page_intro(title: str, copy: str):
    st.markdown(
        f"""
<div class="page-hero">
  <div class="page-kicker">Research guide</div>
  <div class="page-title">{title}</div>
  <div class="page-copy">{copy}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def guide(title: str, copy: str, steps=None):
    items = ""
    for i, step in enumerate(steps or [], start=1):
        items += f'<div class="guide-step"><b>{i}.</b> {step}</div>'

    st.markdown(
        f"""
<div class="guide-box">
  <div class="guide-title">{title}</div>
  <div class="guide-copy">{copy}{items}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def card(title: str, copy: str):
    st.markdown(
        f"""
<div class="card">
  <div class="card-title">{title}</div>
  <div class="card-copy">{copy}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def require_scan():
    if "snapshot" not in st.session_state:
        st.info(
            "Run the market scan from **Scan Engine** first. "
            "All strategy pages reuse that cached scan."
        )
        st.stop()


def render_terminal_footer():
    """Persistent ownership attribution for the terminal."""
    st.markdown(
        """
<div class="terminal-footer">
    <div class="footer-owner">© CapitalSense Advisors. All rights reserved.</div>
    <div>Nifty Total Market Terminal is a proprietary research application.</div>
    <div>Run by Shubham Tejani</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_trendlyne_widgets(symbol: str):
    import streamlit.components.v1 as components
    tl_sym = symbol.replace(".NS", "")
    st.subheader("Trendlyne Consensus")
    st.caption("Note: AI analysis is generated exclusively from CapitalSense proprietary data and cannot read external Trendlyne widgets.")
    
    html_code = f"""
    <div style="display: flex; flex-direction: row; gap: 20px;">
        <div style="flex: 1; min-width: 300px;">
            <div class="tl-swot-widget" data-ticker="{tl_sym}" data-exchange="NSE" data-theme="light" data-font="Helvetica"></div>
        </div>
        <div style="flex: 1; min-width: 300px;">
            <div class="tl-qvt-widget" data-ticker="{tl_sym}" data-exchange="NSE" data-theme="light" data-font="Helvetica"></div>
        </div>
    </div>
    <script async src="https://trendlyne.com/web-widget/widget.js"></script>
    """
    components.html(html_code, height=450, scrolling=True)


