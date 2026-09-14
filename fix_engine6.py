with open("engine.py", "r", encoding="utf-8") as f:
    content = f.read()

import re

old_block = """        # ---- FILTER 2: CANDLESTICK ENTRY SETUP ENGINE ----
        frame["Pattern"], frame["EntryPattern"] = detect_patterns(frame)
        frame["Entry_Quality"] = calculate_entry_quality(frame, frame["Pattern"])"""

new_block = """        # ---- FILTER 2: CANDLESTICK ENTRY SETUP ENGINE ----
        frame["Pattern"], frame["EntryPattern"] = detect_patterns(frame)
        frame["Entry_Quality"] = calculate_entry_quality(frame, frame["Pattern"])
        
        trend_aligned = frame["Stage"].isin([1, 2]) & (frame["SMA50Slope20"] >= 0.00) & (frame["Close"] >= 0.98 * frame["SMA50"])
        location_valid = ((frame["Close"] - frame["SMA50"]) / frame["SMA50"]).abs() <= 0.03
        volume_confirmed = frame["VolumeRatio"] >= 1.20
        frame["EntrySetupQualified"] = trend_aligned & location_valid & volume_confirmed"""

content = content.replace(old_block, new_block)

old_latest = '"Pattern", "EntryPattern", "Entry_Quality",'
new_latest = '"Pattern", "EntryPattern", "Entry_Quality", "EntrySetupQualified",'
content = content.replace(old_latest, new_latest)

with open("engine.py", "w", encoding="utf-8") as f:
    f.write(content)