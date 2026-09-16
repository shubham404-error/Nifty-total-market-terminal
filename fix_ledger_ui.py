with open("pages/signal_ledger.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("def positions_at_risk_page():", "def signal_ledger_page():")
content = content.replace('st.title("dYs\\" Positions at Risk (Thesis Monitoring)")', 'st.title("📓 Signal Ledger")')
content = content.replace('st.markdown("Monitor decay in the original investment thesis for active signals.")', 'st.markdown("Monitor active signals and track their thesis decay.")')

with open("pages/signal_ledger.py", "w", encoding="utf-8") as f:
    f.write(content)

with open("app.py", "r", encoding="utf-8") as f:
    app = f.read()
app = app.replace("from pages.signal_ledger import positions_at_risk_page as signal_ledger_page", "from pages.signal_ledger import signal_ledger_page")
with open("app.py", "w", encoding="utf-8") as f:
    f.write(app)