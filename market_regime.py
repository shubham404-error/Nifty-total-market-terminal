import os
import sqlite3
import pandas as pd
from datetime import datetime
from decision_config import V4_CONFIG
from trading_calendar import is_valid_session

DB_PATH = "data/signal_ledger.sqlite"

def init_regime_db():
    os.makedirs("data", exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS regime_history (
                date TEXT PRIMARY KEY,
                breadth_daily REAL,
                breadth_20 REAL,
                breadth_trend TEXT,
                stage_2_pct REAL,
                stage_4_pct REAL,
                structural_health REAL,
                index_stage INTEGER,
                regime TEXT,
                crisis_persistence INTEGER
            )
        """)

def update_market_regime(date_str: str, snapshot_df: pd.DataFrame, index_stage: int) -> dict:
    init_regime_db()
    
    if not is_valid_session(date_str):
        # Return previous state without updating persistence
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            df_hist = pd.read_sql("SELECT * FROM regime_history ORDER BY date DESC LIMIT 1", conn)
        if not df_hist.empty:
            last = df_hist.iloc[0]
            return {
                "Regime": last["regime"],
                "Breadth20": last["breadth_20"],
                "BreadthTrend": last["breadth_trend"],
                "StructuralHealth": last["structural_health"],
                "IndexStage": last["index_stage"],
                "CrisisPersistence": last["crisis_persistence"]
            }
        else:
            return {"Regime": "NEUTRAL", "Breadth20": 0.0, "BreadthTrend": "Flat", "StructuralHealth": 0.0, "IndexStage": index_stage, "CrisisPersistence": 0}

    
    # BreadthDaily_t
    eligible = snapshot_df[snapshot_df["HistoryEligible"] == True]
    if len(eligible) > 0:
        above_200 = len(eligible[eligible["Close"] > eligible["SMA200"]])
        breadth_daily = above_200 / len(eligible)
        
        stage_2_pct = len(eligible[eligible["Stage"] == 2]) / len(eligible)
        stage_4_pct = len(eligible[eligible["Stage"] == 4]) / len(eligible)
    else:
        breadth_daily = 0.0
        stage_2_pct = 0.0
        stage_4_pct = 0.0
        
    structural_health = stage_2_pct - stage_4_pct
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        df_hist = pd.read_sql(f"SELECT * FROM regime_history WHERE date <= '{date_str}' ORDER BY date", conn)
        
    if not df_hist.empty:
        df_hist["date"] = pd.to_datetime(df_hist["date"])
        df_hist.set_index("date", inplace=True)
        # append today
        df_hist.loc[pd.to_datetime(date_str)] = {
            "breadth_daily": breadth_daily,
            "structural_health": structural_health,
            "index_stage": index_stage
        }
    else:
        df_hist = pd.DataFrame({
            "breadth_daily": [breadth_daily],
            "structural_health": [structural_health],
            "index_stage": [index_stage]
        }, index=[pd.to_datetime(date_str)])
        
    df_hist["breadth_20"] = df_hist["breadth_daily"].ewm(span=20, adjust=False).mean()
    breadth_20 = float(df_hist["breadth_20"].iloc[-1])
    
    lookback = V4_CONFIG["BREADTH_TREND_LOOKBACK"]
    thresh = V4_CONFIG["BREADTH_TREND_CHANGE_THRESHOLD"]
    
    if len(df_hist) >= lookback + 1:
        b_now = df_hist["breadth_20"].iloc[-1]
        b_prev = df_hist["breadth_20"].iloc[-(lookback + 1)]
        if b_now > b_prev + thresh:
            breadth_trend = "Rising"
        elif b_now < b_prev - thresh:
            breadth_trend = "Falling"
        else:
            breadth_trend = "Flat"
    else:
        breadth_trend = "Flat"
        
    # Previous crisis persistence
    if len(df_hist) > 1 and "crisis_persistence" in df_hist.columns:
        prev_persistence = int(df_hist["crisis_persistence"].iloc[-2]) if not pd.isna(df_hist["crisis_persistence"].iloc[-2]) else 0
        prev_regime = str(df_hist["regime"].iloc[-2])
    else:
        prev_persistence = 0
        prev_regime = "NEUTRAL"
        
    # Crisis condition
    crisis_condition = (index_stage == 4) and (breadth_20 < V4_CONFIG["BREADTH_CRISIS_THRESHOLD"])
    
    if crisis_condition:
        curr_persistence = prev_persistence + 1
    else:
        if prev_regime == "CRISIS":
            curr_persistence = prev_persistence - 1
        else:
            curr_persistence = 0
            
    if prev_regime == "CRISIS" and curr_persistence > (V4_CONFIG["CRISIS_PERSISTENCE"] - V4_CONFIG["CRISIS_EXIT_PERSISTENCE"]):
        regime = "CRISIS"
        curr_persistence = min(curr_persistence, V4_CONFIG["CRISIS_PERSISTENCE"])
    elif curr_persistence >= V4_CONFIG["CRISIS_PERSISTENCE"]:
        regime = "CRISIS"
        curr_persistence = V4_CONFIG["CRISIS_PERSISTENCE"]
    elif index_stage == 4 or breadth_20 < V4_CONFIG["BREADTH_DEFENSIVE_THRESHOLD"] or structural_health <= 0:
        regime = "DEFENSIVE"
    elif index_stage in {1, 2} and breadth_20 >= V4_CONFIG["BREADTH_BULLISH_THRESHOLD"] and structural_health > 0:
        regime = "BULLISH"
    else:
        regime = "NEUTRAL" 

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT OR REPLACE INTO regime_history 
            (date, breadth_daily, breadth_20, breadth_trend, stage_2_pct, stage_4_pct, structural_health, index_stage, regime, crisis_persistence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (date_str, breadth_daily, breadth_20, breadth_trend, stage_2_pct, stage_4_pct, structural_health, index_stage, regime, curr_persistence))
        
    return {
        "Regime": regime,
        "Breadth20": breadth_20,
        "BreadthTrend": breadth_trend,
        "StructuralHealth": structural_health,
        "IndexStage": index_stage,
        "CrisisPersistence": curr_persistence
    }