from decision_config import V4_CONFIG
import pandas as pd
import json

def evaluate_decay(current_snapshot_row: pd.Series, original_thesis_dict: dict, previous_decay_state: str = "INTACT", consecutive_closes_below_200sma: int = 0) -> tuple:
    if previous_decay_state == "THESIS_BROKEN":
        return "THESIS_BROKEN", ["Thesis previously broken — permanent"], []
    """Returns (DecayState, DecayReasons, DecayFactorGroups)"""
    reasons = []
    groups = set()
    
    # 1. TREND_STRUCTURE
    trend_reasons = []
    if current_snapshot_row.get("Stage", 0) != original_thesis_dict.get("Stage"):
        trend_reasons.append(f"Stage changed from {original_thesis_dict.get('Stage')} to {current_snapshot_row.get('Stage')}")
    if current_snapshot_row.get("Close", 0) < current_snapshot_row.get("SMA50", 0):
        trend_reasons.append("Close below 50 SMA")
    if current_snapshot_row.get("Close", 0) < current_snapshot_row.get("SMA200", 0):
        trend_reasons.append("Close below 200 SMA")
        
    if trend_reasons:
        reasons.extend(trend_reasons)
        groups.add("TREND_STRUCTURE")
        
    # 2. LEADERSHIP
    lead_reasons = []
    curr_rs = current_snapshot_row.get("Raw_RS_Rating", 0)
    orig_rs = original_thesis_dict.get("RS_Rating", 0)
    if orig_rs - curr_rs >= V4_CONFIG["RS_DECAY_THRESHOLD"]:
        lead_reasons.append(f"RS_Rating dropped by >= {V4_CONFIG['RS_DECAY_THRESHOLD']} points")
    if curr_rs < 50:
        lead_reasons.append("RS Rating < 50")
        
    if lead_reasons:
        reasons.extend(lead_reasons)
        groups.add("LEADERSHIP")
        
    # 3. MOMENTUM
    # Simplified placeholder for momentum drop
    if current_snapshot_row.get("BullMomentum") == False and original_thesis_dict.get("BullMomentum") == True:
        reasons.append("Lost bullish momentum")
        groups.add("MOMENTUM")
        
    # 4. LIQUIDITY
    if current_snapshot_row.get("AvgTradedValue20", 0) < 1_00_00_000:
        reasons.append("Liquidity dropped below threshold")
        groups.add("LIQUIDITY")
        
    # Evaluate severity
    sma200_slope = current_snapshot_row.get("SMA200Slope20", 0) # Fallback to 0 if not present
    
    major_structural = (
        current_snapshot_row.get("Stage") == 4
        or (
            consecutive_closes_below_200sma >= 2
            and sma200_slope <= 0
        )
    )
    
    if major_structural:
        state = "THESIS_BROKEN"
    elif len(groups) >= 2:
        state = "STRUCTURAL_DECAY"
    elif len(groups) == 1:
        state = "EARLY_WARNING"
    else:
        state = "INTACT"
        
    return state, reasons, list(groups)