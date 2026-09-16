with open("engine.py", "r", encoding="utf-8") as f:
    content = f.read()

# Remove the bottom chunk
to_remove = """from stage_rs import calculate_stage, calculate_mansfield_rs
from price_action import detect_patterns, calculate_entry_quality, compute_geometry
def historical_snapshot(indicators: pd.DataFrame, universe: pd.DataFrame, as_of_session: str, n_sessions_ago: int, ema_long: int = 255, rsi_period: int = 14) -> pd.DataFrame:
    from trading_calendar import get_previous_sessions
    target_session = get_previous_sessions(as_of_session, n_sessions_ago).strftime("%Y-%m-%d")
    return latest_snapshot(indicators, universe, ema_long, rsi_period, target_session)"""

if to_remove in content:
    content = content.replace(to_remove, "")
else:
    print("Could not find exact chunk to remove")

# Add it just before get_fundamental_data
to_add = """
def historical_snapshot(indicators: pd.DataFrame, universe: pd.DataFrame, as_of_session: str, n_sessions_ago: int, ema_long: int = 255, rsi_period: int = 14) -> pd.DataFrame:
    from trading_calendar import get_previous_sessions
    target_session = get_previous_sessions(as_of_session, n_sessions_ago).strftime("%Y-%m-%d")
    return latest_snapshot(indicators, universe, ema_long, rsi_period, target_session)

@st.cache_data(ttl=3600*24)
def get_fundamental_data"""

if "@st.cache_data(ttl=3600*24)\ndef get_fundamental_data" in content:
    content = content.replace("@st.cache_data(ttl=3600*24)\ndef get_fundamental_data", to_add)

with open("engine.py", "w", encoding="utf-8") as f:
    f.write(content)