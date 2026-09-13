import pandas as pd
import numpy as np
from stage_rs import calculate_stage, calculate_rs_rating

def test_stage_analysis():
    # Synthetic close prices
    close = pd.Series(np.linspace(100, 200, 300)) # Up trend
    stages = calculate_stage(close)
    
    # Should reach Stage 2 eventually because it's in a pure uptrend above 150SMA
    assert 2 in stages["stage"].values
    
def test_rs_rating_insufficient_history():
    close = pd.Series(np.random.randn(100)) # Less than 252 days
    res = calculate_rs_rating(close, {}, "2023-01-01")
    assert res["insufficient_data"] == True
    assert res["rs_rating"] is None