with open("tests/test_entry_setup.py", "r", encoding="utf-8") as f:
    content = f.read()

import re

old_pad = """def pad_df(df, target_len=253):
    # Padding to satisfy HistoryEligible and SMA calculations
    padding = target_len - len(df)
    if padding <= 0: return df
    
    first_row = df.iloc[0:1]
    pad_df = pd.concat([first_row]*padding, ignore_index=True)
    return pd.concat([pad_df, df], ignore_index=True)"""

new_pad = """def pad_df(df, target_len=253):
    np.random.seed(42)
    pad_len = target_len - len(df)
    if pad_len <= 0: return df
    
    pad = pd.DataFrame({
        "Open": np.random.uniform(98, 102, pad_len),
        "High": np.random.uniform(102, 105, pad_len),
        "Low": np.random.uniform(95, 98, pad_len),
        "Close": np.random.uniform(98, 102, pad_len),
        "Volume": 1000
    })
    return pd.concat([pad, df], ignore_index=True)"""

content = content.replace(old_pad, new_pad)

with open("tests/test_entry_setup.py", "w", encoding="utf-8") as f:
    f.write(content)