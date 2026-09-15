with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

import re

old_start = """    "Start": [
        st.Page(
            home_page,
            title="Home",
            icon="🏠",
            url_path="home",
            default=True,
        ),
    ],"""

new_start = """    "Start": [
        st.Page(
            home_page,
            title="Home",
            icon="🏠",
            url_path="home",
            default=True,
        ),
    ],
    "Monitor": [
        st.Page(
            market_health_page,
            title="Market Health",
            icon="🩺",
            url_path="market-health"
        ),
        st.Page(
            positions_at_risk_page,
            title="Positions at Risk",
            icon="🚨",
            url_path="positions-at-risk"
        ),
    ],"""

content = content.replace(old_start, new_start)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)