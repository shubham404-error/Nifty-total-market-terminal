import os
import sys
import pandas as pd
import logging

# Add parent dir to path so we can import engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def build_cache():
    logging.info("Loading universe: NIFTY TOTAL MARKET")
    universe = engine.load_universe("NIFTY TOTAL MARKET")
    
    logging.info(f"Downloading prices for {len(universe)} symbols...")
    # Use 5 years as specified in TDD 5. Infrastructure
    prices, failures = engine.download_prices(universe, years=5, batch_size=50)
    
    if failures:
        logging.warning(f"Failed to download prices for {len(failures)} symbols: {failures}")
    
    logging.info(f"Downloaded {len(prices)} rows of OHLCV data.")
    
    output_file = "cache.parquet"
    prices.to_parquet(output_file, index=False)
    logging.info(f"Saved cache to {output_file} (Size: {os.path.getsize(output_file) / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    build_cache()
