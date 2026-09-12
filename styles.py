import streamlit as st

def inject_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    @import url('https://api.fontshare.com/v2/css?f[]=clash-display@400,500,600,700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif !important;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Clash Display', sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown(
        """
    <style>
    :root {
        --bg: #080b10;
        --panel: #10151c;
        --panel-soft: #131a23;
        --border: #28323d;
        --text: #eef2f6;
        --muted: #9aa7b5;
        --accent: #f0a51a;
        --green: #27c78a;
        --red: #ef6b68;
    }
    
    .stApp {
        background: var(--bg);
        color: var(--text);
        font-family: Helvetica, Arial, sans-serif;
    }
    
    html, body {
        font-family: Helvetica, Arial, sans-serif;
    }
    
    .stApp [data-testid="stMarkdownContainer"],
    .stApp [data-testid="stText"],
    .stApp p,
    .stApp h1,
    .stApp h2,
    .stApp h3,
    .stApp label {
        font-family: Helvetica, Arial, sans-serif;
    }
    
    .block-container {
        max-width: 1440px;
        padding-top: 4.5rem !important;
        padding-bottom: 3rem;
    }
    
    [data-testid="stSidebar"] {
        background: #0b0f14;
        border-right: 1px solid var(--border);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] *,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] button {
        font-family: Helvetica, Arial, sans-serif;
    }
    
    /* Never override Streamlit / Material Symbols fonts.
       Otherwise icon ligatures render as literal text such as keyboard_double_arrow. */
    .material-symbols-rounded,
    .material-symbols-outlined,
    [class*="material-symbols"],
    [data-testid="stSidebar"] [class*="material-symbols"] {
        font-family: "Material Symbols Rounded", "Material Symbols Outlined", sans-serif !important;
        font-feature-settings: "liga";
    }
    
    .terminal-topbar {
        background: linear-gradient(180deg, #111821 0%, #0d1218 100%);
        border: 1px solid var(--border);
        border-left: 4px solid var(--accent);
        padding: 16px 20px;
        margin: 0 0 18px 0;
        border-radius: 7px;
    }
    
    .terminal-kicker,
    .page-kicker,
    .section-kicker {
        color: var(--accent);
        text-transform: uppercase;
        letter-spacing: 1.3px;
        font-size: 10px;
        font-weight: 700;
    }
    
    .terminal-brand {
        font-size: 28px;
        font-weight: 750;
        margin-top: 3px;
    }
    
    .brand-lockup-name {
        font-size: 15px;
        font-weight: 750;
        line-height: 1.15;
        letter-spacing: 0.2px;
    }
    
    .brand-lockup-sub {
        color: var(--muted);
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 1.1px;
        margin-top: 2px;
    }
    
    .terminal-sub {
        color: var(--muted);
        font-size: 13px;
        line-height: 1.45;
        margin-top: 5px;
    }
    
    .page-hero {
        padding: 8px 0 16px;
    }
    
    .page-title {
        font-size: 38px;
        font-weight: 750;
        line-height: 1.08;
        margin: 5px 0 8px;
    }
    
    .page-copy {
        color: var(--muted);
        max-width: 940px;
        font-size: 15px;
        line-height: 1.6;
    }
    
    .guide-box {
        background: #101720;
        border: 1px solid #354251;
        border-left: 3px solid var(--accent);
        border-radius: 7px;
        padding: 14px 16px;
        margin: 8px 0 18px;
    }
    
    .guide-title {
        font-size: 14px;
        font-weight: 700;
        margin-bottom: 5px;
    }
    
    .guide-copy {
        color: var(--muted);
        font-size: 13px;
        line-height: 1.55;
    }
    
    .guide-step {
        margin-top: 6px;
    }
    
    .info-card {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 7px;
        padding: 16px;
        min-height: 125px;
    }
    
    .info-card h4 {
        margin: 0 0 8px;
        font-size: 15px;
    }
    
    .info-card p {
        color: var(--muted);
        font-size: 13px;
        line-height: 1.55;
        margin: 0;
    }
    
    .status-chip {
        display: inline-block;
        border: 1px solid #3b4653;
        background: #111820;
        color: var(--muted);
        padding: 5px 10px;
        border-radius: 999px;
        font-size: 11px;
        margin: 0 4px 8px 0;
    }
    
    .status-chip.green {
        color: var(--green);
        border-color: #1f6a50;
    }
    
    .status-chip.orange {
        color: var(--accent);
        border-color: #735919;
    }
    
    .status-chip.red {
        color: var(--red);
        border-color: #69302e;
    }
    
    .section-title {
        font-size: 20px;
        font-weight: 750;
        margin: 22px 0 9px;
    }
    
    div[data-testid="stMetric"] {
        background: var(--panel);
        border: 1px solid var(--border);
        border-top: 2px solid var(--accent);
        border-radius: 6px;
    }
    
    .stButton > button,
    .stDownloadButton > button {
        min-height: 42px;
        border-radius: 5px;
        border: 1px solid #4a5665;
        background: #141b24;
        color: var(--text);
        font-weight: 700;
    }
    
    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: var(--accent);
        background: #1a222c;
    }
    
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 6px;
    }
    
    .small-note {
        color: var(--muted);
        font-size: 11px;
        line-height: 1.45;
    }
    
    hr {
        border-color: var(--border);
    }
    
    .product-pill {
        display: inline-block;
        padding: 4px 9px;
        border-radius: 999px;
        border: 1px solid #3a4653;
        background: #111821;
        color: #cbd5e1;
        font-size: 10px;
        letter-spacing: .7px;
        text-transform: uppercase;
        margin-right: 5px;
    }
    .product-pill.accent {
        color: #f0a51a;
        border-color: #735919;
    }
    
    
    @media (max-width: 768px) {
        .block-container {
            padding-top: 5.25rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
    
        .terminal-topbar {
            margin-top: 0;
            padding: 14px 15px;
        }
    
        .terminal-brand {
            font-size: 22px;
        }
    
        .page-title {
            font-size: 30px;
        }
    
        .page-copy {
            font-size: 14px;
        }
    
        [data-testid="stSidebar"] {
            width: min(86vw, 360px);
        }
    }
    
    
    .terminal-ownership {
        margin-top: 5px;
        color: var(--muted);
        font-size: 10px;
        letter-spacing: 0.25px;
        line-height: 1.45;
    }
    .terminal-footer {
        margin-top: 42px;
        padding: 18px 0 8px;
        border-top: 1px solid var(--border);
        text-align: center;
        color: var(--muted);
        font-size: 11px;
        line-height: 1.65;
    }
    .terminal-footer .footer-owner {
        color: var(--text);
        font-weight: 600;
    }
    .sidebar-ownership {
        margin-top: 12px;
        color: var(--muted);
        font-size: 10px;
        line-height: 1.55;
    }
    
    </style>
    """,
        unsafe_allow_html=True,
    )
