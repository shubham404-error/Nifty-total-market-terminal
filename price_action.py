from decision_config import V4_CONFIG
import pandas as pd
import numpy as np

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, window=14) -> pd.Series:
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=window).mean()

def compute_geometry(df: pd.DataFrame) -> pd.DataFrame:
    atr14 = calculate_atr(df['High'], df['Low'], df['Close'], 14)
    df['atr14'] = atr14
    
    # Avoid division by zero
    hl_range = (df['High'] - df['Low']).replace(0, np.nan)
    atr_nonzero = atr14.replace(0, np.nan)
    
    df['range_atr_ratio'] = (df['High'] - df['Low']) / atr_nonzero
    df['body_atr_ratio'] = (df['Close'] - df['Open']).abs() / atr_nonzero
    df['close_loc'] = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / hl_range
    
    return df

def detect_patterns(df: pd.DataFrame) -> pd.Series:
    # Compute basic geometry if not present
    if 'close_loc' not in df.columns:
        df = compute_geometry(df)
        
    patterns = pd.Series("None", index=df.index)
    
    # Pre-compute some shifts
    C1, O1, H1, L1 = df['Close'].shift(1), df['Open'].shift(1), df['High'].shift(1), df['Low'].shift(1)
    C2, O2, H2, L2 = df['Close'].shift(2), df['Open'].shift(2), df['High'].shift(2), df['Low'].shift(2)
    
    body = (df['Close'] - df['Open']).abs()
    body1 = (C1 - O1).abs()
    
    # 1. Hammer: Reversal. Lower wick >> body. close_loc > 0.5
    EPS = 1e-8
    candle_range = df['High'] - df['Low']
    lower_wick = df[['Open', 'Close']].min(axis=1) - df['Low']
    upper_wick = df['High'] - df[['Open', 'Close']].max(axis=1)
    
    is_hammer = (
        (candle_range > 0)
        & (body / candle_range <= 0.35)
        & (lower_wick >= 2.0 * np.maximum(body, EPS))
        & (upper_wick <= 0.50 * np.maximum(body, EPS))
        & (df['Close'] >= df['Low'] + 0.60 * candle_range)
    )
    
    # 2. Bullish Engulfing: C > O1, O < C1, C1 < O1
    prev_bearish = C1 < O1
    current_bullish = df['Close'] > df['Open']
    real_body_engulfs = (df['Open'] <= C1) & (df['Close'] >= O1)
    body_strength = body >= 1.00 * (C1 - O1).abs()
    
    is_bull_engulf = (
        prev_bearish
        & current_bullish
        & real_body_engulfs
        & body_strength
    )
    
    # 3. Harami: Inside bar
    is_harami = (df['High'] < H1) & (df['Low'] > L1) & (df['range_atr_ratio'] < 0.8)
    
    # 4. Inverted Hammer: close_loc < -0.5, but upper wick >> body, after downtrend (simplified)
    is_inv_hammer = (df['close_loc'] < -0.5) & (body < (df['High'] - df['Close']).abs() * 0.5) & (df['range_atr_ratio'] > 0.8)
    
    # 5. Morning Star: C2<O2, small body1, C>O and C > (O2+C2)/2
    is_morning_star = (C2 < O2) & (body1 < body * 0.5) & (df['Close'] > df['Open']) & (df['Close'] > (O2 + C2)/2)
    
    # 6. Inside Bar Breakout: H > H1, previous was inside bar
    prev_inside = (H1 < H2) & (L1 > L2)
    is_inside_bo = prev_inside & (df['Close'] > H1)
    
    # 7. Strong Breakout Candle: large body, closing near high
    is_strong_bo = (df['body_atr_ratio'] > 1.2) & (df['close_loc'] > 0.7) & (df['Close'] > df['Open'])
    
    # 8. Bearish Engulfing
    is_bear_engulf = (C1 > O1) & (df['Close'] < O1) & (df['Open'] > C1) & (df['range_atr_ratio'] > 1.0)
    
    # 9. Shooting Star
    is_shooting_star = (df['close_loc'] < -0.5) & (body < (df['High'] - df['Open']).abs() * 0.5) & (df['range_atr_ratio'] > 0.8) & (df['Close'] < df['Open'])

    # Priority assignment
    patterns = np.where(is_strong_bo, "Strong Breakout Candle", patterns)
    patterns = np.where(is_inside_bo, "Inside Bar Breakout", patterns)
    patterns = np.where(is_morning_star, "Morning Star", patterns)
    patterns = np.where(is_bull_engulf, "Bullish Engulfing", patterns)
    patterns = np.where(is_hammer, "Hammer", patterns)
    patterns = np.where(is_inv_hammer, "Inverted Hammer", patterns)
    patterns = np.where(is_harami, "Harami", patterns)
    patterns = np.where(is_bear_engulf, "Bearish Engulfing", patterns)
    patterns = np.where(is_shooting_star, "Shooting Star", patterns)
    
    entry_patterns = np.where(is_hammer, "Hammer", np.where(is_bull_engulf, "Bullish Engulfing", None))
    return pd.Series(patterns, index=df.index), pd.Series(entry_patterns, index=df.index)

