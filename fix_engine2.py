with open("engine.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    '"Close", "EMA9", "EMA21", "SMA20", "SMA50", "SMA200",',
    '"Close", "EMA9", "EMA21", "SMA20", "SMA50", "SMA200", "SMA50Slope20",'
)

with open("engine.py", "w", encoding="utf-8") as f:
    f.write(content)