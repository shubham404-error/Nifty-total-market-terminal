with open("price_action.py", "r", encoding="utf-8") as f:
    content = f.read()

import re

# Replace Hammer logic
old_hammer = """    # 1. Hammer: Reversal. Lower wick >> body. close_loc > 0.5
    is_hammer = (df['close_loc'] > 0.5) & (body < (df['Open'] - df['Low']).abs() * 0.5) & (df['range_atr_ratio'] > 0.8)"""

new_hammer = """    # 1. Hammer: Reversal. Lower wick >> body. close_loc > 0.5
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
    )"""

content = content.replace(old_hammer, new_hammer)

# Replace Bullish Engulfing logic
old_bull = """    # 2. Bullish Engulfing: C > O1, O < C1, C1 < O1
    is_bull_engulf = (C1 < O1) & (df['Close'] > O1) & (df['Open'] < C1) & (df['range_atr_ratio'] > 1.0)"""

new_bull = """    # 2. Bullish Engulfing: C > O1, O < C1, C1 < O1
    prev_bearish = C1 < O1
    current_bullish = df['Close'] > df['Open']
    real_body_engulfs = (df['Open'] <= C1) & (df['Close'] >= O1)
    body_strength = body >= 1.00 * (C1 - O1).abs()
    
    is_bull_engulf = (
        prev_bearish
        & current_bullish
        & real_body_engulfs
        & body_strength
    )"""

content = content.replace(old_bull, new_bull)

# Add EntryPattern column return
old_return = "    return pd.Series(patterns, index=df.index)"
new_return = """    entry_patterns = np.where(is_hammer, "Hammer", np.where(is_bull_engulf, "Bullish Engulfing", None))
    return pd.Series(patterns, index=df.index), pd.Series(entry_patterns, index=df.index)"""

content = content.replace(old_return, new_return)

with open("price_action.py", "w", encoding="utf-8") as f:
    f.write(content)