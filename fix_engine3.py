with open("engine.py", "r", encoding="utf-8") as f:
    content = f.read()

old_engine = '        frame["Pattern"] = detect_patterns(frame)'
new_engine = '        frame["Pattern"], frame["EntryPattern"] = detect_patterns(frame)'

content = content.replace(old_engine, new_engine)

with open("engine.py", "w", encoding="utf-8") as f:
    f.write(content)