with open("market_regime.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'df_hist = pd.read_sql("SELECT * FROM regime_history ORDER BY date", conn)',
    'df_hist = pd.read_sql(f"SELECT * FROM regime_history WHERE date <= \'{date_str}\' ORDER BY date", conn)'
)

# Also remove the debug print
import re
content = re.sub(r'\n\s*print\("DEBUG: date=.*?prev_pers=\{prev_persistence\}"\)', '', content)

with open("market_regime.py", "w", encoding="utf-8") as f:
    f.write(content)