import re

with open("app.py", "r", encoding="utf-8") as f:
    code = f.read()

# Add Trendlyne widget renderer
trendlyne_renderer = """
def render_trendlyne_widgets(symbol: str):
    import streamlit.components.v1 as components
    tl_sym = symbol.replace(".NS", "")
    st.subheader("Trendlyne Consensus")
    st.caption("Note: AI analysis is generated exclusively from CapitalSense proprietary data and cannot read external Trendlyne widgets.")
    
    html_code = f\"\"\"
    <div style="display: flex; flex-direction: row; gap: 20px;">
        <div style="flex: 1; min-width: 300px;">
            <div class="tl-swot-widget" data-ticker="{tl_sym}" data-exchange="NSE" data-theme="light" data-font="Helvetica"></div>
        </div>
        <div style="flex: 1; min-width: 300px;">
            <div class="tl-qvt-widget" data-ticker="{tl_sym}" data-exchange="NSE" data-theme="light" data-font="Helvetica"></div>
        </div>
    </div>
    <script async src="https://trendlyne.com/web-widget/widget.js"></script>
    \"\"\"
    components.html(html_code, height=450, scrolling=True)
"""

if "def render_trendlyne_widgets" not in code:
    # Insert it before nifty_ai_page
    code = code.replace("def nifty_ai_page():", trendlyne_renderer + "\ndef nifty_ai_page():")

# Now inject it into nifty_ai_page
nifty_ai_page_match = re.search(r'(st\.success\(f"Current verified strategy membership: {labels}"\).*?)(chat_key = f"nifty_ai_chat::{selected}")', code, re.DOTALL)
if nifty_ai_page_match:
    old_block = nifty_ai_page_match.group(0)
    
    # We want to inject it here:
    inject = """st.success(f"Current verified strategy membership: {labels}")
    
    if IS_BETA:
        st.divider()
        render_trendlyne_widgets(selected)

    chat_key = f"nifty_ai_chat::{selected}" """
    
    new_block = re.sub(r'st\.success\(f"Current verified strategy membership: {labels}"\)\s*chat_key = f"nifty_ai_chat::{selected}"', inject, old_block)
    # The regex might fail if there's whitespace.
    code = code.replace(old_block, old_block.replace('chat_key =', f'if IS_BETA:\n        st.divider()\n        render_trendlyne_widgets(selected)\n\n    chat_key ='))

with open("app.py", "w", encoding="utf-8") as f:
    f.write(code)
print("Updated AI page with Trendlyne")
