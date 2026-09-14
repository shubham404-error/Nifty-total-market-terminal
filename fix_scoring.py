with open("scoring.py", "r", encoding="utf-8") as f:
    content = f.read()

import re

# Add imports
imports = """from decision_config import V4_CONFIG
from market_regime import update_market_regime
import datetime
"""
content = content.replace("from constants import", imports + "from constants import")

new_func = """def compute_funnel_booleans(snapshot: pd.DataFrame) -> pd.DataFrame:
    if snapshot.empty:
        return snapshot
        
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    index_stage = 2 # Dummy value if we don't have Nifty50. Ideally fetch from actual Nifty50 stage
    # For now, just use 2.
    
    # Check if Nifty 50 exists in snapshot to get actual stage
    nifty_row = snapshot[snapshot["Symbol"] == "^NSEI"]
    if not nifty_row.empty:
        index_stage = int(nifty_row["Stage"].iloc[0])
        
    regime_info = update_market_regime(date_str, snapshot, index_stage)
    regime = regime_info["Regime"]
    
    current_regime_threshold = V4_CONFIG["CONFLUENCE_STANDARD"]
    if regime == "DEFENSIVE":
        current_regime_threshold = V4_CONFIG["CONFLUENCE_DEFENSIVE"]
        
    snapshot["passed_data_quality"] = snapshot["HistoryEligible"].fillna(False).astype(bool)
    
    # 2. LIQUIDITY (Hard Gate)
    snapshot["passed_liquidity"] = pd.to_numeric(snapshot.get("AvgTradedValue20", 0), errors="coerce") >= 1_00_00_000
    
    # 3. STAGE (Hard Gate)
    snapshot["passed_stage"] = snapshot.get("Stage", -1).isin([1, 2])
    
    # 4. LEADERSHIP (Hard Gate)
    snapshot["passed_leadership"] = pd.to_numeric(snapshot.get("Raw_RS_Rating", 0), errors="coerce") >= V4_CONFIG["RS_RATING_MIN"]
    
    # 5. CONFLUENCE (Hard Gate)
    snapshot["passed_confluence"] = pd.to_numeric(snapshot.get("ConvergenceScore", 0), errors="coerce") >= current_regime_threshold
    
    # 6. ENTRY SETUP (Hard Gate)
    valid_patterns = V4_CONFIG["VALID_ENTRY_PATTERNS"]
    snapshot["passed_entry"] = snapshot.get("EntryPattern", "").isin(valid_patterns) & snapshot.get("EntrySetupQualified", False).astype(bool)
    
    # Overall funnel pass
    snapshot["passed_all"] = (
        snapshot["passed_data_quality"] & 
        snapshot["passed_liquidity"] & 
        snapshot["passed_stage"] & 
        snapshot["passed_leadership"] & 
        snapshot["passed_confluence"] & 
        snapshot["passed_entry"]
    )
    
    if regime == "CRISIS":
        snapshot["passed_all"] = False
        
    return snapshot
"""

content = content.replace("def build_final_buy_list(", new_func + "\ndef build_final_buy_list(")

# Apply in build_final_buy_list
old_logic = """    source = convergence.copy()
    if prefilter_score is not None:
        source = build_ai_confluence_pool(source, min_score=prefilter_score)"""

new_logic = """    source = convergence.copy()
    source = compute_funnel_booleans(source)
    if not FILTERS_SHADOW_MODE:
        source = source[source["passed_all"]].copy()
        
    if prefilter_score is not None:
        source = build_ai_confluence_pool(source, min_score=prefilter_score)"""

content = content.replace(old_logic, new_logic)

with open("scoring.py", "w", encoding="utf-8") as f:
    f.write(content)