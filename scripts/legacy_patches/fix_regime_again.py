with open("market_regime.py", "r", encoding="utf-8") as f:
    content = f.read()

import re

old_text = """    # Previous crisis persistence
    if len(df_hist) > 1 and "crisis_persistence" in df_hist.columns:
        prev_persistence = int(df_hist["crisis_persistence"].iloc[-2]) if not pd.isna(df_hist["crisis_persistence"].iloc[-2]) else 0
    else:
        prev_persistence = 0
        
    # Crisis condition
    crisis_condition = (index_stage == 4) and (breadth_20 < V4_CONFIG["BREADTH_CRISIS_THRESHOLD"])
    if crisis_condition:
        curr_persistence = prev_persistence + 1
    else:
        curr_persistence = max(0, prev_persistence - 1)
        
    if curr_persistence >= V4_CONFIG["CRISIS_PERSISTENCE"]:
        regime = "CRISIS"
    elif index_stage == 4 or breadth_20 < V4_CONFIG["BREADTH_DEFENSIVE_THRESHOLD"] or structural_health <= 0:
        regime = "DEFENSIVE"
    elif index_stage in {1, 2} and breadth_20 >= V4_CONFIG["BREADTH_BULLISH_THRESHOLD"] and structural_health > 0:
        regime = "BULLISH"
    else:
        regime = "NEUTRAL" """

new_text = """    # Previous crisis persistence
    if len(df_hist) > 1 and "crisis_persistence" in df_hist.columns:
        prev_persistence = int(df_hist["crisis_persistence"].iloc[-2]) if not pd.isna(df_hist["crisis_persistence"].iloc[-2]) else 0
        prev_regime = str(df_hist["regime"].iloc[-2])
    else:
        prev_persistence = 0
        prev_regime = "NEUTRAL"
        
    # Crisis condition
    crisis_condition = (index_stage == 4) and (breadth_20 < V4_CONFIG["BREADTH_CRISIS_THRESHOLD"])
    
    if crisis_condition:
        curr_persistence = prev_persistence + 1
    else:
        if prev_regime == "CRISIS":
            curr_persistence = prev_persistence - 1
        else:
            curr_persistence = 0
            
    if prev_regime == "CRISIS" and curr_persistence > (V4_CONFIG["CRISIS_PERSISTENCE"] - V4_CONFIG["CRISIS_EXIT_PERSISTENCE"]):
        regime = "CRISIS"
    elif curr_persistence >= V4_CONFIG["CRISIS_PERSISTENCE"]:
        regime = "CRISIS"
        curr_persistence = V4_CONFIG["CRISIS_PERSISTENCE"]
    elif index_stage == 4 or breadth_20 < V4_CONFIG["BREADTH_DEFENSIVE_THRESHOLD"] or structural_health <= 0:
        regime = "DEFENSIVE"
    elif index_stage in {1, 2} and breadth_20 >= V4_CONFIG["BREADTH_BULLISH_THRESHOLD"] and structural_health > 0:
        regime = "BULLISH"
    else:
        regime = "NEUTRAL" """

# Fallback string replace in case of spacing issues
content = re.sub(r'    # Previous crisis persistence\s+if len\(df_hist\).*?regime = "NEUTRAL"\s+', new_text + "\n\n", content, flags=re.DOTALL)

with open("market_regime.py", "w", encoding="utf-8") as f:
    f.write(content)