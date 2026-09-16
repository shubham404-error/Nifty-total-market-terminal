with open("engine.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('frame["SMA200"] = close.rolling(200, min_periods=200).mean()', 'frame["SMA200"] = close.rolling(200, min_periods=200).mean()\n        frame["RollingHigh20"] = high.rolling(20, min_periods=20).max()')
content = content.replace('"Close", "EMA9", "EMA21", "SMA20", "SMA50", "SMA200", "SMA50Slope20",', '"Close", "EMA9", "EMA21", "SMA20", "SMA50", "SMA200", "SMA50Slope20", "RollingHigh20",')

with open("engine.py", "w", encoding="utf-8") as f:
    f.write(content)