"""Use the diabetes model trained in notebooks/train_diabetes_model.ipynb.

The model is a logistic regression saved as plain numbers in models/diabetes_model.json,
so the app only needs basic Python here (no scikit-learn).
"""
import json
import math
from pathlib import Path

MODEL_FILE = Path(__file__).parent / "models" / "diabetes_model.json"

# Friendly names for the four inputs
LABELS = {
    "Glucose": "Glucose after a meal",
    "BMI": "BMI",
    "Age": "Age",
    "Pregnancies": "Number of pregnancies",
}


def load_model(path=MODEL_FILE):
    with open(path) as f:
        return json.load(f)


def predict(inputs, m):
    """inputs: dict like {"Glucose": 140, "BMI": 27, "Age": 32, "Pregnancies": 1}.

    Returns (probability, contributions). Each contribution says how much one input
    pushed the score up (positive) or down (negative) compared with an average
    person in the training data. They add up, with the baseline, to the final score.
    """
    contributions = {}
    for name, mean, scale, coef in zip(m["features"], m["mean"], m["scale"], m["coef"]):
        contributions[name] = coef * (inputs[name] - mean) / scale
    z = m["intercept"] + sum(contributions.values())
    probability = 1 / (1 + math.exp(-z))
    return probability, contributions


def risk_level(probability, m):
    """Low below the screening cutoff, Moderate up to 50%, High from 50%."""
    if probability < m["threshold"]:
        return "Low"
    if probability < 0.5:
        return "Moderate"
    return "High"
