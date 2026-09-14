with open("engine.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    '"Pattern", "Entry_Quality",',
    '"Pattern", "EntryPattern", "Entry_Quality",'
)

with open("engine.py", "w", encoding="utf-8") as f:
    f.write(content)