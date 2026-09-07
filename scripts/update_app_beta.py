import re

with open("app.py", "r", encoding="utf-8") as f:
    code = f.read()

# Add imports and IS_BETA
if "IS_BETA =" not in code:
    code = code.replace("from engine import (", "from engine import (\n    load_dvm_scores,\n")
    code = code.replace("st.set_page_config(", "IS_BETA = st.query_params.get('beta') == 'true'\n\nst.set_page_config(")

# Refactor scan_page
scan_func_match = re.search(r'def scan_page\(\):.*?prices, failures = download_prices\(.*?\).*?indicators = calculate_indicators\(prices\).*?convergence_v2 = convergence_table_v2\(snapshot\)', code, re.DOTALL)

if scan_func_match:
    old_scan = scan_func_match.group(0)
    
    # We will replace the download logic
    new_download = """
            if IS_BETA:
                st.info("BETA MODE: Loading offline data (Zero Live Compute)")
                import os
                if os.path.exists("cache.parquet"):
                    prices = pd.read_parquet("cache.parquet")
                    failures = []
                else:
                    st.error("Offline cache.parquet not found. Run build_cache.py")
                    st.stop()
            else:
                prices, failures = download_prices(
                    universe,
                    years=history_years,
                    batch_size=batch_size,
                    progress_callback=update,
                )
    """
    
    # Replace the original download_prices call
    old_dl = r"""prices, failures = download_prices\(
                universe,
                years=history_years,
                batch_size=batch_size,
                progress_callback=update,
            \)"""
    
    new_scan = re.sub(old_dl, new_download.strip(), old_scan)
    
    # Now merge DVM scores after convergence_table_v2
    dvm_merge = """convergence_v2 = convergence_table_v2(snapshot)
            
            if IS_BETA:
                dvm = load_dvm_scores()
                if not dvm.empty:
                    snapshot = snapshot.merge(dvm, on="Yahoo Symbol", how="left")
                    convergence = convergence.merge(dvm, on="Yahoo Symbol", how="left")
                    convergence_v2 = convergence_v2.merge(dvm, on="Yahoo Symbol", how="left")"""
                    
    new_scan = new_scan.replace("convergence_v2 = convergence_table_v2(snapshot)", dvm_merge)
    
    code = code.replace(old_scan, new_scan)
else:
    print("Could not match scan_page")

with open("app.py", "w", encoding="utf-8") as f:
    f.write(code)
print("Updated app.py")
