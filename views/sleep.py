from datetime import date

import streamlit as st

import database as db
import ui

st.title(":material/bedtime: Sleep & Exercise")
st.caption("Log last night's sleep and today's activity. Pick an earlier date to fix a past day.")

day = st.date_input("Date", date.today(), max_value=date.today())
saved = db.get_activity_day(day)

with st.form("activity_form"):
    if saved:
        st.caption(f"You already logged {day:%d %b}. Change the values and save to update it.")
    sleep = st.slider("Sleep last night (hours)", 0.0, 12.0, float(saved["sleep_hours"]) if saved else 7.0, 0.5,
                      help="Hours actually asleep. Adults need 7 to 9.")
    c1, c2 = st.columns(2)
    exercise = c1.number_input("Exercise (minutes)", 0, 300, int(saved["exercise_min"]) if saved else 0,
                               help="Brisk walking, yoga, sport or gym. Aim for 30 minutes a day.")
    steps = c2.number_input("Steps", 0, 50000, int(saved["steps"]) if saved else 0, step=500,
                            help="From your phone or watch. Leave 0 if you don't know.")
    label = "Update" if saved else "Save"
    # Only save when the button is clicked (before, it saved on every page visit)
    if st.form_submit_button(label, icon=":material/save:", type="primary"):
        db.save_activity(day, sleep, exercise, steps)
        st.success(f"Saved for {day:%d %b}.", icon=":material/check_circle:")

df = db.get_activity(30)
if df.empty:
    st.info("No entries yet. Log last night's sleep above to start your charts.", icon=":material/info:")
else:
    st.subheader("Sleep (hours)")
    ui.daily_bars(df, "sleep_hours", "Hours", ui.TEAL, goal=7)
    st.subheader("Exercise (minutes)")
    ui.daily_bars(df, "exercise_min", "Minutes", ui.ORANGE, goal=30)
    st.subheader("Steps")
    ui.daily_line(df, "steps", "Steps")
