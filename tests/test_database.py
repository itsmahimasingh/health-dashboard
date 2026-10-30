"""Tests for database.py. Each test gets its own empty database file."""
import sqlite3
from datetime import date, timedelta

import pytest

import database as db


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_FILE", str(tmp_path / "test.db"))
    monkeypatch.delenv("DEMO_MODE", raising=False)
    db.init_db()


def test_new_database_has_no_profile():
    assert db.get_profile() is None


def test_profile_save_and_load():
    db.save_profile("Asha", 28, "Female", 158, 55, 76, 0, 1)
    p = db.get_profile()
    assert p["name"] == "Asha"
    assert p["age"] == 28
    assert p["waist_cm"] == 76


def test_saving_profile_again_replaces_it():
    db.save_profile("Asha", 28, "Female", 158, 55, 76, 0, 1)
    db.save_profile("Asha", 29, "Female", 158, 54, 75, 0, 1)
    assert db.get_profile()["age"] == 29


def test_activity_for_a_day_is_updated_not_duplicated():
    today = date.today()
    db.save_activity(today, 6, 10, 3000)
    db.save_activity(today, 7.5, 30, 6000)
    assert db.get_activity_day(today) == {"sleep_hours": 7.5, "exercise_min": 30, "steps": 6000}
    assert len(db.get_activity(7)) == 1


def test_glucose_time_is_saved_and_used_for_spikes():
    from datetime import time
    today = date.today()
    db.add_glucose(today, "Before meal", 100, time(13, 0))
    db.add_glucose(today, "After meal", 150, time(14, 30))
    db.add_glucose(today, "Random", 120)  # no time
    assert len(db.get_glucose(1)) == 3
    timed = db.get_glucose_timed(1)
    assert len(timed) == 2
    assert list(timed["ts"].dt.strftime("%H:%M")) == ["13:00", "14:30"]


def test_old_readings_are_left_out_of_recent_results():
    db.add_glucose(date.today() - timedelta(days=40), "Fasting", 95)
    db.add_glucose(date.today(), "Fasting", 98)
    assert len(db.get_glucose(30)) == 1


def test_meal_totals_per_day():
    today = date.today()
    db.add_meal(today, "Lunch", "Rice", 1, 200, 44, 4, 0.4)
    db.add_meal(today, "Dinner", "Roti", 2, 200, 36, 6, 5)
    totals = db.daily_totals(7)
    assert totals["carbs"].iloc[0] == pytest.approx(80)
    db.clear_meals(today)
    assert db.get_meals(today).empty


def test_water_starts_at_zero_and_saves():
    today = date.today()
    assert db.get_intake(today) == {"water": 0, "tea": 0, "chai": 0}
    db.save_intake(today, 5, 1, 2)
    assert db.get_intake(today) == {"water": 5, "tea": 1, "chai": 2}


def test_medicines_checklist():
    today = date.today()
    med = db.add_medicine("Vitamin D", "1 tablet", "Morning")
    db.set_taken(today, med, True)
    assert db.get_taken(today) == {med}
    db.set_taken(today, med, False)
    assert db.get_taken(today) == set()
    db.delete_medicine(med)
    assert db.get_medicines().empty


def test_demo_data_fills_two_weeks_with_timed_readings():
    db.seed_demo()
    assert db.get_profile()["name"] == "Priya Sharma"
    assert len(db.get_activity(14)) == 14
    assert len(db.get_glucose(14)) == 42           # 3 readings a day
    assert len(db.get_glucose_timed(14)) == 42     # all with a time
    assert not db.get_intake_history(14).empty


def test_demo_data_can_be_loaded_twice_without_duplicates():
    db.seed_demo()
    db.seed_demo()
    assert len(db.get_glucose(14)) == 42


def test_clear_all_removes_everything():
    db.seed_demo()
    db.add_medicine("Vitamin D", "1 tablet", "Morning")
    db.clear_all()
    assert db.get_profile() is None
    assert db.get_glucose(30).empty
    assert db.get_medicines().empty


def test_old_database_gets_the_time_column_added(tmp_path, monkeypatch):
    # a database made before readings had a time
    old = tmp_path / "old.db"
    with sqlite3.connect(old) as c:
        c.execute("CREATE TABLE glucose_log(id INTEGER PRIMARY KEY, day TEXT, context TEXT, value REAL)")
        c.execute("INSERT INTO glucose_log(day, context, value) VALUES (?, 'Fasting', 101)",
                  (str(date.today()),))
    monkeypatch.setattr(db, "DB_FILE", str(old))
    db.init_db()
    assert len(db.get_glucose(1)) == 1
    assert db.get_glucose_timed(1).empty  # the old reading has no time, and nothing crashes
