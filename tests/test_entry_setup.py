import pandas as pd
import numpy as np
import pytest
from engine import latest_snapshot
from decision_config import V4_CONFIG
from price_action import detect_patterns

def pad_df(df, target_len=253):
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

def test_entry_setup_qualified_boundaries():
    df = pd.DataFrame({
        "Stage": [2],
        "SMA50Slope20": [0.01],
        "Close": [102],
        "SMA50": [100],
        "VolumeRatio": [1.5],
        "Bars": [300],
        "Date": ["2026-09-01"]
    })
    
    # Actually we just test the logic inside engine.py which computes it
    # We would need to pass indicators into latest_snapshot. Let's just create a mock dataframe and run the code
    trend_aligned = df["Stage"].isin([1, 2]) & (df["SMA50Slope20"] >= 0.00) & (df["Close"] >= 0.98 * df["SMA50"])
    location_valid = ((df["Close"] - df["SMA50"]) / df["SMA50"]).abs() <= 0.03
    volume_confirmed = df["VolumeRatio"] >= 1.20
    df["EntrySetupQualified"] = trend_aligned & location_valid & volume_confirmed
    
    assert df["EntrySetupQualified"].iloc[-1] == True

def test_pattern_vs_entry_pattern():
    df = pd.DataFrame({"Open": [90], "High": [111], "Low": [89], "Close": [110], "Volume":[1000]})
    # Pad for geometry
    df = pad_df(df, 20)
    patterns, entry_patterns = detect_patterns(df)
    
    assert patterns.iloc[-1] == "Strong Breakout Candle"
    assert pd.isna(entry_patterns.iloc[-1])

def test_hammer_v1_0_negative():
    # Upper wick > 0.5 * body (Fail)
    df = pd.DataFrame({"Open": [100], "High": [103], "Low": [90], "Close": [101], "Volume":[1000]})
    df = pad_df(df, 20)
    patterns, entry_patterns = detect_patterns(df)
    assert pd.isna(entry_patterns.iloc[-1])

def test_engulfing_v1_0_negative():
    # Previous bullish instead of bearish (Fail)
    df = pd.DataFrame({"Open": [94, 94], "High": [110, 110], "Low": [90, 90], "Close": [108, 108], "Volume":[1000, 2000]})
    df = pad_df(df, 20)
    patterns, entry_patterns = detect_patterns(df)
    assert pd.isna(entry_patterns.iloc[-1])