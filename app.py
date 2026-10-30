import streamlit as st

import database as db
import theme

st.set_page_config(
    page_title="Health Dashboard",
    page_icon=":material/health_and_safety:",
    layout="wide",
    initial_sidebar_state="auto",  # open on computers, folded into a menu button on phones
)
db.init_db()

# Online demo: fill each new visitor's private copy with demo data straight away
if db.demo_mode() and not st.session_state.get("demo_seeded"):
    db.seed_demo()
    st.session_state["demo_seeded"] = True

profile = db.get_profile()

# The menu, grouped so it is clear what each page is for
check_pages = [
    st.Page("views/diabetes.py", title="Diabetes Risk", icon=":material/bloodtype:"),
    st.Page("views/ml_model.py", title="AI Risk Check", icon=":material/psychology:"),
]
# PCOS page is only shown for female users
if profile and profile["sex"] == "Female":
    check_pages.append(st.Page("views/pcos.py", title="PCOS Check", icon=":material/female:"))

pages = {
    "": [st.Page("views/home.py", title="Dashboard", icon=":material/dashboard:", default=True)],
    "Track your day": [
        st.Page("views/meals.py", title="Food, Water & Medicines", icon=":material/restaurant:"),
        st.Page("views/sleep.py", title="Sleep & Exercise", icon=":material/bedtime:"),
        st.Page("views/glucose.py", title="Glucose", icon=":material/show_chart:"),
    ],
    "Check your risk": check_pages,
    "Help": [st.Page("views/help.py", title="Help & Glossary", icon=":material/help:")],
}
nav = st.navigation(pages)

with st.sidebar:
    with st.container(key="settings"):
        night = st.toggle(":material/dark_mode: Night mode", key="dark_mode")
    if db.demo_mode():
        st.caption("Online demo with sample data. Anything you enter stays private to this "
                   "browser tab and is deleted when you close it. Please do not enter real health details.")

try:
    _theme = st.context.theme
    native_dark = (getattr(_theme, "type", None) or getattr(_theme, "base", None)) == "dark"
except Exception:
    native_dark = False

theme.apply(dark=night, native_dark=native_dark)

nav.run()