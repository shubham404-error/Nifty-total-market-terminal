with open("tests/test_market_regime.py", "r", encoding="utf-8") as f:
    content = f.read()

import re

old_crisis = """    for i in range(3, 40):
        update_market_regime(f"2026-09-{i:02d}", df_crisis, 4)
    res_crisis = update_market_regime("2026-09-40", df_crisis, 4) # Fake date to get past 30 days and drop EMA"""

new_crisis = """    import datetime
    d = datetime.date(2026, 9, 3)
    for i in range(40):
        update_market_regime(d.strftime("%Y-%m-%d"), df_crisis, 4)
        d += datetime.timedelta(days=1)
    res_crisis = update_market_regime(d.strftime("%Y-%m-%d"), df_crisis, 4)"""
content = content.replace(old_crisis, new_crisis)

old_exit = """    def test_crisis_exit_persistence():
        df = pd.DataFrame({"HistoryEligible": [True]*10, "Close": [90]*10, "SMA200": [100]*10, "Stage": [4]*10})
        update_market_regime("2026-09-01", df, 4)
        update_market_regime("2026-09-02", df, 4)
        update_market_regime("2026-09-03", df, 4) # CRISIS
    
        # Now non-crisis
        df_good = pd.DataFrame({"HistoryEligible": [True]*10, "Close": [110]*10, "SMA200": [100]*10, "Stage": [2]*10})
        r1 = update_market_regime("2026-09-04", df_good, 2)
        assert r1["Regime"] == "CRISIS"
        assert r1["CrisisPersistence"] == 2
        
        r2 = update_market_regime("2026-09-05", df_good, 2)
        assert r2["Regime"] != "CRISIS"
        assert r2["CrisisPersistence"] == 0"""

new_exit = """    def test_crisis_exit_persistence():
        import datetime
        df = pd.DataFrame({"HistoryEligible": [True]*10, "Close": [90]*10, "SMA200": [100]*10, "Stage": [4]*10})
        d = datetime.date(2026, 9, 1)
        for i in range(40):
            update_market_regime(d.strftime("%Y-%m-%d"), df, 4)
            d += datetime.timedelta(days=1)
        
        # We are now in CRISIS
        df_good = pd.DataFrame({"HistoryEligible": [True]*10, "Close": [110]*10, "SMA200": [100]*10, "Stage": [2]*10})
        
        # Exit day 1
        d += datetime.timedelta(days=1)
        while not is_valid_session(d.strftime("%Y-%m-%d")): d += datetime.timedelta(days=1)
        r1 = update_market_regime(d.strftime("%Y-%m-%d"), df_good, 2)
        assert r1["Regime"] == "CRISIS"
        assert r1["CrisisPersistence"] == 2
        
        # Exit day 2
        d += datetime.timedelta(days=1)
        while not is_valid_session(d.strftime("%Y-%m-%d")): d += datetime.timedelta(days=1)
        r2 = update_market_regime(d.strftime("%Y-%m-%d"), df_good, 2)
        assert r2["Regime"] != "CRISIS"
        assert r2["CrisisPersistence"] == 0"""
content = content.replace(old_exit, new_exit)
# Also add is_valid_session import if missing
content = "from trading_calendar import is_valid_session\n" + content

with open("tests/test_market_regime.py", "w", encoding="utf-8") as f:
    f.write(content)