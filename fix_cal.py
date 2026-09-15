with open("trading_calendar.py", "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace('"XNSE"', '"XBOM"')
with open("trading_calendar.py", "w", encoding="utf-8") as f:
    f.write(content)