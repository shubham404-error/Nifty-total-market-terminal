import glob
for file in glob.glob("tests/test_*.py"):
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()
    if "def clean_db():" in content:
        old_fix = """def clean_db():
    with sqlite3.connect"""
        new_fix = """def clean_db():
    import os
    os.makedirs("data", exist_ok=True)
    with sqlite3.connect"""
        content = content.replace(old_fix, new_fix)
        with open(file, "w", encoding="utf-8") as f:
            f.write(content)