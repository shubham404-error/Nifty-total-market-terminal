with open("engine.py", "r", encoding="utf-8") as f:
    content = f.read()

import re

old_block = """    # Cross-sectional relative strength percentiles. Rank only observations
    # with sufficient history for that horizon, so missing data is not treated
    # as weak performance.
    for label, periods in RS_PERIODS.items():
        ret_col = f"Return{label}"
        eligible = snapshot["Bars"] >= periods + 1
        snapshot[f"RS{label}Pct"] = pd.NA
        snapshot.loc[eligible, f"RS{label}Pct"] = (
            snapshot.loc[eligible, ret_col].rank(pct=True, method="average") * 100
        )"""

new_block = """    # Cross-sectional relative strength percentiles. Rank only observations
    # with sufficient history for that horizon, so missing data is not treated
    # as weak performance.
    for label, periods in RS_PERIODS.items():
        ret_col = f"Return{label}"
        eligible = snapshot["Bars"] >= periods + 1
        snapshot[f"RS{label}Pct"] = pd.NA
        snapshot.loc[eligible, f"RS{label}Pct"] = (
            snapshot.loc[eligible, ret_col].rank(pct=True, method="average") * 100
        )
        
    from stage_rs import scale_rs_ratings
    eligible_rs = snapshot["Bars"] >= max(RS_PERIODS.values()) + 1
    snapshot["RS_Rating"] = pd.NA
    snapshot.loc[eligible_rs, "RS_Rating"] = scale_rs_ratings(snapshot.loc[eligible_rs, "Raw_RS_Rating"])"""

content = content.replace(old_block, new_block)

with open("engine.py", "w", encoding="utf-8") as f:
    f.write(content)