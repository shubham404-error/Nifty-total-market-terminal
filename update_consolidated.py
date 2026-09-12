import os

files_to_consolidate = [
    "app.py",
    "engine.py",
    "requirements.txt",
    "scripts/build_cache.py",
    "scripts/build_dvm_cache.py",
    "scripts/backtest.py",
    "tests/test_engine.py",
    "performance terminal/app.py",
    "performance terminal/requirements.txt"
]

with open("consolidated_codebase.txt", "w", encoding="utf-8") as outfile:
    for filepath in files_to_consolidate:
        if os.path.exists(filepath):
            outfile.write(f"\n--- BEGIN FILE: {filepath} ---\n\n")
            with open(filepath, "r", encoding="utf-8") as infile:
                outfile.write(infile.read())
            outfile.write(f"\n--- END FILE: {filepath} ---\n")
        else:
            print(f"File not found: {filepath}")

print("Consolidated codebase updated.")
