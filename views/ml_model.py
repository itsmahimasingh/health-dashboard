from datetime import date, timedelta

import pandas as pd
import streamlit as st

import database as db
import model
import scoring as sc
import ui

st.title(":material/psychology: AI Risk Check")
st.caption("A machine learning model trained on real patient data, shown next to the rule-based IDRS score. "
           "Screening only. Only a blood test can diagnose diabetes.")

m = model.load_model()
p = db.get_profile()
if not p:
    st.warning("Please fill in your profile first. It takes 30 seconds.")
    st.page_link("views/home.py", label="Go to your profile", icon=":material/person:")
    st.stop()

if p["sex"] != "Female":
    st.info(
        "This model was trained only on women, so it would not be reliable for men. "
        "Your Diabetes Risk page uses the IDRS score, which works for everyone.",
        icon=":material/info:",
    )
    st.page_link("views/diabetes.py", label="Open Diabetes Risk", icon=":material/bloodtype:")
    st.stop()

# ---------- inputs (filled in from your profile and logs; change them to explore) ----------
g = db.get_glucose(30)
after_meal = g[g["context"] == "After meal"]["value"] if not g.empty else pd.Series(dtype=float)
glucose_default = int(min(max(round(after_meal.mean()), 50), 400)) if not after_meal.empty else 140
bmi_default = round(min(max(sc.bmi(p["weight_kg"], p["height_cm"]), 15.0), 60.0), 1)
age_default = int(min(max(p["age"], 21), 90))

st.subheader("Your inputs")
st.caption("Filled in from your profile and logs. Change any number to see how the result moves.")
c1, c2, c3, c4 = st.columns(4)
glucose = c1.number_input(model.LABELS["Glucose"] + " (mg/dL)", 50, 400, glucose_default,
                          help="The model was trained on a 2-hour glucose test. "
                               "Your average after-meal reading is the closest thing the app has.")
bmi = c2.number_input("BMI", 15.0, 60.0, float(bmi_default), 0.1)
age = c3.number_input("Age", 21, 90, age_default)
pregnancies = c4.number_input(model.LABELS["Pregnancies"], 0, 15, 0)

if after_meal.empty:
    st.caption("No after-meal readings logged yet, so glucose starts at 140 mg/dL. "
               "Log some on the Glucose page for a personal value.")
else:
    st.caption(f"Glucose starts at the average of your {ui.plural(len(after_meal), 'after-meal reading')} "
               "from the last 30 days.")
if p["age"] < 21:
    st.caption("The model only saw people aged 21 or older, so age is set to 21.")

inputs = {"Glucose": glucose, "BMI": bmi, "Age": age, "Pregnancies": pregnancies}
prob, contributions = model.predict(inputs, m)
level = model.risk_level(prob, m)

# ---------- result vs IDRS ----------
st.subheader("Result")
idrs = sc.idrs_score(p["age"], p["sex"], p["waist_cm"], p["activity"], p["family"])
idrs_level = sc.idrs_category(idrs)

left, right = st.columns(2)
ui.show_card("AI model score", f"{prob:.0%}", f"{level} risk", ui.RISK_COLORS[level],
             bar=prob * 100, where=left)
ui.show_card("IDRS score (rules)", f"{idrs} / 100", f"{idrs_level} risk", ui.RISK_COLORS[idrs_level],
             bar=idrs, where=right)
st.write("")

if level == idrs_level:
    st.info(f"Both methods agree: **{level.lower()} risk**.", icon=":material/handshake:")
else:
    st.info(
        f"The two methods disagree: the AI model says **{level.lower()}**, IDRS says **{idrs_level.lower()}**. "
        "That can happen because they look at different things: the model uses glucose, BMI, age and "
        "pregnancies, while IDRS uses age, waist, activity and family history.",
        icon=":material/compare_arrows:",
    )
st.caption(f"The model flags anyone at {m['threshold']:.0%} or above, a low cutoff chosen on purpose so it "
           f"misses fewer people with diabetes. The percentage is the chance in the study group, "
           f"where {m['dataset']['share_with_diabetes']:.0%} had diabetes, not your exact personal chance.")

# ---------- why ----------
st.subheader("Why this result?")
contrib = pd.DataFrame({
    "input": [model.LABELS[k] for k in contributions],
    "effect": list(contributions.values()),
}).sort_values("effect", ascending=False)
ui.contribution_chart(contrib)

top = contrib.iloc[contrib["effect"].abs().argmax()]
direction = "raises" if top["effect"] > 0 else "lowers"
st.write(f"**{top['input']}** {direction} your score the most.")
st.caption("Each bar compares your value with the average person in the training data. "
           "Bars to the right push the score up; bars to the left pull it down.")

# ---------- how good is it ----------
with st.expander(":material/analytics: How good is this model?"):
    t = m["test_metrics"]
    cm = m["confusion_matrix"]
    st.write(f"Tested on **{m['dataset']['test_rows']} people the model never saw** during training.")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Recall", f"{t['recall']:.0%}", help="Of people who really had diabetes, the share it flagged.")
    k2.metric("Precision", f"{t['precision']:.0%}", help="Of people it flagged, the share who really had diabetes.")
    k3.metric("Accuracy", f"{t['accuracy']:.0%}", help="Share of all predictions that were right.")
    k4.metric("ROC AUC", f"{t['roc_auc']:.2f}", help="How well it ranks people by risk. 0.5 is guessing, 1.0 is perfect.")

    st.markdown("**What happened on the test set**")
    st.dataframe(pd.DataFrame({
        "": ["Really had diabetes", "Really did not"],
        "Model said higher risk": [f"{cm['tp']} caught", f"{cm['fp']} false alarms"],
        "Model said low risk": [f"{cm['fn']} missed", f"{cm['tn']} correctly cleared"],
    }), hide_index=True, width="stretch")
    st.caption("For screening, a missed case is worse than a false alarm (which only costs a blood test), "
               "so the cutoff was set to catch about 80% of cases.")

    st.markdown("**Why logistic regression?**")
    comp = pd.DataFrame(m["cv_comparison"])[["Inputs", "Model", "ROC AUC", "Accuracy"]]
    st.dataframe(comp, hide_index=True, width="stretch")
    st.caption("Cross-validation on the training data. The simple model did as well as the complex ones, "
               "and 4 inputs did as well as all 8, so the simplest, most explainable option was chosen.")

    st.markdown("**Limitations**")
    st.write(f"• Trained on {m['dataset']['rows']} people: {m['dataset']['population']}. "
             "It may not fit other groups as well, including Indian adults, who often develop diabetes at a lower BMI.")
    st.write("• The model expects a 2-hour glucose test; an after-meal reading is only a rough stand-in.")
    st.write("• Small test set, so these scores could move by a few points.")
    st.caption(f"Model trained {m['trained_on']}. Full details: notebooks/train_diabetes_model.ipynb.")
