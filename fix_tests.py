with open("tests/test_price_action.py", "r", encoding="utf-8") as f:
    content = f.read()

import re

# Fix detect_patterns call
content = content.replace("detect_patterns(pad_df(df))", "detect_patterns(pad_df(df))[0]")
content = content.replace("patterns = detect_patterns(df)", "patterns = detect_patterns(df)[0]")
content = content.replace("pat1 = detect_patterns(df1)[0]", "pat1 = detect_patterns(df1)[0]") # in case it was already replaced
content = content.replace("pat1 = detect_patterns(df1)", "pat1 = detect_patterns(df1)[0]")
content = content.replace("pat2 = detect_patterns(df2)", "pat2 = detect_patterns(df2)[0]")

# Fix Hammer fixture to have upper_wick <= 0.5 * body
# Open=100, High=101.5, Low=90, Close=101. body=1, upper_wick=0.5
content = content.replace('"High": [102]', '"High": [101.5]')

with open("tests/test_price_action.py", "w", encoding="utf-8") as f:
    f.write(content)