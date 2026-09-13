import pandas as pd
import numpy as np

def calculate_mansfield_rs(stock_close: pd.Series, bench_close: pd.Series) -> pd.Series:
    rp = (stock_close / bench_close) * 100
    sma200 = rp.rolling(window=200).mean()
    mrs = ((rp / sma200) - 1) * 100
    return mrs

def calculate_rs_rating(stock_close: pd.Series, universe_data: dict, current_date) -> dict:
    # Requires stock_close to have 252 days of history
    if len(stock_close) < 252:
        return {"rs_rating": None, "insufficient_data": True}
        
    def get_return(series, periods):
        if len(series) <= periods: return 0
        return (series.iloc[-1] / series.iloc[-1 - periods]) - 1

    r63 = get_return(stock_close, 63)
    r126 = get_return(stock_close, 126)
    r189 = get_return(stock_close, 189)
    r252 = get_return(stock_close, 252)
    
    raw_score = 0.40 * r63 + 0.20 * r126 + 0.20 * r189 + 0.20 * r252
    return {"raw_score": raw_score, "insufficient_data": False}

def scale_rs_ratings(cross_sectional_scores: pd.Series) -> pd.Series:
    # Scale raw scores to 1-99 percentile cross-sectionally
    if cross_sectional_scores.dropna().empty:
        return cross_sectional_scores
    ranks = cross_sectional_scores.rank(pct=True)
    scaled = (ranks * 98) + 1
    return scaled.clip(1, 99).round(0)

def calculate_stage(close: pd.Series) -> pd.DataFrame:
    sma150 = close.rolling(window=150).mean()
    sma150_10d_ago = sma150.shift(10)
    
    slope_pct = (sma150 - sma150_10d_ago) / sma150_10d_ago * 100
    high50 = close.rolling(window=50).max()
    
    is_rising = slope_pct > 0.5
    is_falling = slope_pct < -0.5
    
    is_stage2 = (close > sma150) & is_rising & (close > high50.shift(1))
    is_stage4 = (close < sma150) & is_falling
    
    stages = pd.Series(index=close.index, dtype=float)
    
    # Walk-forward classification
    last_confirmed = None
    
    for i in range(len(close)):
        if pd.isna(sma150.iloc[i]):
            stages.iloc[i] = np.nan
            continue
            
        if is_stage2.iloc[i]:
            stages.iloc[i] = 2
            last_confirmed = 2
        elif is_stage4.iloc[i]:
            stages.iloc[i] = 4
            last_confirmed = 4
        else:
            if last_confirmed == 4:
                stages.iloc[i] = 1
            elif last_confirmed == 2:
                stages.iloc[i] = 3
            else:
                stages.iloc[i] = 0 # Undefined early state
                
    return pd.DataFrame({
        'stage': stages,
        'sma150': sma150,
        'slope_pct': slope_pct
    })