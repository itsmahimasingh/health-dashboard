import streamlit as st

TEAL = "#3E9DA9"
TEAL_DARK = "#2F8793"
ORANGE = "#F4A340"
ORANGE_DARK = "#E8922A"


def _sel(kind, suffix=""):
    """CSS selectors for one Streamlit button type (primary, secondary or tertiary)."""
    names = [
        f'button[kind="{kind}"]',
        f'button[kind="{kind}FormSubmit"]',
        f'[data-testid="stBaseButton-{kind}"]',
        f'[data-testid="stBaseButton-{kind}FormSubmit"]',
    ]
    return ", ".join(n + suffix for n in names)


def apply(*_ignored, dark=False, native_dark=False):
    """Shared look for every page. dark = our Night mode switch."""
    css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
/* one font everywhere (icons keep their own font) */
html, body, .stApp, p, li, label, button, input, textarea, h1, h2, h3, h4 {{
    font-family: 'Poppins', sans-serif;
}}
/* calmer sizes: smaller page titles and section headings */
h1 {{ font-size: 2rem !important; font-weight: 700 !important; padding-bottom: 0.2rem !important; }}
h2 {{ font-size: 1.5rem !important; font-weight: 600 !important; }}
h3 {{ font-size: 1.2rem !important; font-weight: 600 !important; padding-top: 1rem !important; }}
[data-testid="stMetricValue"] {{ font-size: 1.6rem !important; }}
[data-testid="stMetricLabel"] p {{ font-size: 0.9rem !important; }}
[data-testid="stCaptionContainer"] p {{ font-size: 0.88rem; }}
/* phones and small tablets */
@media (max-width: 640px) {{
    .block-container, [data-testid="stMainBlockContainer"] {{
        padding-left: 1rem !important; padding-right: 1rem !important; padding-top: 3rem !important;
    }}
    h1 {{ font-size: 1.55rem !important; }}
    h3 {{ font-size: 1.1rem !important; padding-top: 0.6rem !important; }}
    [data-testid="stMetricValue"] {{ font-size: 1.35rem !important; }}
    /* bigger tap targets for buttons */
    .stButton > button, [data-testid="stFormSubmitButton"] button {{ min-height: 3rem; width: 100%; }}
    /* tabs scroll sideways instead of squashing */
    [data-baseweb="tab-list"] {{ overflow-x: auto; }}
    /* cards: less padding, smaller number */
    .hd-card {{ padding: 14px 16px !important; }}
    .hd-card-value {{ font-size: 1.6rem !important; }}
}}
/* menu section headings */
[data-testid="stNavSectionHeader"] {{
    text-transform: uppercase; letter-spacing: 0.06em; font-size: 0.72rem !important;
    opacity: 0.85; margin-top: 0.6rem;
}}
h1 {{
    background: linear-gradient(90deg, {TEAL}, {TEAL_DARK});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
[data-baseweb="tab-highlight"] {{ background-color: {TEAL} !important; }}
button[data-baseweb="tab"][aria-selected="true"] p {{
    color: {TEAL} !important;
    font-weight: 600;
}}
[data-testid="stAlert"] {{ border-radius: 14px; }}
[data-testid="stSidebarNavLink"] {{ border-radius: 12px !important; }}
</style>
"""
    if not native_dark:
        css += f"""
<style>
.stApp, [data-testid="stAppViewContainer"] {{
    background: linear-gradient(180deg, #EAF5F5 0%, #DCEEF0 100%) !important;
}}
div[data-testid="stMetric"] {{
    background: white !important;
    border: none !important;
    border-radius: 18px !important;
    padding: 16px 20px !important;
    box-shadow: 0 6px 20px rgba(62, 157, 169, 0.15) !important;
}}
[data-testid="stExpander"], [data-testid="stForm"] {{
    background: white !important;
    border: none !important;
    border-radius: 18px !important;
    box-shadow: 0 6px 20px rgba(62, 157, 169, 0.12) !important;
}}
[data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"] {{
    background: white !important;
    border-radius: 18px !important;
    padding: 18px 14px 6px 14px !important;
    box-shadow: 0 6px 20px rgba(62, 157, 169, 0.12) !important;
}}

/* every button: same height and shape */
.stButton > button, .stDownloadButton > button,
[data-testid="stFormSubmitButton"] button {{
    min-height: 2.75rem;
    border-radius: 999px;
    padding: 0 1.25rem;
    font-weight: 500;
}}
[data-testid="stColumn"] .stButton > button,
[data-testid="column"] .stButton > button {{ width: 100%; }}

/* secondary: outlined, subtle */
{_sel('secondary')} {{
    background: white !important;
    color: {TEAL_DARK} !important;
    border: 1.5px solid {TEAL} !important;
}}
{_sel('secondary', ':hover')} {{
    background: {TEAL} !important;
    color: white !important;
    border-color: {TEAL} !important;
}}
/* primary: the main action, orange */
{_sel('primary')} {{
    background: {ORANGE} !important;
    color: white !important;
    border: none !important;
    font-weight: 600;
}}
{_sel('primary', ':hover')} {{
    background: {ORANGE_DARK} !important;
    color: white !important;
}}
/* tertiary: plain text, for minor or destructive actions */
{_sel('tertiary')} {{
    background: transparent !important;
    color: {TEAL_DARK} !important;
    border: none !important;
}}
{_sel('tertiary', ':hover')} {{
    background: rgba(62, 157, 169, 0.12) !important;
    color: {TEAL_DARK} !important;
}}

/* teal sidebar */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {TEAL} 0%, {TEAL_DARK} 100%) !important;
}}
[data-testid="stSidebar"] a, [data-testid="stSidebar"] p,
[data-testid="stSidebar"] span, [data-testid="stSidebar"] label {{
    color: white !important;
}}
[data-testid="stSidebarNavLink"]:hover {{ background: rgba(255, 255, 255, 0.15) !important; }}
[data-testid="stSidebarNavLink"][aria-current="page"] {{
    background: rgba(255, 255, 255, 0.28) !important;
}}
.st-key-settings {{
    background: white;
    border-radius: 14px;
    padding: 12px 14px;
}}
.st-key-settings p, .st-key-settings span, .st-key-settings label {{
    color: #2C4A52 !important;
}}
</style>
"""
        if dark:
            css += """
<style>
html { filter: invert(1) hue-rotate(180deg); }
</style>
"""
    st.markdown(css, unsafe_allow_html=True)