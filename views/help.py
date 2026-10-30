import streamlit as st

import database as db

st.title(":material/help: Help & Glossary")
st.caption("How to use the app, and what the numbers mean.")

tab_start, tab_numbers, tab_words, tab_privacy = st.tabs([
    ":material/flag: Getting started",
    ":material/straighten: Normal ranges",
    ":material/menu_book: Glossary",
    ":material/lock: Privacy & safety",
])

# ---------- getting started ----------
with tab_start:
    st.markdown("**Use it in four steps**")
    steps = [
        ("Fill your profile", "On the Dashboard, open **Your profile** and enter your age, height, weight and waist.",
         "views/home.py", "Go to Dashboard"),
        ("Log your day", "Add meals, water, chai and medicines. It takes a minute.",
         "views/meals.py", "Log food & water"),
        ("Log sleep and glucose", "Log last night's sleep. If you have a glucose meter, add your readings with the time.",
         "views/glucose.py", "Add a glucose reading"),
        ("Check your risk", "See your Indian Diabetes Risk Score and a lifestyle plan made for you.",
         "views/diabetes.py", "See my risk"),
    ]
    for i, (title, text, page, link) in enumerate(steps, start=1):
        with st.container(border=True):
            st.markdown(f"**{i}. {title}**  \n{text}")
            st.page_link(page, label=link, icon=":material/arrow_forward:")

    st.markdown("**Tips**")
    st.markdown(
        "- Hover over the :material/help: icon next to a field to see what it means.\n"
        "- You can pick an earlier date on the logging pages to fill in a missed day.\n"
        "- Turn on **Night mode** at the bottom of the menu if the screen is too bright.\n"
        "- Just exploring? Use **Load demo data** in Your profile on the Dashboard."
    )

# ---------- normal ranges ----------
with tab_numbers:
    st.markdown("**Blood glucose (sugar)**")
    st.table({
        "Test": ["Fasting (no food for 8 hours)", "2 hours after a meal", "HbA1c (3-month average)"],
        "Normal": ["70 to 99 mg/dL", "Under 140 mg/dL", "Under 5.7%"],
        "Prediabetes range": ["100 to 125 mg/dL", "140 to 199 mg/dL", "5.7% to 6.4%"],
        "Diabetes range": ["126 mg/dL or more", "200 mg/dL or more", "6.5% or more"],
    })
    st.caption("Only a doctor can diagnose diabetes, usually by repeating a lab test. "
               "Under 70 mg/dL is low: eat or drink something sugary and tell your doctor if it keeps happening.")

    st.markdown("**BMI for Indian adults**")
    st.table({
        "BMI": ["Under 18.5", "18.5 to 22.9", "23 to 24.9", "25 or more"],
        "Meaning": ["Underweight", "Healthy", "Overweight", "Obese range"],
    })
    st.caption("Indian guidelines use lower cut-offs than the global ones, because health risks start at a lower BMI.")

    st.markdown("**Waist**")
    st.table({
        "": ["Women", "Men"],
        "Healthy": ["Under 80 cm", "Under 90 cm"],
    })

    st.markdown("**Indian Diabetes Risk Score (IDRS)**")
    st.table({
        "Score": ["Under 30", "30 to 50", "60 or more"],
        "Risk": ["Low", "Moderate", "High"],
        "What to do": ["Keep up healthy habits", "Get a blood sugar test every year",
                       "Get a fasting glucose or HbA1c test soon"],
    })

# ---------- glossary ----------
with tab_words:
    terms = {
        "mg/dL": "Milligrams per decilitre. The unit glucose meters in India use.",
        "Fasting glucose": "Blood sugar measured in the morning before eating anything for at least 8 hours.",
        "After-meal glucose": "Blood sugar measured about 2 hours after you start eating.",
        "Glucose spike": "A quick rise in blood sugar, usually after a meal high in carbs. "
                         "The Glucose page finds them when you log readings before and after meals.",
        "HbA1c": "A lab blood test that shows your average blood sugar over the last 2 to 3 months.",
        "Prediabetes": "Blood sugar higher than normal, but not high enough for diabetes. "
                       "It can often be reversed with diet and exercise.",
        "BMI": "Body Mass Index: weight (kg) divided by height (m) squared. A rough guide to healthy weight.",
        "IDRS": "Indian Diabetes Risk Score, from the Madras Diabetes Research Foundation. "
                "It uses age, waist, activity and family history. No blood test needed.",
        "Carbs": "Carbohydrates: rice, roti, sugar, potatoes and similar foods. They raise blood sugar the most.",
        "PCOS": "Polycystic ovary syndrome. A common hormone condition in women that can cause irregular periods "
                "and raises the risk of type 2 diabetes.",
        "AI risk check": "A machine learning model trained on data from 768 women. It looks at glucose, BMI, age "
                         "and pregnancies, and shows which of them affected your result.",
        "Health score": "A simple 0 to 100 score from this app, based on your sleep, exercise, fasting glucose "
                        "and water in the last 7 days. It is not a medical measure.",
    }
    for term, meaning in terms.items():
        st.markdown(f"**{term}**  \n{meaning}")

# ---------- privacy ----------
with tab_privacy:
    if db.demo_mode():
        st.info("You are using the online demo. Anything you enter stays only in this browser tab "
                "and is deleted when you close it. Please do not enter real health details.",
                icon=":material/info:")
    else:
        st.info("Your data is saved only on this computer, in a file called health.db. "
                "Nothing is sent anywhere.", icon=":material/info:")
    st.markdown("**This app is a screening and tracking aid, not a doctor.**")
    st.markdown(
        "- It cannot diagnose diabetes, PCOS or any other condition.\n"
        "- Do not start, stop or change any medicine because of what it shows.\n"
        "- See a doctor if your readings are often outside the normal ranges.\n"
        "- **Get medical help straight away** if you feel very unwell, confused, very thirsty, "
        "or your glucose is very high or very low."
    )
