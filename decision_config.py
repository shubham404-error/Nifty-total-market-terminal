# decision_config.py

V4_CONFIG = {
    "CONFIG_VERSION": "DecisionEngine_v4.1",

    # Data Quality
    "MIN_HISTORY_BARS": 252,

    # Leadership
    "RS_RATING_MIN": 70,

    # Entry Setup
    "LOCATION_MAX_DISTANCE_50SMA": 0.03,     # 3% — research default
    "VOLUME_RVOL_MIN": 1.20,                 # 1.20x — research default
    "TREND_SMA50_SLOPE_LOOKBACK": 20,
    "TREND_SMA50_SLOPE_MIN": 0.00,
    "TREND_CLOSE_VS_SMA50_MIN": 0.98,        # Close >= 0.98 * SMA50

    # Market Regime
    "BREADTH_DEFENSIVE_THRESHOLD": 0.35,
    "BREADTH_CRISIS_THRESHOLD": 0.15,
    "BREADTH_BULLISH_THRESHOLD": 0.60,
    "CRISIS_PERSISTENCE": 3,                  # valid trading sessions
    "CRISIS_EXIT_PERSISTENCE": 2,
    "BREADTH_TREND_LOOKBACK": 5,
    "BREADTH_TREND_CHANGE_THRESHOLD": 0.02,

    # Confluence (verify against existing ConvergenceScore scale)
    "CONFLUENCE_STANDARD": 60,
    "CONFLUENCE_DEFENSIVE": 70,

    # Patterns
    "PATTERN_VERSIONS": {
        "Hammer": "Hammer_v1.0",
        "Bullish Engulfing": "BullishEngulfing_v1.0",
    },
    "VALID_ENTRY_PATTERNS": {"Hammer", "Bullish Engulfing"},

    # Execution
    "EXECUTION_CONVENTION": "T+1_OPEN",

    # Decay
    "RS_DECAY_THRESHOLD": 15,   # RS drop of 15+ points triggers LEADERSHIP group
    "MOMENTUM_FLOOR_LOOKBACK": 20,

    # EPS guard for candle geometry division
    "CANDLE_EPS": 1e-8,
}