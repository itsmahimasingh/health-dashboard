from datetime import date

import streamlit as st

import database as db
import scoring as sc
import ui

GREEN, YELLOW, RED = ui.GREEN, ui.YELLOW, ui.RED

# Status icons for the plain-language summary
GOOD = ":green[:material/check_circle:]"
WATCH = ":orange[:material/error:]"
ACT = ":red[:material/warning:]"


def welcome_card():
    steps = [
        ("1", "Fill your profile", "Age, height, weight and waist. It takes 30 seconds."),
        ("2", "Log your day", "Meals, water, sleep and glucose from the menu on the left."),
        ("3", "See what it means", "Your scores, alerts and a plain-language summary appear here."),
    ]
    items = ""
    for n, title, text in steps:
        items += (
            "<div style='flex:1;min-width:160px;display:flex;gap:10px'>"
            "<div style='flex:none;width:30px;height:30px;border-radius:50%;background:#3E9DA9;"
            "color:white;display:flex;align-items:center;justify-content:center;font-weight:600'>"
            f"{n}</div>"
            f"<div><div style='font-weight:600;color:#2C4A52'>{title}</div>"
            f"<div style='font-size:0.85rem;color:#5B7C84'>{text}</div></div></div>"
        )
    return (
        "<div style='background:white;border-radius:18px;padding:20px 24px;"
        "box-shadow:0 6px 20px rgba(62,157,169,0.15)'>"
        "<div style='font-size:1.1rem;font-weight:600;color:#2C4A52;margin-bottom:14px'>"
        "Welcome! Here is how to start</div>"
        f"<div style='display:flex;flex-wrap:wrap;gap:18px'>{items}</div></div>"
    )


def profile_section(profile, expanded):
    with st.expander(":material/person: Your profile", expanded=expanded):
        p = profile or {}
        with st.form("profile_form"):
            name = st.text_input("Name", p.get("name", ""), placeholder="Your first name is enough")
            c1, c2, c3 = st.columns(3)
            age = c1.number_input("Age", 10, 100, p.get("age", 30))
            sex = c2.selectbox("Sex", ["Female", "Male"],
                               index=["Female", "Male"].index(p.get("sex", "Female")),
                               help="Used for waist limits, and to show the PCOS and AI pages.")
            height = c3.number_input("Height (cm)", 100.0, 220.0, float(p.get("height_cm", 165)))
            c4, c5 = st.columns(2)
            weight = c4.number_input("Weight (kg)", 20.0, 200.0, float(p.get("weight_kg", 65)))
            waist = c5.number_input("Waist (cm)", 40.0, 160.0, float(p.get("waist_cm", 85)),
                                    help="Measure around your belly button, standing, after breathing out.")
            activity = st.selectbox("How active are you?", range(3), index=p.get("activity", 1),
                                    format_func=lambda i: sc.ACTIVITY_OPTIONS[i],
                                    help="Regular exercise means about 30 minutes most days. "
                                         "Active work means a job where you are on your feet and moving.")
            family = st.selectbox("Parents with diabetes", range(3), index=p.get("family", 0),
                                  format_func=lambda i: sc.FAMILY_OPTIONS[i])
            if st.form_submit_button("Save profile", icon=":material/save:", type="primary"):
                db.save_profile(name, age, sex, height, weight, waist, family, activity)
                st.rerun()

        st.caption("Want to look around first, or start over?")
        b1, b2, _ = st.columns([1, 1, 2])
        if b1.button("Load demo data", icon=":material/auto_awesome:", key="profile_demo",
                     help="Fills the app with two weeks of made-up data."):
            db.seed_demo()
            st.rerun()
        if b2.button("Start empty", icon=":material/restart_alt:", key="clear_all",
                     help="Deletes the profile and all logs."):
            db.clear_all()
            st.rerun()


# ======================= page =======================
profile = db.get_profile()

