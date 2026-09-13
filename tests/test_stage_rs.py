import pandas as pd
import numpy as np
import pytest
from stage_rs import calculate_stage, calculate_mansfield_rs, calculate_rs_rating, scale_rs_ratings

# --- EXISTING (keep) ---

def test_stage2_detection_uptrend():
    """Synthetic uptrend must eventually classify as Stage 2."""
    close = pd.Series(np.linspace(100, 200, 300))
    stages = calculate_stage(close)
    assert 2 in stages["stage"].values

def test_rs_rating_insufficient_history():
    """< 252 bars must return insufficient_data=True."""
    close = pd.Series(np.random.randn(100))
    res = calculate_rs_rating(close)
    assert res["insufficient_data"] == True
    assert res["rs_rating"] is None

# --- NEW (add all of these) ---

def test_stage4_detection_downtrend():
    """Synthetic downtrend: price declining below a falling 150MA."""
    close = pd.Series(np.concatenate([
        np.linspace(200, 250, 200),  # rise first to establish history
        np.linspace(250, 120, 200),  # then decline
    ]))
    stages = calculate_stage(close)
    assert 4 in stages["stage"].values

def test_stage1_vs_stage3_disambiguation():
    """After Stage 4 -> flat = Stage 1. After Stage 2 -> flat = Stage 3."""
    close = pd.Series(np.concatenate([
        np.linspace(100, 200, 200),   # rise -> Stage 2
        np.full(100, 200),             # flatten -> should be Stage 3
        np.linspace(200, 100, 200),   # decline -> Stage 4
        np.full(300, 100),             # flatten -> should be Stage 1
    ]))
    stages = calculate_stage(close)
    stage_vals = stages["stage"]
    # After the first flat period (following rise), should be Stage 3
    flat_after_rise = stage_vals.iloc[250:290]
    assert (flat_after_rise == 3).any(), "Flat after Stage 2 should resolve to Stage 3"
    # After the second flat period (following decline), should be Stage 1
    flat_after_decline = stage_vals.iloc[750:790]
    assert (flat_after_decline == 1).any(), "Flat after Stage 4 should resolve to Stage 1"

def test_stage_nan_before_150_bars():
    """First 149 bars must be NaN (insufficient data for 150MA)."""
    close = pd.Series(np.linspace(100, 200, 300))
    stages = calculate_stage(close)
    assert stages["stage"].iloc[:149].isna().all()

def test_mansfield_rs_flat_stock_equals_index():
    """If stock price == index price for the full window, MRS should be ~0."""
    prices = pd.Series(np.linspace(100, 150, 300))
    mrs = calculate_mansfield_rs(prices, prices)
    # After the 200-bar warmup, MRS should be approximately zero
    assert mrs.iloc[-1] == pytest.approx(0, abs=0.01)

def test_mansfield_rs_outperformer_positive():
    """Stock rising faster than index should have positive MRS."""
    stock = pd.Series(np.linspace(100, 300, 300))
    index = pd.Series(np.linspace(100, 150, 300))
    mrs = calculate_mansfield_rs(stock, index)
    assert mrs.iloc[-1] > 0

def test_rs_rating_cross_sectional_ordering():
    """Best performer should get highest percentile, worst gets lowest."""
    scores = pd.Series([0.50, 0.10, 0.30, 0.05, 0.80], index=['A','B','C','D','E'])
    scaled = scale_rs_ratings(scores)
    assert scaled['E'] > scaled['A'] > scaled['C'] > scaled['B'] > scaled['D']

def test_rs_rating_bounds():
    """Scaled RS Rating must be between 1 and 99."""
    scores = pd.Series(np.random.randn(200))
    scaled = scale_rs_ratings(scores)
    assert scaled.min() >= 1
    assert scaled.max() <= 99