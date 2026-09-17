import sys
import os
import logging
from datetime import datetime

# Allow imports from the parent directory (Nifty terminal root)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import load_universe
from performance_tracker import update_signal_performance
from trading_calendar import is_valid_session, get_previous_sessions
import subprocess

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def main():
    "\""
    Automated CRON execution wrapper for CapitalSense Nifty Terminal.
    Runs daily to update the MFE/MAE performance tracker and rebuild application caches.
    "\""
    logging.info("Starting Daily Production Jobs...")
    
    # 1. Update Performance Tracker
    try:
        logging.info("Loading Universe...")
        universe = load_universe()
        
        # Determine the target session (most recent valid session)
        today = datetime.now().strftime("%Y-%m-%d")
        if is_valid_session(today):
            as_of = today
        else:
            as_of = get_previous_sessions(today, 1)
            
        logging.info(f"Running update_signal_performance for session: {as_of}")
        update_signal_performance(as_of, universe)
        logging.info("Performance tracking updated successfully.")
    except Exception as e:
        logging.error(f"Error in performance tracking: {e}")
        
    # 2. Rebuild Data Cache
    try:
        logging.info("Rebuilding caches (build_cache.py)...")
        cache_script = os.path.join(os.path.dirname(__file__), "build_cache.py")
        if os.path.exists(cache_script):
            subprocess.run([sys.executable, cache_script], check=True)
            logging.info("Cache rebuilt successfully.")
        else:
            logging.warning("build_cache.py not found.")
    except Exception as e:
        logging.error(f"Error rebuilding cache: {e}")

    logging.info("Daily Production Jobs completed.")

if __name__ == "__main__":
    main()