if not profile:
    st.title(":material/health_and_safety: Personal Health Dashboard")
    st.caption("Track your meals, sleep and glucose, and check your diabetes risk. "
               "A screening aid, not a medical diagnosis.")
    left, right = st.columns([3, 1], vertical_alignment="center")
    left.markdown(welcome_card(), unsafe_allow_html=True)
    with right:
        st.markdown(
            "<div style='text-align:center;color:#5B7C84;font-size:0.85rem;margin-bottom:6px'>"
            "Just looking around?</div>",
            unsafe_allow_html=True,
        )
        if st.button("Load demo data", icon=":material/auto_awesome:", key="welcome_demo", type="primary"):
            db.seed_demo()
            st.rerun()
    st.write("")
    profile_section(profile, expanded=True)
    st.stop()

today = date.today()
act = db.get_activity(7)
meals = db.daily_totals(7)
gluc = db.get_glucose(7)
water_hist = db.get_intake_history(7)

score = sc.idrs_score(profile["age"], profile["sex"], profile["waist_cm"],
                      profile["activity"], profile["family"])
risk = sc.idrs_category(score)
bmi = sc.bmi(profile["weight_kg"], profile["height_cm"])
bmi_label, bmi_level = sc.bmi_category(bmi)
health = sc.health_score(act, gluc, water_hist)

first_name = (profile["name"] or "").strip().split(" ")[0]
st.title(f"Hello, {first_name or 'there'}")
st.caption(f"{today:%A, %d %B}  ·  Your health at a glance. A screening aid, not a medical diagnosis.")

# ---------- 1. three headline cards ----------
c1, c2, c3 = st.columns(3)
if health is None:
    ui.show_card("Health score", "–", "No data yet", YELLOW, where=c1,
                 note="Log sleep, water or glucose to get a score.")
else:
    if health >= 80:
        h_label, h_color = "Good", GREEN
    elif health >= 60:
        h_label, h_color = "Fair", YELLOW
    else:
        h_label, h_color = "Needs attention", RED
    ui.show_card("Health score", f"{health} / 100", h_label, h_color, bar=health, where=c1,
                 note="Your sleep, exercise, fasting glucose and water over the last 7 days.")

ui.show_card("BMI", f"{bmi:.1f}", bmi_label, ui.RISK_COLORS[bmi_level], where=c2,
             note="Healthy for Indian adults: 18.5 to 22.9.")
ui.show_card("Diabetes risk", f"{score} / 100", f"{risk} risk", ui.RISK_COLORS[risk], bar=score, where=c3,
             note="Indian Diabetes Risk Score. Under 30 is low, 60 or more is high.")

# ---------- 2. alerts (only shown when there is something to say) ----------
alerts = []
if not gluc.empty:
    fasting_days = gluc[gluc["context"] == "Fasting"].groupby("day")["value"].mean().tail(3)
    if len(fasting_days) == 3:
        if (fasting_days >= 126).all():
            alerts.append(("error", "Your fasting glucose was 126 mg/dL or higher for the last 3 days. "
                                    "Please see a doctor soon."))
        elif (fasting_days >= 100).all():
            alerts.append(("warning", "Your fasting glucose was 100 mg/dL or higher for the last 3 days. "
                                      "Watch your carbs and consider a check-up."))
if not act.empty:
    recent_sleep = act.sort_values("day")["sleep_hours"].tail(3)
    if len(recent_sleep) == 3:
        if (recent_sleep < 6).all():
            alerts.append(("error", "You slept under 6 hours for the last 3 days. "
                                    "Poor sleep can raise blood sugar, so try to rest more."))
        elif (recent_sleep < 7).all():
            alerts.append(("warning", "You slept under 7 hours for the last 3 days. Try to get to bed earlier."))

st.write("")
for kind, msg in alerts:
    if kind == "error":
        st.error(msg, icon=":material/warning:")
    else:
        st.warning(msg, icon=":material/error:")

# ---------- 3. today ----------
st.subheader(":material/today: Today")
intake = db.get_intake(today)
today_act = db.get_activity_day(today)
today_gluc = db.get_glucose(0)
meds = db.get_medicines()
taken = len({int(i) for i in meds["id"]} & db.get_taken(today)) if not meds.empty else 0

t1, t2, t3, t4 = st.columns(4)
with t1:
    st.metric("Water", f"{intake['water']} of 8 glasses")
    st.page_link("views/meals.py", label="Add water", icon=":material/water_drop:")
