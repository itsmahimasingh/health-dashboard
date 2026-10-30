import math
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

import database as db
import ui

WATER_GOAL = 8
SLOTS = ["Morning", "Afternoon", "Evening", "Night"]
SLOT_ICONS = {
    "Morning": ":material/wb_twilight:",
    "Afternoon": ":material/wb_sunny:",
    "Evening": ":material/wb_cloudy:",
    "Night": ":material/dark_mode:",
}
TEAL = "#3E9DA9"
DROP = (
    '<svg width="34" height="34" viewBox="0 0 24 24" style="margin-right:4px">'
    '<path d="M12 2C12 2 5 10 5 15a7 7 0 0 0 14 0c0-5-7-13-7-13z" '
    'fill="{fill}" opacity="{opacity}"/></svg>'
)


@st.cache_data
def load_foods():
    return pd.read_csv(Path(__file__).parent.parent / "data" / "foods.csv")


def change(day, field, delta):
    cur = db.get_intake(day)
    cur[field] = max(0, cur[field] + delta)
    db.save_intake(day, cur["water"], cur["tea"], cur["chai"])


st.title(":material/restaurant: Food, Water & Medicines")
st.caption("Log your meals, water, chai and medicines for the day. Food values are approximate for common Indian foods.")

foods = load_foods()
day = st.date_input("Date", date.today(), max_value=date.today())
intake = db.get_intake(day)

tab_meals, tab_water, tab_meds = st.tabs([
    ":material/restaurant: Meals",
    ":material/water_drop: Water and chai",
    ":material/medication: Medicines",
])

# ================= Meals =================
with tab_meals:
    with st.form("add_meal", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 4, 1])
        meal_type = c1.selectbox("Meal", ["Breakfast", "Lunch", "Snack", "Dinner"])
        food = c2.selectbox("Food", foods["food"], help="Type to search. Portion sizes are in brackets.")
        servings = c3.number_input("Servings", 0.5, 10.0, 1.0, 0.5,
                                   help="1 = the portion in brackets. 2 rotis = 2 servings.")
        if st.form_submit_button("Add to log", icon=":material/add:", type="primary"):
            r = foods[foods["food"] == food].iloc[0]
            db.add_meal(day, meal_type, food, servings,
                        r["calories"] * servings, r["carbs_g"] * servings,
                        r["protein_g"] * servings, r["fat_g"] * servings)

    meals = db.get_meals(day)
    if meals.empty:
        st.info("Nothing logged for this day yet. Add a food above.")
    else:
        t1, t2, t3, t4 = st.columns(4)
        t1.metric("Calories", f"{meals['calories'].sum():.0f} kcal")
        t2.metric("Carbs", f"{meals['carbs'].sum():.0f} g")
        t3.metric("Protein", f"{meals['protein'].sum():.0f} g")
        t4.metric("Fat", f"{meals['fat'].sum():.0f} g")
        st.dataframe(meals.round(1), width="stretch", hide_index=True)
        if st.button("Clear this day's meals", icon=":material/delete:", type="tertiary", key="clear_meals"):
            db.clear_meals(day)
            st.rerun()

    totals = db.daily_totals(7)
    if not totals.empty:
        st.subheader("Carbs per day (last 7 days)")
        ui.daily_bars(totals, "carbs", "Carbs (g)", ui.ORANGE)

