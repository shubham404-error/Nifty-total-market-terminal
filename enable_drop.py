with open("tests/test_market_regime.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("pass", "conn.execute(\"DROP TABLE IF EXISTS regime_history\")")

with open("tests/test_market_regime.py", "w", encoding="utf-8") as f:
    f.write(content)