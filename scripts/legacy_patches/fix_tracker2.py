with open("thesis_tracker.py", "r", encoding="utf-8") as f:
    content = f.read()

import re

old_eval = """    # Evaluate severity
    sma200_slope = 0.0 # Assuming it's calculated in snapshot if needed, or defaults to 0
    # Actually, we can approximate slope if we don't have it, but for now we rely on the parameter
    
    major_structural = (
        current_snapshot_row.get("Stage") == 4
        or (
            consecutive_closes_below_200sma >= 2
            # Assuming sma200 slope is <= 0 if not explicitly bullish. We can't strictly compute slope without history,
            # so we'll just check if SMA200 hasn't gone up (not strictly implemented but parameter acts as placeholder).
        )
    )"""

new_eval = """    # Evaluate severity
    sma200_slope = current_snapshot_row.get("SMA200Slope20", 0) # Fallback to 0 if not present
    
    major_structural = (
        current_snapshot_row.get("Stage") == 4
        or (
            consecutive_closes_below_200sma >= 2
            and sma200_slope <= 0
        )
    )"""

content = content.replace(old_eval, new_eval)

with open("thesis_tracker.py", "w", encoding="utf-8") as f:
    f.write(content)