# ================= Water, tea and chai =================
with tab_water:
    st.subheader(":material/water_drop: Water")
    glasses = intake["water"]
    shown = max(WATER_GOAL, glasses)
    drops = (DROP.format(fill=TEAL, opacity=1) * glasses
             + DROP.format(fill=TEAL, opacity=0.2) * (shown - glasses))
    st.markdown(f"<div style='display:flex;flex-wrap:wrap'>{drops}</div>", unsafe_allow_html=True)
    st.progress(min(glasses / WATER_GOAL, 1.0))
    st.write(f"**{glasses} of {WATER_GOAL} glasses**")
    w1, w2, _ = st.columns([1, 1, 2])
    w1.button("Add a glass", icon=":material/add:", type="primary", key="water_add",
              on_click=change, args=(day, "water", 1))
    w2.button("Remove one", icon=":material/remove:", key="water_sub",
              on_click=change, args=(day, "water", -1))
    if glasses >= WATER_GOAL:
        st.success("You reached your water goal for the day!", icon=":material/check_circle:")

    st.subheader(":material/emoji_food_beverage: Tea and chai")
    tea_col, chai_col = st.columns(2)
    for col, field, label in [(tea_col, "tea", "Tea"), (chai_col, "chai", "Chai")]:
        with col:
            st.metric(label, ui.plural(intake[field], "cup"))
            b1, b2 = st.columns(2)
            b1.button("Add", icon=":material/add:", type="primary", key=f"{field}_add",
                      on_click=change, args=(day, field, 1))
            b2.button("Remove", icon=":material/remove:", key=f"{field}_sub",
                      on_click=change, args=(day, field, -1))

    total_cups = intake["tea"] + intake["chai"]
    if total_cups > 3:
        st.info(f"You have had {total_cups} cups of tea and chai today. Try less sugar in each cup.")
    if intake["chai"] > 0:
        st.caption(f"Sweet chai adds roughly {intake['chai'] * 11} g of carbs (about 11 g per cup).")

    hist = db.get_intake_history(7)
    tea_total = int(hist["tea"].sum()) if not hist.empty else 0
    chai_total = int(hist["chai"].sum()) if not hist.empty else 0
    total = tea_total + chai_total

    st.caption("Tea vs chai (last 7 days)")
    if total == 0:
        st.info("No tea or chai logged yet. Use the Add buttons above.")
    else:
        tea_pct = round(tea_total * 100 / total)
        chai_pct = 100 - tea_pct
        cx, cy, r, w = 260, 170, 105, 34
        circ = 2 * math.pi * r
        light, dark = "#A9DCE0", "#2F8793"

        parts = [
            '<div style="text-align:center">',
            '<svg viewBox="0 0 520 340" style="width:100%;max-width:520px" xmlns="http://www.w3.org/2000/svg">',
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{light}" stroke-width="{w}"/>',
        ]
        if tea_total == 0:
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{dark}" stroke-width="{w}"/>')
        elif chai_total > 0:
            length = circ * chai_total / total
            start = -90 + 360 * tea_total / total
            parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{dark}" stroke-width="{w}" '
                f'stroke-linecap="round" stroke-dasharray="{max(length - w, 0.01):.2f} {circ:.2f}" '
                f'stroke-dashoffset="{-w / 2:.2f}" transform="rotate({start:.2f} {cx} {cy})"/>'
            )
        parts += [
            f'<circle cx="{cx}" cy="{cy - r}" r="11" fill="white"/>',
            f'<text x="{cx}" y="{cy}" text-anchor="middle" font-size="36" font-weight="600" fill="currentColor" font-family="Poppins, sans-serif">{total}</text>',
            f'<text x="{cx}" y="{cy + 26}" text-anchor="middle" font-size="13" fill="currentColor" opacity="0.7" font-family="Poppins, sans-serif">{"cup" if total == 1 else "cups"} in 7 days</text>',
            f'<rect x="395" y="30" width="105" height="64" rx="14" fill="{light}"/>',
            f'<text x="447" y="62" text-anchor="middle" font-size="26" fill="#1F4A52" font-family="Poppins, sans-serif">{tea_pct}%</text>',
            f'<text x="447" y="84" text-anchor="middle" font-size="12" fill="#1F4A52" font-family="Poppins, sans-serif">Tea · {ui.plural(tea_total, "cup")}</text>',
            f'<rect x="20" y="246" width="105" height="64" rx="14" fill="{dark}"/>',
            f'<text x="72" y="278" text-anchor="middle" font-size="26" fill="white" font-family="Poppins, sans-serif">{chai_pct}%</text>',
            f'<text x="72" y="300" text-anchor="middle" font-size="12" fill="white" font-family="Poppins, sans-serif">Chai · {ui.plural(chai_total, "cup")}</text>',
            '</svg></div>',
        ]
        st.markdown("".join(parts), unsafe_allow_html=True)

# ================= Medicines =================
with tab_meds:
    meds = db.get_medicines()
    taken_ids = db.get_taken(day)

    with st.expander(":material/add: Add a medicine", expanded=meds.empty):
        with st.form("med_form", clear_on_submit=True):
            mc1, mc2, mc3 = st.columns([3, 2, 2])
            med_name = mc1.text_input("Medicine name")
            med_dose = mc2.text_input("Dose (e.g. 1 tablet)")
            med_slot = mc3.selectbox("When", SLOTS)
            if st.form_submit_button("Add medicine", icon=":material/add:", type="primary"):
                if med_name.strip():
                    db.add_medicine(med_name.strip(), med_dose.strip(), med_slot)
                    st.rerun()
                else:
                    st.warning("Please type the medicine name.")

    if meds.empty:
        st.info("No medicines added yet. Add one above.")
    else:
        all_ids = {int(i) for i in meds["id"]}
        done = len(all_ids & taken_ids)
        st.write(f"**{done} of {len(all_ids)} medicines taken**")
        st.progress(done / len(all_ids))

        for slot in SLOTS:
            group = meds[meds["slot"] == slot]
            if group.empty:
                continue
            st.markdown(f"**{SLOT_ICONS[slot]} {slot}**")
            for _, m in group.iterrows():
                mid = int(m["id"])
                was_taken = mid in taken_ids
                label = m["name"] + (f" — {m['dose']}" if m["dose"] else "")
                row1, row2 = st.columns([6, 2])
                now_taken = row1.checkbox(label, value=was_taken, key=f"med_{mid}_{day}")
                if now_taken != was_taken:
                    db.set_taken(day, mid, now_taken)
                    st.rerun()
                if row2.button("Delete", icon=":material/delete:", type="tertiary", key=f"del_{mid}"):
                    db.delete_medicine(mid)
                    st.rerun()

    st.caption("Take medicines exactly as your doctor prescribed. This is only a reminder log.")