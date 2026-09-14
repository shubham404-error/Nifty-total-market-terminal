with open("pages/buying_list.py", "r", encoding="utf-8") as f:
    content = f.read()

import re

new_import = "from constants import FILTERS_SHADOW_MODE\n"
content = content.replace("from constants import AI_STRATEGY_PREFILTER_SCORE", new_import + "from constants import AI_STRATEGY_PREFILTER_SCORE")

funnel_ui = """
    # --- V4.1 Elimination Funnel ---
    snapshot = get_snapshot().copy()
    from scoring import compute_funnel_booleans
    snapshot = compute_funnel_booleans(snapshot)
    
    universe_size = len(snapshot)
    q_pass = snapshot["passed_data_quality"].sum()
    l_pass = snapshot["passed_data_quality"] & snapshot["passed_liquidity"]
    s_pass = l_pass & snapshot["passed_stage"]
    lead_pass = s_pass & snapshot["passed_leadership"]
    conf_pass = lead_pass & snapshot["passed_confluence"]
    entry_pass = conf_pass & snapshot["passed_entry"]
    
    st.markdown("### Decision Engine V4.1 Funnel")
    if FILTERS_SHADOW_MODE:
        st.warning("⚠️ **SHADOW MODE ACTIVE:** Funnel calculations are displayed but do not filter the Buy List.")
        
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("1. Data Quality", f"{q_pass.sum():,}")
    c2.metric("2. Liquidity", f"{l_pass.sum():,}")
    c3.metric("3. Stage (1/2)", f"{s_pass.sum():,}")
    c4.metric("4. Leadership", f"{lead_pass.sum():,}")
    c5.metric("5. Confluence", f"{conf_pass.sum():,}")
    c6.metric("6. Entry Setup", f"{entry_pass.sum():,}")
    st.divider()
"""

content = content.replace('    min_score = st.slider(', funnel_ui + '    min_score = st.slider(')

with open("pages/buying_list.py", "w", encoding="utf-8") as f:
    f.write(content)