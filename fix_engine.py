import re
with open("engine.py", "r", encoding="utf-8") as f:
    content = f.read()

old_block = """        frame["SMA50"] = close.rolling(50, min_periods=50).mean()
        frame["SMA200"] = close.rolling(200, min_periods=200).mean()"""
new_block = """        frame["SMA50"] = close.rolling(50, min_periods=50).mean()
        frame["SMA200"] = close.rolling(200, min_periods=200).mean()
        
        # V4.1: 20-day slope of the 50 SMA for EntrySetupQualified
        sma50 = frame["SMA50"]
        sma50_20d_ago = sma50.shift(20)
        frame["SMA50Slope20"] = (sma50 - sma50_20d_ago) / sma50_20d_ago"""

content = content.replace(old_block, new_block)

old_latest = '        "SMA20", "SMA50", "SMA200",'
new_latest = '        "SMA20", "SMA50", "SMA200", "SMA50Slope20",'
content = content.replace(old_latest, new_latest)

with open("engine.py", "w", encoding="utf-8") as f:
    f.write(content)