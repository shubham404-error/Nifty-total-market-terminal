with open("tests/test_market_regime.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("conn.execute(\"DROP TABLE IF EXISTS regime_history\")", "pass")

with open("tests/test_market_regime.py", "w", encoding="utf-8") as f:
    f.write(content)