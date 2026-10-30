"""Tests for the trained diabetes model and model.py."""
import math

import pytest

import model


@pytest.fixture(scope="module")
def m():
    return model.load_model()


HEALTHY = {"Glucose": 95, "BMI": 21, "Age": 25, "Pregnancies": 0}
HIGH_RISK = {"Glucose": 190, "BMI": 38, "Age": 55, "Pregnancies": 5}


def test_model_file_has_everything_the_app_needs(m):
    for key in ["features", "mean", "scale", "coef", "intercept", "threshold",
                "test_metrics", "confusion_matrix", "dataset"]:
        assert key in m
    assert m["features"] == ["Glucose", "BMI", "Age", "Pregnancies"]
    assert len(m["mean"]) == len(m["scale"]) == len(m["coef"]) == 4


def test_probability_is_between_0_and_1(m):
    for inputs in [HEALTHY, HIGH_RISK]:
        prob, _ = model.predict(inputs, m)
        assert 0 < prob < 1


def test_healthy_person_is_low_risk(m):
    prob, _ = model.predict(HEALTHY, m)
    assert model.risk_level(prob, m) == "Low"


def test_high_risk_person_is_high_risk(m):
    prob, _ = model.predict(HIGH_RISK, m)
    assert model.risk_level(prob, m) == "High"


@pytest.mark.parametrize("feature", ["Glucose", "BMI", "Age", "Pregnancies"])
def test_more_of_any_input_never_lowers_risk(m, feature):
    # every weight the model learned is positive, so risk should go up
    low, _ = model.predict(HEALTHY, m)
    raised = dict(HEALTHY, **{feature: HEALTHY[feature] + 10})
    high, _ = model.predict(raised, m)
    assert high > low


def test_contributions_add_up_to_the_score(m):
    prob, contributions = model.predict(HIGH_RISK, m)
    logit = m["intercept"] + sum(contributions.values())
    assert 1 / (1 + math.exp(-logit)) == pytest.approx(prob)


def test_average_person_has_zero_contributions(m):
    average = dict(zip(m["features"], m["mean"]))
    _, contributions = model.predict(average, m)
    assert all(abs(c) < 1e-9 for c in contributions.values())


def test_risk_levels_follow_the_cutoff(m):
    t = m["threshold"]
    assert model.risk_level(t - 0.01, m) == "Low"
    assert model.risk_level(t, m) == "Moderate"
    assert model.risk_level(0.5, m) == "High"


def test_saved_test_results_meet_the_recall_goal(m):
    # the cutoff was chosen to catch about 80% of diabetes cases
    assert m["test_metrics"]["recall"] >= 0.75
    cm = m["confusion_matrix"]
    assert cm["tp"] + cm["fn"] + cm["tn"] + cm["fp"] == m["dataset"]["test_rows"]
