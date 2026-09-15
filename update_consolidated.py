import os
import glob

files_to_consolidate = glob.glob("**/*.py", recursive=True) + glob.glob("**/*.txt", recursive=True) + glob.glob("**/*.md", recursive=True)

# Exclude virtual environments, cache, etc.
files_to_consolidate = [f for f in files_to_consolidate if "venv" not in f and "__pycache__" not in f and ".git" not in f]

with open("consolidated_codebase.txt", "w", encoding="utf-8") as outfile:
    for filepath in files_to_consolidate:
        if os.path.isfile(filepath):
            outfile.write(f"\n--- BEGIN FILE: {filepath} ---\n\n")
            try:
                with open(filepath, "r", encoding="utf-8") as infile:
                    outfile.write(infile.read())
            except Exception as e:
                outfile.write(f"Error reading file: {e}")
            outfile.write(f"\n--- END FILE: {filepath} ---\n")

print("Consolidated codebase updated with all files.")