with t2:
    st.metric("Sleep last night", f"{today_act['sleep_hours']:g} h" if today_act else "Not logged")
    st.page_link("views/sleep.py", label="Log sleep", icon=":material/bedtime:")
with t3:
    st.metric("Glucose readings", len(today_gluc))
    st.page_link("views/glucose.py", label="Add a reading", icon=":material/bloodtype:")
with t4:
    st.metric("Medicines taken", f"{taken} of {len(meds)}" if not meds.empty else "None set")
    st.page_link("views/meals.py", label="Open checklist" if not meds.empty else "Add medicines",
                 icon=":material/medication:")

# ---------- 4. what it means / trends ----------
st.write("")
tab_summary, tab_trends = st.tabs([":material/lightbulb: What this means", ":material/trending_up: Last 7 days"])

with tab_summary:
    notes = []
    if bmi_level == "Low":
        notes.append((GOOD, f"Your BMI is **{bmi:.1f}**, which is in the healthy range."))
    elif bmi < 18.5:
        notes.append((WATCH, f"Your BMI is **{bmi:.1f}**, which is below the healthy range."))
    else:
        notes.append((WATCH if bmi_level == "Moderate" else ACT,
                      f"Your BMI is **{bmi:.1f}**. For Indian adults, 23 or more is above the healthy range."))

    risk_icon = {"Low": GOOD, "Moderate": WATCH, "High": ACT}[risk]
    advice = {"Low": "Keep up your habits.",
              "Moderate": "A yearly blood sugar test is a good idea.",
              "High": "Please get a fasting glucose or HbA1c test."}[risk]
    notes.append((risk_icon, f"Your diabetes risk is **{risk.lower()}** ({score} points). {advice}"))

    fasting = gluc[gluc["context"] == "Fasting"]["value"] if not gluc.empty else []
    if len(fasting):
        f = fasting.mean()
        if f < 100:
            notes.append((GOOD, f"Your fasting glucose averages **{f:.0f} mg/dL**, which is normal."))
        elif f < 126:
            notes.append((WATCH, f"Your fasting glucose averages **{f:.0f} mg/dL**, a bit above normal "
                                 "(70 to 99). Worth discussing with a doctor."))
        else:
            notes.append((ACT, f"Your fasting glucose averages **{f:.0f} mg/dL**, which is high. Please see a doctor."))

    if not act.empty:
        s, e = act["sleep_hours"].mean(), act["exercise_min"].mean()
        notes.append((GOOD, f"You sleep **{s:.1f} hours** on average. Well done.") if s >= 7 else
                     (WATCH, f"You sleep **{s:.1f} hours** on average. Aim for 7 or more."))
        notes.append((GOOD, f"You exercise **{e:.0f} minutes** a day on average. On track.") if e >= 30 else
                     (WATCH, f"You exercise **{e:.0f} minutes** a day on average. Try to build up to 30."))

    if not water_hist.empty:
        w = water_hist["water"].mean()
        notes.append((GOOD, f"You drink **{w:.0f} glasses** of water a day.") if w >= 8 else
                     (WATCH, f"You drink **{w:.0f} glasses** of water a day. Aim for 8."))

    for icon, text in notes:
        st.markdown(f"{icon} {text}")
    st.caption("This summary is automatic and for tracking only. It is not medical advice.")

with tab_trends:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Avg glucose", f"{gluc['value'].mean():.0f} mg/dL" if not gluc.empty else "–")
    m2.metric("Avg sleep", f"{act['sleep_hours'].mean():.1f} h" if not act.empty else "–")
    m3.metric("Avg exercise", f"{act['exercise_min'].mean():.0f} min" if not act.empty else "–")
    m4.metric("Avg carbs", f"{meals['carbs'].mean():.0f} g a day" if not meals.empty else "–")
    if not act.empty:
        st.markdown("**Sleep (hours)**")
        ui.daily_bars(act, "sleep_hours", "Hours", ui.TEAL, goal=7)
    else:
        st.info("Log your sleep on the Sleep & Exercise page to see a chart here.")
    st.caption("Health score: sleep 25 points, exercise 25, fasting glucose 30, water 20. "
               "Only the parts you have logged are counted. It is a simple tracking score, not a medical measure.")

# ---------- 5. profile ----------
st.write("")
profile_section(profile, expanded=False)
