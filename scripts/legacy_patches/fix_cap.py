with open("market_regime.py", "r", encoding="utf-8") as f:
    content = f.read()

import re

old_text = """    if prev_regime == "CRISIS" and curr_persistence > (V4_CONFIG["CRISIS_PERSISTENCE"] - V4_CONFIG["CRISIS_EXIT_PERSISTENCE"]):
        regime = "CRISIS"
    elif curr_persistence >= V4_CONFIG["CRISIS_PERSISTENCE"]:
        regime = "CRISIS"
        curr_persistence = V4_CONFIG["CRISIS_PERSISTENCE"]"""

new_text = """    if prev_regime == "CRISIS" and curr_persistence > (V4_CONFIG["CRISIS_PERSISTENCE"] - V4_CONFIG["CRISIS_EXIT_PERSISTENCE"]):
        regime = "CRISIS"
        curr_persistence = min(curr_persistence, V4_CONFIG["CRISIS_PERSISTENCE"])
    elif curr_persistence >= V4_CONFIG["CRISIS_PERSISTENCE"]:
        regime = "CRISIS"
        curr_persistence = V4_CONFIG["CRISIS_PERSISTENCE"]"""

content = content.replace(old_text, new_text)

with open("market_regime.py", "w", encoding="utf-8") as f:
    f.write(content)