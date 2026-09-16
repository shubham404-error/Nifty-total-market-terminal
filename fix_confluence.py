with open("pages/confluence.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'terminal_header("Confluence","Setup-aware ranking. Trend, pullback, fresh momentum and breakout paths are evaluated separately.")',
    'terminal_header("Confluence Builder","Exploratory workspace for mixing and matching signals. This is NOT an auto-buy list.")'
)

# Add checkboxes for legacy momentum filters
injection = """
    with st.expander("LEGACY MOMENTUM FILTERS", expanded=True):
        st.write("Mix in legacy signals to further filter your Confluence pool.")
        c_leg1, c_leg2 = st.columns(2)
        with c_leg1:
            req_mom_9_21 = st.checkbox("Require 9/21 Momentum Setup", value=False)
        with c_leg2:
            req_swing_20_50 = st.checkbox("Require 20/50 Swing Setup", value=False)
            
    if req_mom_9_21:
        snapshot = get_snapshot()
        mom_symbols = snapshot[snapshot["MomentumFresh"] | snapshot["BullMomentum"] | snapshot["VolumeConfirmedMomentum"]]["Symbol"].tolist()
        df = df[df["Symbol"].isin(mom_symbols)]
        
    if req_swing_20_50:
        snapshot = get_snapshot()
        swing_symbols = snapshot[snapshot["BullSwing"]]["Symbol"].tolist()
        df = df[df["Symbol"].isin(swing_symbols)]
"""

content = content.replace("c1,c2,c3,c4=st.columns(4)", injection + "\n    c1,c2,c3,c4=st.columns(4)")

with open("pages/confluence.py", "w", encoding="utf-8") as f:
    f.write(content)