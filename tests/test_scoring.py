"""Tests for the scoring rules in scoring.py."""
import pandas as pd
import pytest

import scoring as sc


# ---------- BMI ----------
def test_bmi_formula():
    # 70 kg, 175 cm -> 70 / 1.75^2 = 22.86
    assert sc.bmi(70, 175) == pytest.approx(22.86, abs=0.01)


@pytest.mark.parametrize("value, label, level", [
    (17.0, "Underweight", "Moderate"),
    (18.5, "Healthy", "Low"),      # lower edge counts as healthy
    (22.9, "Healthy", "Low"),
    (23.0, "Overweight", "Moderate"),  # Indian cut-off, lower than the global 25
    (25.0, "Obese range", "High"),
])
def test_bmi_category_uses_indian_cutoffs(value, label, level):
    assert sc.bmi_category(value) == (label, level)


# ---------- IDRS ----------
def test_idrs_lowest_possible_score():
    # young, slim waist, very active, no family history
    assert sc.idrs_score(age=25, sex="Female", waist_cm=70, activity=0, family=0) == 0


def test_idrs_highest_possible_score():
    assert sc.idrs_score(age=60, sex="Male", waist_cm=105, activity=2, family=2) == 100


def test_idrs_demo_user():
    # age 32 -> 0, female waist 88 -> 10, no exercise -> 30, one parent -> 10
    assert sc.idrs_score(age=32, sex="Female", waist_cm=88, activity=2, family=1) == 50


def test_idrs_waist_limits_differ_by_sex():
    # 85 cm is above the female limit (80) but below the male limit (90)
    female = sc.idrs_score(age=25, sex="Female", waist_cm=85, activity=0, family=0)
    male = sc.idrs_score(age=25, sex="Male", waist_cm=85, activity=0, family=0)
    assert female == 10
    assert male == 0


@pytest.mark.parametrize("age, points", [(34, 0), (35, 20), (49, 20), (50, 30)])
def test_idrs_age_bands(age, points):
    assert sc.idrs_score(age=age, sex="Female", waist_cm=70, activity=0, family=0) == points


@pytest.mark.parametrize("score, category", [(0, "Low"), (20, "Low"), (30, "Moderate"),
                                             (50, "Moderate"), (60, "High"), (100, "High")])
def test_idrs_category(score, category):
    assert sc.idrs_category(score) == category


# ---------- health score ----------
def test_health_score_is_none_without_data():
    empty = pd.DataFrame()
    assert sc.health_score(empty, empty, empty) is None


def test_health_score_full_marks():
    act = pd.DataFrame({"sleep_hours": [8, 8], "exercise_min": [40, 40]})
    gluc = pd.DataFrame({"context": ["Fasting", "Fasting"], "value": [90, 92]})
    water = pd.DataFrame({"water": [8, 9]})
    assert sc.health_score(act, gluc, water) == 100


def test_health_score_only_counts_logged_parts():
    # only sleep and exercise logged, both at half the goal -> 50%
    act = pd.DataFrame({"sleep_hours": [3.5], "exercise_min": [15]})
    assert sc.health_score(act, pd.DataFrame(), pd.DataFrame()) == 50


def test_health_score_drops_with_high_fasting_glucose():
    act = pd.DataFrame({"sleep_hours": [8], "exercise_min": [30]})
    normal = pd.DataFrame({"context": ["Fasting"], "value": [90]})
    high = pd.DataFrame({"context": ["Fasting"], "value": [140]})
    assert sc.health_score(act, high, None) < sc.health_score(act, normal, None)


# ---------- PCOS ----------
@pytest.mark.parametrize("irregular, androgen, ultrasound, supporting, expected", [
    (False, False, False, 0, (0, "Low")),
    (True, False, False, 0, (1, "Moderate")),
    (False, False, False, 2, (0, "Moderate")),  # no main sign, but 2 supporting signs
    (True, True, False, 0, (2, "High")),        # 2 of 3 Rotterdam criteria
    (True, True, True, 3, (3, "High")),
])
def test_pcos_screen(irregular, androgen, ultrasound, supporting, expected):
    assert sc.pcos_screen(irregular, androgen, ultrasound, supporting) == expected


# ---------- lifestyle tips ----------
def test_lifestyle_tips_mention_waist_and_sleep_when_needed():
    profile = {"waist_cm": 95, "sex": "Female", "activity": 2}
    tips = " ".join(sc.lifestyle_tips(profile, avg_sleep=5.5, avg_exercise=5))
    assert "waist" in tips
    assert "sleeping under 7 hours" in tips
    assert "walk" in tips


def test_lifestyle_tips_skip_waist_tip_when_healthy():
    profile = {"waist_cm": 75, "sex": "Female", "activity": 0}
    tips = " ".join(sc.lifestyle_tips(profile, avg_sleep=8, avg_exercise=40))
    assert "waist" not in tips
    assert "sleeping under" not in tips
