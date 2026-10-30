import streamlit as st

import database as db
import scoring as sc
import ui

st.title(":material/bloodtype: Diabetes Risk & Lifestyle Plan")
st.caption("Screening only. Only a blood test (fasting glucose or HbA1c) can confirm diabetes.")

p = db.get_profile()
if not p:
    st.warning("Please fill in your profile first. It takes 30 seconds.")
    st.page_link("views/home.py", label="Go to your profile", icon=":material/person:")
    st.stop()

score = sc.idrs_score(p["age"], p["sex"], p["waist_cm"], p["activity"], p["family"])
cat = sc.idrs_category(score)

ui.show_card("Your IDRS score", f"{score} / 100", f"{cat} risk", ui.RISK_COLORS[cat], bar=score)
st.write("")
{"Low": st.success, "Moderate": st.warning, "High": st.error}[cat](
    f"{cat} risk." + (" Please get a fasting glucose or HbA1c test." if cat != "Low" else " Keep up healthy habits."))

with st.expander("How is this score calculated?"):
    st.markdown(
        "The **Indian Diabetes Risk Score (IDRS)** from the Madras Diabetes Research Foundation "
        "adds points for four things:\n\n"
        "| Factor | Points |\n|---|---|\n"
        "| Age: under 35 / 35 to 49 / 50 or more | 0 / 20 / 30 |\n"
        "| Waist (women: under 80 / 80 to 89 / 90+ cm; men: under 90 / 90 to 99 / 100+ cm) | 0 / 10 / 20 |\n"
        "| Activity: exercise and active work / one of them / neither | 0 / 20 / 30 |\n"
        "| Family history: no parent / one parent / both parents | 0 / 10 / 20 |\n\n"
        "Under 30 is low risk, 30 to 50 is moderate, and 60 or more is high."
    )

act = db.get_activity(7)
avg_sleep = act["sleep_hours"].mean() if not act.empty else None
avg_ex = act["exercise_min"].mean() if not act.empty else None

st.subheader("Your lifestyle plan")
for tip in sc.lifestyle_tips(p, avg_sleep, avg_ex):
    st.write("• " + tip)
st.caption("If you already have diabetes, review any plan with your doctor.")

st.write("")
st.page_link("views/ml_model.py", label="Want a second opinion? Try the AI Risk Check", icon=":material/psychology:")
