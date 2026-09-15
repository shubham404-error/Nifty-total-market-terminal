with open("market_regime.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('prev_regime = str(df_hist["regime"].iloc[-2])', 'prev_regime = str(df_hist["regime"].iloc[-2])\n        print(f"DEBUG: date={date_str}, iloc[-2]={df_hist.index[-2]}, prev_reg={prev_regime}, prev_pers={prev_persistence}")')

with open("market_regime.py", "w", encoding="utf-8") as f:
    f.write(content)