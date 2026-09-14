with open("engine.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("Has_252d_History", "HistoryEligible")

with open("engine.py", "w", encoding="utf-8") as f:
    f.write(content)