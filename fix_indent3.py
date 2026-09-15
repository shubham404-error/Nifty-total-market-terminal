with open("market_regime.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
    
# Find the lines that are broken
for i in range(len(lines)):
    if "with sqlite3.connect(DB_PATH) as conn:" in lines[i]:
        if i > 0 and "if not is_valid_session" in "".join(lines[i-4:i]):
            lines[i] = "        with sqlite3.connect(DB_PATH) as conn:\n"

with open("market_regime.py", "w", encoding="utf-8") as f:
    f.writelines(lines)