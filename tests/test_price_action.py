import pandas as pd
import numpy as np
import pytest
from price_action import detect_patterns, calculate_entry_quality

def pad_df(df, target_len=20):
    np.random.seed(42)
    pad_len = target_len - len(df)
    if pad_len <= 0: return df
    
    pad = pd.DataFrame({
        "Open": np.random.uniform(98, 102, pad_len),
        "High": np.random.uniform(102, 105, pad_len),
        "Low": np.random.uniform(95, 98, pad_len),
        "Close": np.random.uniform(98, 102, pad_len),
        "Volume": 1000
    })
    return pd.concat([pad, df], ignore_index=True)

def test_bullish_engulfing():
    df = pd.DataFrame({"Open": [105, 94], "High": [106, 110], "Low": [94, 90], "Close": [95, 108], "Volume":[1000, 2000]})
    assert detect_patterns(pad_df(df)).iloc[-1] == "Bullish Engulfing"

def test_hammer():
    df = pd.DataFrame({"Open": [100], "High": [102], "Low": [90], "Close": [101], "Volume":[1000]})
    assert detect_patterns(pad_df(df)).iloc[-1] == "Hammer"
    
def test_harami():
    # Make the inside bar very small so range_atr_ratio < 0.8
    df = pd.DataFrame({"Open": [90, 101], "High": [115, 101.5], "Low": [85, 100.5], "Close": [110, 101], "Volume":[1000, 1000]})
    assert detect_patterns(pad_df(df)).iloc[-1] == "Harami"
    
def test_inverted_hammer():
    # Close > Open avoids overlapping with shooting star test
    df = pd.DataFrame({"Open": [99], "High": [110], "Low": [98], "Close": [100], "Volume":[1000]})
    assert detect_patterns(pad_df(df)).iloc[-1] == "Inverted Hammer"
    
def test_morning_star():
    df = pd.DataFrame({
        "Open": [110, 100, 101],
        "High": [112, 102, 110],
        "Low":  [98,  98,  100],
        "Close":[99,  101, 109],
        "Volume":[1000, 1000, 1000]
    })
    assert detect_patterns(pad_df(df)).iloc[-1] == "Morning Star"
    
def test_inside_bar_breakout():
    df = pd.DataFrame({
        "Open": [95, 100, 102],
        "High": [110, 105, 112],
        "Low":  [90, 95,  100],
        "Close":[108, 102, 111],
        "Volume":[1000, 1000, 1000]
    })
    assert detect_patterns(pad_df(df)).iloc[-1] == "Inside Bar Breakout"
    
def test_strong_breakout_candle():
    df = pd.DataFrame({"Open": [90], "High": [111], "Low": [89], "Close": [110], "Volume":[1000]})
    assert detect_patterns(pad_df(df)).iloc[-1] == "Strong Breakout Candle"
    
def test_bearish_engulfing():
    df = pd.DataFrame({"Open": [95, 109], "High": [110, 111], "Low": [90, 89], "Close": [108, 94], "Volume":[1000, 2000]})
    assert detect_patterns(pad_df(df)).iloc[-1] == "Bearish Engulfing"
    
def test_shooting_star():
    df = pd.DataFrame({"Open": [100], "High": [110], "Low": [98], "Close": [99], "Volume":[1000]})
    assert detect_patterns(pad_df(df)).iloc[-1] == "Shooting Star"

def test_entry_quality_bounds():
    df = pd.DataFrame({
        "Open":  np.random.uniform(90, 110, 100),
        "High":  np.random.uniform(110, 120, 100),
        "Low":   np.random.uniform(80, 90, 100),
        "Close": np.random.uniform(90, 110, 100),
        "Volume":np.random.uniform(1000, 5000, 100)
    })
    patterns = detect_patterns(df)
    quality = calculate_entry_quality(df, patterns)
    assert quality.min() >= 0
    assert quality.max() <= 100

def test_no_lookahead_bias():
    df1 = pd.DataFrame({"Open": [105, 94], "High": [106, 110], "Low": [94, 90], "Close": [95, 108], "Volume":[1000, 2000]})
    df1 = pad_df(df1)
    
    # Add a future candle
    df2 = pd.concat([df1, pd.DataFrame({"Open": [108], "High": [112], "Low": [105], "Close": [110], "Volume":[1000]})], ignore_index=True)
    
    pat1 = detect_patterns(df1)
    pat2 = detect_patterns(df2)
    
    # The pattern assigned to the engulfing candle should be identical whether we know the future or not
    assert pat1.iloc[-1] == pat2.iloc[-2]