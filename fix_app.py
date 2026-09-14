with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

import re

imports_old = "from pages.buying_list import buying_list_page"
imports_new = "from pages.buying_list import buying_list_page\nfrom pages.market_health import market_health_page\nfrom pages.positions_at_risk import positions_at_risk_page"
content = content.replace(imports_old, imports_new)

pages_old = """    "Start": [
        st.Page(
            home_page,
            title="Home",
            icon="🏠",
            url_path="home",
        ),
    ],"""
pages_new = """    "Start": [
        st.Page(
            home_page,
            title="Home",
            icon="🏠",
            url_path="home",
        ),
    ],
    "Health": [
        st.Page(
            market_health_page,
            title="Market Health",
            icon="🩺",
            url_path="market-health",
        ),
        st.Page(
            positions_at_risk_page,
            title="Positions at Risk",
            icon="🚨",
            url_path="positions-at-risk",
        ),
    ],"""
content = content.replace(pages_old, pages_new)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)