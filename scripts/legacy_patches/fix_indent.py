with open("market_regime.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("with sqlite3.connect(DB_PATH) as conn:\n        conn.execute(", "    with sqlite3.connect(DB_PATH) as conn:\n        conn.execute(")

with open("market_regime.py", "w", encoding="utf-8") as f:
    f.write(content)