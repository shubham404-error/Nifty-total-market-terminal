import pandas as pd
from thesis_tracker import evaluate_decay

def test_factor_group_independence():
    current = pd.Series({"Stage": 2, "Raw_RS_Rating": 40, "Close": 105, "SMA50": 100, "SMA200": 90, "AvgTradedValue20": 5000000})
    original = {"Stage": 2, "RS_Rating": 60}
    
    state, reasons, groups = evaluate_decay(current, original)
    
    # RS_Rating dropped 20 points + < 50 => LEADERSHIP group
    # Liquidity dropped => LIQUIDITY group
    assert "LEADERSHIP" in groups
    assert "LIQUIDITY" in groups
    assert len(groups) == 2
    assert state == "STRUCTURAL_DECAY"

def test_thesis_broken_permanence():
    current = pd.Series({"Stage": 2, "Raw_RS_Rating": 80, "Close": 105, "SMA200": 90})
    original = {"Stage": 2, "RS_Rating": 80}
    
    # Even if it looks intact now, previous state was broken
    state, _, _ = evaluate_decay(current, original, previous_decay_state="THESIS_BROKEN")
    assert state == "THESIS_BROKEN"