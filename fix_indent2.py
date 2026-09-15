with open("market_regime.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
    
# Find the lines that are broken
for i in range(len(lines)):
    if "with sqlite3.connect(DB_PATH) as conn:" in lines[i]:
        # If it has 8 spaces, it was init_regime_db which should have 4.
        # Wait, inside init_regime_db, it was 4 spaces. My replace made it 8.
        if lines[i].startswith("        with sqlite3.connect"):
            lines[i] = "    with sqlite3.connect" + lines[i][28:]
        # If it has 4 spaces and is at the end...
        if lines[i].startswith("with sqlite3.connect"):
            lines[i] = "    with sqlite3.connect" + lines[i][20:]

with open("market_regime.py", "w", encoding="utf-8") as f:
    f.writelines(lines)