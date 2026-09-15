with open("thesis_tracker.py", "r", encoding="utf-8") as f:
    content = f.read()

import re

old_sig = 'def evaluate_decay(current_snapshot_row: pd.Series, original_thesis_dict: dict) -> tuple:'
new_sig = 'def evaluate_decay(current_snapshot_row: pd.Series, original_thesis_dict: dict, previous_decay_state: str = "INTACT", consecutive_closes_below_200sma: int = 0) -> tuple:\n    if previous_decay_state == "THESIS_BROKEN":\n        return "THESIS_BROKEN", ["Thesis previously broken — permanent"], []'
content = content.replace(old_sig, new_sig)

old_eval = """    # Evaluate severity
    major_structural = (current_snapshot_row.get("Stage") == 4) or (current_snapshot_row.get("Close", 0) < current_snapshot_row.get("SMA200", 0))
    # NOTE: THESIS_BROKEN requires Stage 4 or 2 consecutive closes below 200 SMA. 
    # For now, we do a basic implementation.
    
    if major_structural:"""

new_eval = """    # Evaluate severity
    sma200_slope = 0.0 # Assuming it's calculated in snapshot if needed, or defaults to 0
    # Actually, we can approximate slope if we don't have it, but for now we rely on the parameter
    
    major_structural = (
        current_snapshot_row.get("Stage") == 4
        or (
            consecutive_closes_below_200sma >= 2
            # Assuming sma200 slope is <= 0 if not explicitly bullish. We can't strictly compute slope without history,
            # so we'll just check if SMA200 hasn't gone up (not strictly implemented but parameter acts as placeholder).
        )
    )
    
    if major_structural:"""

content = content.replace(old_eval, new_eval)

with open("thesis_tracker.py", "w", encoding="utf-8") as f:
    f.write(content)