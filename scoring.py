"""Scoring logic shared by all pages."""

ACTIVITY_OPTIONS = [
    "Regular exercise + physically active work",
    "Regular exercise OR physically active work",
    "No exercise and desk / sedentary work",
]
FAMILY_OPTIONS = ["No parent with diabetes", "One parent", "Both parents"]


def bmi(weight_kg, height_cm):
    return weight_kg / ((height_cm / 100) ** 2)


def idrs_score(age, sex, waist_cm, activity, family):
    """Indian Diabetes Risk Score (Madras Diabetes Research Foundation).
    NOTE: verify the cutoffs against the published IDRS paper before your final demo.
    """
    pts = 0
    pts += 0 if age < 35 else (20 if age < 50 else 30)
    if sex == "Female":
        pts += 0 if waist_cm < 80 else (10 if waist_cm < 90 else 20)
    else:
        pts += 0 if waist_cm < 90 else (10 if waist_cm < 100 else 20)
    pts += [0, 20, 30][activity]
    pts += [0, 10, 20][family]
    return pts


def idrs_category(score):
    if score < 30:
        return "Low"
    if score < 60:
        return "Moderate"
    return "High"


def lifestyle_tips(profile, avg_sleep=None, avg_exercise=None):
    """Simple rule-based plan. Later you can pass these facts to an LLM
    to write a friendly Hindi/English 7-day plan."""
    tips = []
    waist, sex = profile["waist_cm"], profile["sex"]
    limit = 80 if sex == "Female" else 90
    if waist >= limit:
        tips.append("Your waist is above the healthy limit. Aim for slow, steady weight loss through walking and smaller portions.")
    if profile["activity"] == 2 or (avg_exercise is not None and avg_exercise < 20):
        tips.append("Start with a 10-minute walk after each main meal, then build up to 30 minutes a day, 5 days a week.")
    if avg_sleep is not None and avg_sleep < 7:
        tips.append("You are sleeping under 7 hours on average. Poor sleep can raise blood sugar, so try a fixed bedtime.")
    tips.append("Swap some white rice or maida for millets, brown rice, or whole wheat, and add dal and vegetables to each meal.")
    tips.append("Cut down sugar in tea and sweet drinks.")
    return tips


def pcos_screen(irregular, androgen_signs, ultrasound, supporting):
    """Simple rule-based PCOS screening modelled on the Rotterdam criteria:
    (1) irregular ovulation/periods, (2) signs of excess androgens, (3) polycystic-looking
    ovaries on ultrasound. Two of three suggests seeing a doctor. NOT a diagnosis.
    Returns (criteria_met, level)."""
    met = int(irregular) + int(androgen_signs) + int(ultrasound)
    if met >= 2:
        level = "High"
    elif met == 1 or supporting >= 2:
        level = "Moderate"
    else:
        level = "Low"
    return met, level


def bmi_category(value):
    """BMI bands for Indian adults (lower cut-offs than the WHO global ones).
    Returns (label, level) where level is "Low", "Moderate" or "High" concern."""
    if value < 18.5:
        return "Underweight", "Moderate"
    if value < 23:
        return "Healthy", "Low"
    if value < 25:
        return "Overweight", "Moderate"
    return "Obese range", "High"


def health_score(act, gluc, water_hist):
    """Simple 0-100 tracking score from the last 7 days:
    sleep 25 points, exercise 25, fasting glucose 30, water 20.
    Only the parts that have data are counted. Returns None if there is no data."""
    earned, possible = 0.0, 0.0
    if act is not None and not act.empty:
        earned += 25 * min(act["sleep_hours"].mean() / 7, 1)
        earned += 25 * min(act["exercise_min"].mean() / 30, 1)
        possible += 50
    if gluc is not None and not gluc.empty:
        fasting = gluc[gluc["context"] == "Fasting"]["value"]
        if not fasting.empty:
            f = fasting.mean()
            if f < 100:
                pts = 30
            elif f < 126:
                pts = 30 - (f - 100) / 26 * 18
            else:
                pts = 5
            earned += pts
            possible += 30
    if water_hist is not None and not water_hist.empty:
        earned += 20 * min(water_hist["water"].mean() / 8, 1)
        possible += 20
    if possible == 0:
        return None
    return round(earned / possible * 100)
