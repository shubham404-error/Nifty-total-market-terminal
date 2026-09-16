with open("scoring.py", "r", encoding="utf-8") as f:
    content = f.read()

replacement = """
                original_thesis = {
                    "Stage": int(s_row.get("Stage", 0)) if pd.notna(s_row.get("Stage")) else 0,
                    "RS_Rating": float(s_row.get("RS_Rating", 0)) if pd.notna(s_row.get("RS_Rating")) else None,
                    "Confluence": float(s_row.get("ConvergenceScore", 0)) if pd.notna(s_row.get("ConvergenceScore")) else None,
                    "EntryPattern": s_row.get("EntryPattern"),
                    "VolumeRatio": float(s_row.get("VolumeRatio", 0)) if pd.notna(s_row.get("VolumeRatio")) else None,
                    "Risk_SMA50": float(s_row.get("SMA50", 0)) if pd.notna(s_row.get("SMA50")) else None,
                    "Target_RollingHigh20": float(s_row.get("RollingHigh20", 0)) if pd.notna(s_row.get("RollingHigh20")) else None
                }
"""

import re
content = re.sub(r'original_thesis\s*=\s*\{.*?\}', replacement, content, flags=re.DOTALL)

with open("scoring.py", "w", encoding="utf-8") as f:
    f.write(content)