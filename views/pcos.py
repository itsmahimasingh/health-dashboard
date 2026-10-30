import streamlit as st

import database as db
import scoring as sc
import ui

st.title(":material/female: PCOS Check")
st.caption("A screening aid based on common PCOS features. It is not a diagnosis.")

p = db.get_profile()
if not p or p["sex"] != "Female":
    st.info("This page is for female users. You can set this in your profile on the Dashboard.")
    st.stop()

bmi = sc.bmi(p["weight_kg"], p["height_cm"])

with st.form("pcos_form"):
    cycle = st.radio("Your periods are usually...", [
        "Regular (about every 21 to 35 days)",
        "Irregular (shorter than 21 or longer than 35 days)",
        "Often missed (gaps of 3 months or more)",
    ])
    st.write("Tick anything that applies to you:")
    hair = st.checkbox("Extra dark or coarse hair on face, chest or abdomen")
    acne = st.checkbox("Persistent acne, especially along the jawline")
    thin = st.checkbox("Thinning hair on the scalp")
    weight = st.checkbox("Weight gain, or difficulty losing weight, mainly around the waist")
    dark = st.checkbox("Dark, velvety skin patches (neck, underarms)")
    fam = st.checkbox("Mother or sister with PCOS or type 2 diabetes")
    us = st.checkbox("A doctor told me an ultrasound showed polycystic-looking ovaries")
    go = st.form_submit_button("Check", icon=":material/check:", type="primary")

if go:
    irregular = not cycle.startswith("Regular")
    androgen = hair or acne or thin
    supporting = int(weight or bmi >= 23) + int(dark) + int(fam)
    met, level = sc.pcos_screen(irregular, androgen, us, supporting)

    ui.show_card("Main PCOS features found", f"{met} of 3", f"{level} chance", ui.RISK_COLORS[level])
    st.write("")
    if level == "High":
        st.error("Several main features of PCOS are present. Please see a gynecologist or "
                 "endocrinologist for proper tests (blood hormones and an ultrasound).")
    elif level == "Moderate":
        st.warning("Some features are present. If they continue, it is worth discussing with a doctor.")
    else:
        st.success("Few PCOS features were found. Mention any new or worsening symptoms to a doctor.")

    st.write("Good to know:")
    st.write("• Thyroid problems, high prolactin and pregnancy can cause similar signs, so only a doctor can tell the cause.")
    st.write("• PCOS is linked with a higher risk of type 2 diabetes, so the Diabetes Risk page is worth checking too.")
    st.write("• Regular activity, good sleep and balanced meals support most women with PCOS. Do not start any medicine without a doctor.")