def calculate_entry_quality(df: pd.DataFrame, pattern_series: pd.Series) -> pd.Series:
    score = pd.Series(0.0, index=df.index)
    
    # Pattern Geometry (25%): 25 for strong bullish, 15 for moderate, 0 for bearish
    geom_score = pd.Series(0.0, index=df.index)
    geom_score[pattern_series.isin(["Strong Breakout Candle", "Bullish Engulfing", "Morning Star"])] = 25
    geom_score[pattern_series.isin(["Hammer", "Inside Bar Breakout", "Inverted Hammer"])] = 15
    geom_score[pattern_series.isin(["Harami"])] = 10
    
    # Location (20%): Proximity to structural support levels
    ema21 = df['Close'].ewm(span=21).mean()
    sma50 = df['Close'].rolling(50).mean()
    sma200 = df['Close'].rolling(200).mean()
    
    dist_21 = ((df['Close'] - ema21) / df['Close']).abs()
    dist_50 = ((df['Close'] - sma50) / df['Close']).abs()
    dist_200 = ((df['Close'] - sma200) / df['Close']).abs()
    
    nearest_support_dist = pd.concat([dist_21, dist_50, dist_200], axis=1).min(axis=1)
    loc_score = (1 - (nearest_support_dist / 0.05).clip(0, 1)) * 20
    
    # Trend Alignment (15%):
    sma50 = df['Close'].rolling(50).mean()
    trend_score = np.where(df['Close'] > sma50, 15, 0)
    
    # Volume (10%):
    vol_sma20 = df['Volume'].rolling(20).mean()
    vol_score = np.where(df['Volume'] > vol_sma20 * V4_CONFIG["VOLUME_RVOL_MIN"], 10, np.where(df['Volume'] > vol_sma20, 5, 0))
    
    # Momentum (10%):
    mom_score = np.where(df['Close'] > df['Close'].shift(5), 10, 0)
    
    # Relative Strength (5%):
    if 'RS_Rating' in df.columns:
        rs_score = (df['RS_Rating'].fillna(50) / 100 * 5).clip(0, 5)
    else:
        ret5 = df['Close'].pct_change(5)
        rs_score = np.where(ret5 > 0.02, 5, np.where(ret5 > 0, 3, 0))
    
    # Volatility (5%):
    volatility_score = np.where(df['range_atr_ratio'] > 1.0, 5, 0)
    
    # Confirmation (5%):
    next_close = df['Close'].shift(-1)
    pattern_high = df['High']
    conf_score = np.where(next_close > pattern_high, 5, 0)
    if len(conf_score) > 0:
        conf_score[-1] = 0
    
    # Liquidity (5%):
    liq_score = np.where(df['Volume'] * df['Close'] > V4_CONFIG["LIQUIDITY_THRESHOLD"], 5, 0) # 1Cr turnover
    
    total_score = geom_score + loc_score + trend_score + vol_score + mom_score + rs_score + volatility_score + conf_score + liq_score
    
    return total_score.clip(0, 100)