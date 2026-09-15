with open("scoring.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'snapshot["passed_leadership"] = pd.to_numeric(snapshot.get("Raw_RS_Rating", 0), errors="coerce") >= V4_CONFIG["RS_RATING_MIN"]',
    'snapshot["passed_leadership"] = pd.to_numeric(snapshot.get("RS_Rating", 0), errors="coerce") >= V4_CONFIG["RS_RATING_MIN"]'
)

with open("scoring.py", "w", encoding="utf-8") as f:
    f.write(content)