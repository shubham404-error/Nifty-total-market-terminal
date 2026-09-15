with open("market_regime.py", "r", encoding="utf-8") as f:
    content = f.read()

import re

old_update = "def update_market_regime(date_str: str, snapshot_df: pd.DataFrame, index_stage: int) -> dict:\n    init_regime_db()"

new_update = """def update_market_regime(date_str: str, snapshot_df: pd.DataFrame, index_stage: int) -> dict:
    init_regime_db()
    
    if not is_valid_session(date_str):
        # Return previous state without updating persistence
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            df_hist = pd.read_sql("SELECT * FROM regime_history ORDER BY date DESC LIMIT 1", conn)
        if not df_hist.empty:
            last = df_hist.iloc[0]
            return {
                "Regime": last["regime"],
                "Breadth20": last["breadth_20"],
                "BreadthTrend": last["breadth_trend"],
                "StructuralHealth": last["structural_health"],
                "IndexStage": last["index_stage"],
                "CrisisPersistence": last["crisis_persistence"]
            }
        else:
            return {"Regime": "NEUTRAL", "Breadth20": 0.0, "BreadthTrend": "Flat", "StructuralHealth": 0.0, "IndexStage": index_stage, "CrisisPersistence": 0}
"""
content = content.replace(old_update, new_update)

old_persistence = """    # Previous crisis persistence
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

new_persistence = """    # Previous crisis persistence
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
        curr_persistence = V4_CONFIG["CRISIS_PERSISTENCE"] # cap it
    elif index_stage == 4 or breadth_20 < V4_CONFIG["BREADTH_DEFENSIVE_THRESHOLD"] or structural_health <= 0:
        regime = "DEFENSIVE"
    elif index_stage in {1, 2} and breadth_20 >= V4_CONFIG["BREADTH_BULLISH_THRESHOLD"] and structural_health > 0:
        regime = "BULLISH"
    else:
        regime = "NEUTRAL" """

content = content.replace(old_persistence, new_persistence)

with open("market_regime.py", "w", encoding="utf-8") as f:
    f.write(content)