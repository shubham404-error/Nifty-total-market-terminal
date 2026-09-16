import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace imports
content = re.sub(
    r'from pages.strategies import regime_page, momentum_page, swing_page, pullback_page\nfrom pages.ai_analyst import nifty_ai_page\nfrom pages.confluence import convergence_page\nfrom pages.buying_list import buying_list_page\nfrom pages.market_health import market_health_page\nfrom pages.positions_at_risk import positions_at_risk_page',
    'from pages.strategies import pullback_page\nfrom pages.ai_analyst import nifty_ai_page\nfrom pages.confluence import convergence_page\nfrom pages.buying_list import buying_list_page\nfrom pages.market_structure import market_structure_page\nfrom pages.candlesticks import candlesticks_page\nfrom pages.rs_and_stage import rs_and_stage_page\nfrom pages.signal_ledger import positions_at_risk_page as signal_ledger_page',
    content
)

pages_dict = """pages = {
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
}"""

content = re.sub(r'pages = \{.*?\n\}', pages_dict, content, flags=re.DOTALL)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)