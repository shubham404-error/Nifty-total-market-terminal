with open("signal_ledger.py", "r", encoding="utf-8") as f:
    content = f.read()
if "CloseReason TEXT" not in content:
    content = content.replace("DataStatus TEXT", "DataStatus TEXT,\n                CloseReason TEXT")
    with open("signal_ledger.py", "w", encoding="utf-8") as f:
        f.write(content)