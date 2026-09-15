with open("tests/test_entry_setup.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("assert entry_patterns.iloc[-1] == None", "assert pd.isna(entry_patterns.iloc[-1])")

with open("tests/test_entry_setup.py", "w", encoding="utf-8") as f:
    f.write(content)