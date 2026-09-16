with open("performance_tracker.py", "r", encoding="utf-8") as f:
    content = f.read()

import re
content = re.sub(
    r'updates_ledger\.append\(\(entry_price, status, sig_id\)\).*?updates_ledger\.append\(\(entry_price, "CLOSED", close_reason, sig_id\)\)',
    '''updates_ledger[sig_id] = {"EntryPrice": entry_price, "Status": status}
            else:
                continue
                
        if status != "ACTIVE" or pd.isna(entry_price):
            continue
            
        post_entry = sym_prices.loc[entry_date:as_of_session]
        if post_entry.empty:
            continue
            
        current_price = post_entry.iloc[-1]["Close"]
        highest_high = post_entry["High"].max()
        lowest_low = post_entry["Low"].min()
        
        ret = (current_price - entry_price) / entry_price if entry_price else 0
        mfe = (highest_high - entry_price) / entry_price if entry_price else 0
        mae = (lowest_low - entry_price) / entry_price if entry_price else 0
        
        days_held = max(0, len(sessions_between(entry_date, as_of_session)) - 1)
        
        nifty_ret = None
        if entry_date in nifty_prices.index and as_of_session in nifty_prices.index:
            nifty_entry = nifty_prices.loc[entry_date, "Close"]
            nifty_curr = nifty_prices.loc[as_of_session, "Close"]
            nifty_ret = (nifty_curr - nifty_entry) / nifty_entry if nifty_entry else 0
            
        updates_perf.append((sig_id, entry_price, current_price, ret, mfe, mae, days_held, nifty_ret))
        
        decay_state = sig.get("DecayState", "INTACT")
        if decay_state == "THESIS_BROKEN" or days_held >= 65:
            close_reason = "THESIS_BROKEN" if decay_state == "THESIS_BROKEN" else "TIME_STOP_65"
            if sig_id not in updates_ledger:
                updates_ledger[sig_id] = {}
            updates_ledger[sig_id].update({"Status": "CLOSED", "CloseReason": close_reason})''',
    content, flags=re.DOTALL
)
content = content.replace("updates_ledger = []", "updates_ledger = {}")

content = content.replace("""                for upd in updates_ledger:
                    if len(upd) == 3: # (entry_price, status, sig_id)
                        conn.execute("UPDATE signal_ledger SET EntryPrice = ?, Status = ? WHERE SignalID = ?", upd)
                    elif len(upd) == 4: # (entry_price, status, close_reason, sig_id)
                        conn.execute("UPDATE signal_ledger SET EntryPrice = ?, Status = ?, CloseReason = ? WHERE SignalID = ?", upd)""", 
"""                for sig_id, fields in updates_ledger.items():
                    set_clause = ", ".join([f"{k} = ?" for k in fields.keys()])
                    values = list(fields.values()) + [sig_id]
                    conn.execute(f"UPDATE signal_ledger SET {set_clause} WHERE SignalID = ?", values)""")

with open("performance_tracker.py", "w", encoding="utf-8") as f:
    f.write(content)