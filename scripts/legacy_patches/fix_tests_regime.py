with open("tests/test_market_regime.py", "r", encoding="utf-8") as f:
    content = f.read()

import re

old_crisis = """    update_market_regime("2026-09-03", df_crisis, 4) # persistence = 1
    update_market_regime("2026-09-04", df_crisis, 4) # persistence = 2
    res_crisis = update_market_regime("2026-09-05", df_crisis, 4) # persistence = 3"""

new_crisis = """    for i in range(3, 40):
        update_market_regime(f"2026-09-{i:02d}", df_crisis, 4)
    res_crisis = update_market_regime("2026-09-40", df_crisis, 4) # Fake date to get past 30 days and drop EMA"""
content = content.replace(old_crisis, new_crisis)

old_exit = """    def test_crisis_exit_persistence():
        df = pd.DataFrame({"HistoryEligible": [True]*10, "Close": [90]*10, "SMA200": [100]*10, "Stage": [4]*10})
        update_market_regime("2026-09-01", df, 4)
        update_market_regime("2026-09-02", df, 4)
        update_market_regime("2026-09-03", df, 4) # CRISIS"""

new_exit = """    def test_crisis_exit_persistence():
        df = pd.DataFrame({"HistoryEligible": [True]*10, "Close": [90]*10, "SMA200": [100]*10, "Stage": [4]*10})
        for i in range(1, 40):
            update_market_regime(f"2026-08-{i:02d}", df, 4)"""
content = content.replace(old_exit, new_exit)

with open("tests/test_market_regime.py", "w", encoding="utf-8") as f:
    f.write(content)