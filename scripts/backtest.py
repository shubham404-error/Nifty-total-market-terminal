import os
import sys
import json
import pandas as pd
import logging
from datetime import timedelta

# Add parent dir to path so we can import engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_backtest():
    cache_file = "cache.parquet"
    if not os.path.exists(cache_file):
        logging.error(f"Cache file {cache_file} not found. Run build_cache.py first.")
        return

    logging.info("Loading cache...")
    prices = pd.read_parquet(cache_file)
    
    logging.info("Calculating technical indicators for the entire history...")
    indicators = engine.calculate_indicators(prices)
    
    # We will iterate through history. This can be slow, but it's offline.
    # To avoid looping every day, we can filter for days where signals were active.
    logging.info("Running backtest evaluations...")
    
    # Instead of running `latest_snapshot` per day (which is extremely slow in python),
    # we can use the vectorized indicator boolean flags from `calculate_indicators`.
    
    # Define the core setup conditions similar to `convergence_table`
    # df already has: Pullback, Breakout20, BullRegime, BullSwing, BullMomentum, MomentumFresh, SwingFresh, VolumeConfirmedMomentum
    
    # We need to map future returns. Since `prices` has all dates for all symbols, we can calculate forward returns.
    
    # Shift prices backwards to get future prices
    # Note: the dataframe is sorted by 'Yahoo Symbol' and 'Date' if we do groupby.
    # Let's add forward returns:
    
    def add_forward_returns(df):
        # 1W = ~5 trading days, 1M = ~21, 3M = ~63, 6M = ~126, 1Y = ~252
        df = df.sort_values(['Yahoo Symbol', 'Date']).copy()
        for days, label in [(5, '1W'), (21, '1M'), (63, '3M'), (126, '6M'), (252, '1Y')]:
            df[f'Fwd_{label}'] = df.groupby('Yahoo Symbol')['Close'].shift(-days)
            df[f'Ret_{label}'] = (df[f'Fwd_{label}'] / df['Close'] - 1) * 100
        return df

    indicators = add_forward_returns(indicators)
    
    results = {}
    
    # Helper to evaluate a mask
    def eval_strategy(mask, name):
        signals = indicators[mask]
        total_signals = len(signals)
        logging.info(f"Strategy {name}: {total_signals} signals found.")
        
        if total_signals == 0:
            return {"Count": 0}
            
        stats = {"Count": total_signals}
        for label in ['1W', '1M', '3M', '6M', '1Y']:
            col = f'Ret_{label}'
            valid = signals[col].dropna()
            if len(valid) > 0:
                stats[f"Avg_Ret_{label}"] = round(valid.mean(), 2)
                stats[f"WinRate_{label}"] = round((valid > 0).mean() * 100, 2)
                stats[f"Median_{label}"] = round(valid.median(), 2)
        return stats

    # Strategy 1: Pullback in Bull Regime
    pullback_mask = (indicators["Pullback"] == True) & (indicators["BullRegime"] == True) & (indicators["BullSwing"] == True)
    results["Pullback"] = eval_strategy(pullback_mask, "Pullback")
    
    # Strategy 2: Volume Breakout
    breakout_mask = (indicators["Breakout20"] == True) & (indicators["BullRegime"] == True)
    results["Breakout"] = eval_strategy(breakout_mask, "Breakout")
    
    # Strategy 3: Fresh Momentum
    momentum_mask = (indicators["MomentumFresh"] == True) & (indicators["BullMomentum"] == True) & ((indicators["BullRegime"] == True) | (indicators["BullSwing"] == True))
    results["Fresh Momentum"] = eval_strategy(momentum_mask, "Fresh Momentum")
    
    # Strategy 4: Trend Continuation
    trend_mask = (indicators["BullRegime"] == True) & (indicators["BullSwing"] == True) & (indicators["BullMomentum"] == True) & (indicators["VolumeConfirmedMomentum"] == True) & (indicators["Breakout20"] == False)
    results["Trend Continuation"] = eval_strategy(trend_mask, "Trend Continuation")

    output_file = "backtest_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=4)
        
    logging.info(f"Saved backtest results to {output_file}")

if __name__ == "__main__":
    run_backtest()
