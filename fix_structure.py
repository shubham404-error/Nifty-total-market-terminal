with open("pages/market_structure.py", "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace("def market_health_page():", "def market_structure_page():")
content = content.replace('st.title("dYc Market Health")', 'from ui.components import terminal_header\n    terminal_header("Market Structure", "Global index-health dashboard showing Nifty 50 MAs, Breadth, and Stage Distribution.")')
content = content.replace('st.title("📊 Market Health")', 'from ui.components import terminal_header\n    terminal_header("Market Structure", "Global index-health dashboard showing Nifty 50 MAs, Breadth, and Stage Distribution.")')
with open("pages/market_structure.py", "w", encoding="utf-8") as f:
    f.write(content)