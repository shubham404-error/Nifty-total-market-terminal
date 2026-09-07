import os
import sys
import time
import pandas as pd
import yfinance as yf
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_momentum_score(hist):
    if len(hist) < 50:
        return 50 # Neutral if not enough history
        
    close = hist['Close']
    
    # Simple SMA 20/50
    sma20 = close.rolling(20).mean().iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1]
    trend_score = 100 if sma20 > sma50 else 0
    
    # Simple RSI (using engine's rsi_wilder if available, or just a basic one)
    try:
        rsi_series = engine.rsi_wilder(close, 14)
        rsi = rsi_series.iloc[-1]
    except Exception:
        rsi = 50
        
    if pd.isna(rsi):
        rsi = 50
        
    rsi_score = 100 if rsi > 50 else 0 # binary for simplicity in this offline script
    
    # 50/50 weight for trend and rsi
    return (trend_score * 0.5) + (rsi_score * 0.5)

def fetch_dvm_for_ticker(ticker_symbol):
    try:
        t = yf.Ticker(ticker_symbol)
        info = t.info or {}
        
        # Determine history length
        hist = t.history(period="1y")
        trading_days = len(hist)
        is_newly_listed = trading_days < 252
        
        # 1. Momentum Score
        mom_score = calculate_momentum_score(hist)
        
        if is_newly_listed:
            return {
                "Yahoo Symbol": ticker_symbol,
                "Momentum Score": mom_score,
                "Valuation Score": None,
                "Durability Score": None,
                "DVM Score": mom_score, # Strictly on Momentum
                "is_newly_listed": True,
                "valuation_confidence": "N/A",
                "durability_confidence": "N/A"
            }
            
        # 2. Valuation Score (Fallback Hierarchy)
        val_score = 50
        val_conf = "Low"
        
        trailing_pe = info.get("trailingPE")
        forward_pe = info.get("forwardPE")
        pb_ratio = info.get("priceToBook")
        
        if trailing_pe is not None:
            val_score = 100 if trailing_pe < 25 else 40
            val_conf = "High"
        elif forward_pe is not None:
            val_score = 100 if forward_pe < 25 else 40
            val_conf = "Medium"
        elif pb_ratio is not None:
            val_score = 100 if pb_ratio < 3 else 40
            val_conf = "Medium"
            
        # 3. Durability Score (Require 2 of 3)
        dur_score = 50
        dur_conf = "Low"
        
        profit_margin = info.get("profitMargins")
        roe = info.get("returnOnEquity")
        rev_growth = info.get("revenueGrowth")
        
        valid_metrics = sum(x is not None for x in [profit_margin, roe, rev_growth])
        if valid_metrics >= 2:
            dur_conf = "High"
            # Simple average if available, mapped to 0-100
            score = 0
            if profit_margin is not None and profit_margin > 0.1: score += 100
            if roe is not None and roe > 0.15: score += 100
            if rev_growth is not None and rev_growth > 0.1: score += 100
            dur_score = score / max(valid_metrics, 1)

        # Final DVM = 40% Mom + 30% Val + 30% Dur
        final_dvm = (mom_score * 0.4) + (val_score * 0.3) + (dur_score * 0.3)
        
        return {
            "Yahoo Symbol": ticker_symbol,
            "Momentum Score": mom_score,
            "Valuation Score": val_score,
            "Durability Score": dur_score,
            "DVM Score": final_dvm,
            "is_newly_listed": False,
            "valuation_confidence": val_conf,
            "durability_confidence": dur_conf
        }
    except Exception as e:
        logging.warning(f"Failed to fetch DVM for {ticker_symbol}: {e}")
        return {
            "Yahoo Symbol": ticker_symbol,
            "Momentum Score": 50,
            "Valuation Score": 50,
            "Durability Score": 50,
            "DVM Score": 50,
            "is_newly_listed": False,
            "valuation_confidence": "Low",
            "durability_confidence": "Low"
        }

def build_dvm_cache():
    logging.info("Loading universe for DVM Cache")
    universe = engine.load_universe("NIFTY TOTAL MARKET")
    tickers = universe["Yahoo Symbol"].tolist()
    
    results = []
    batch_size = 50
    
    # ONLY FETCHING 10 FOR NOW TO SAVE TIME/API LIMITS IN THE TEST RUN. 
    # IN PRODUCTION GITHUB ACTION IT WILL RUN ALL.
    is_github_action = os.environ.get("GITHUB_ACTIONS") == "true"
    if not is_github_action:
        logging.info("Running locally - truncating to 10 tickers for speed.")
        tickers = tickers[:10]

    for idx in range(0, len(tickers), batch_size):
        batch = tickers[idx:idx+batch_size]
        logging.info(f"Processing batch {idx//batch_size + 1}")
        
        for ticker in batch:
            res = fetch_dvm_for_ticker(ticker)
            results.append(res)
            
        time.sleep(2) # Prevent IP bans
        
    df = pd.DataFrame(results)
    
    output_file = "dvm_scores.parquet"
    df.to_parquet(output_file, index=False)
    logging.info(f"Saved DVM cache to {output_file}")

if __name__ == "__main__":
    build_dvm_cache()
