"""All database code lives here so every page shares the same data."""
import os
import random
import sqlite3
import tempfile
import uuid
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

# Saved next to this file, so it works whichever folder you start the app from
DB_FILE = str(Path(__file__).parent / "health.db")

GLUCOSE_CONTEXTS = ["Fasting", "Before meal", "After meal", "Random"]


def demo_mode():
    """True for the online version: set demo_mode = true in Streamlit secrets
    (or the DEMO_MODE=1 environment variable). On your own computer it is off."""
    if os.environ.get("DEMO_MODE") == "1":
        return True
    try:
        import streamlit as st
        return bool(st.secrets.get("demo_mode", False))
    except Exception:  # no secrets file on your computer
        return False


def db_file():
    """Which database file to use.
    Online (demo mode) every visitor gets their own temporary file, so nobody
    sees anyone else's data and it disappears when they leave."""
    if not demo_mode():
        return DB_FILE
    import streamlit as st
    if "db_file" not in st.session_state:
        st.session_state["db_file"] = os.path.join(
            tempfile.gettempdir(), f"health_{uuid.uuid4().hex}.db")
    return st.session_state["db_file"]


def conn():
    return sqlite3.connect(db_file())



def init_db():
    with conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS profile(
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT, age INTEGER, sex TEXT,
                height_cm REAL, weight_kg REAL, waist_cm REAL,
                family INTEGER, activity INTEGER
            );
            CREATE TABLE IF NOT EXISTS activity_log(
                day TEXT PRIMARY KEY,
                sleep_hours REAL, exercise_min INTEGER, steps INTEGER
            );
            CREATE TABLE IF NOT EXISTS meal_log(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day TEXT, meal_type TEXT, food TEXT, servings REAL,
                calories REAL, carbs REAL, protein REAL, fat REAL
            );
            CREATE TABLE IF NOT EXISTS glucose_log(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day TEXT, context TEXT, value REAL,
                measured_at TEXT
            );
            CREATE TABLE IF NOT EXISTS intake_log(
                day TEXT PRIMARY KEY,
                water INTEGER, tea INTEGER, chai INTEGER
            );
            CREATE TABLE IF NOT EXISTS medicines(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, dose TEXT, slot TEXT
            );
            CREATE TABLE IF NOT EXISTS medicine_taken(
                day TEXT, med_id INTEGER,
                PRIMARY KEY (day, med_id)
            );
            """
        )

        # Older databases were created before readings had a time: add the column
        columns = {row[1] for row in c.execute("PRAGMA table_info(glucose_log)").fetchall()}
        if "measured_at" not in columns:
            c.execute("ALTER TABLE glucose_log ADD COLUMN measured_at TEXT")


def _since(days):
    return str(date.today() - timedelta(days=days))


# ---------- profile ----------
def save_profile(name, age, sex, height_cm, weight_kg, waist_cm, family, activity):
    with conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO profile VALUES (1,?,?,?,?,?,?,?,?)",
            (name, age, sex, height_cm, weight_kg, waist_cm, family, activity),
        )


def get_profile():
    with conn() as c:
        c.row_factory = sqlite3.Row
        row = c.execute("SELECT * FROM profile WHERE id = 1").fetchone()
        return dict(row) if row else None


# ---------- sleep and exercise ----------
def save_activity(day, sleep_hours, exercise_min, steps):
    with conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO activity_log VALUES (?,?,?,?)",
            (str(day), sleep_hours, exercise_min, steps),
        )


def get_activity(days=14):
    with conn() as c:
        df = pd.read_sql_query(
            "SELECT * FROM activity_log WHERE day >= ? ORDER BY day", c, params=(_since(days),)
        )
    if not df.empty:
        df["day"] = pd.to_datetime(df["day"])
    return df


def get_activity_day(day):
    """Saved sleep, exercise and steps for one day, or None."""
    with conn() as c:
        row = c.execute(
            "SELECT sleep_hours, exercise_min, steps FROM activity_log WHERE day = ?", (str(day),)
        ).fetchone()
    if row:
        return {"sleep_hours": row[0], "exercise_min": row[1], "steps": row[2]}
    return None


# ---------- meals ----------
def add_meal(day, meal_type, food, servings, calories, carbs, protein, fat):
    with conn() as c:
        c.execute(
            "INSERT INTO meal_log(day, meal_type, food, servings, calories, carbs, protein, fat) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (str(day), meal_type, food, float(servings), float(calories),
             float(carbs), float(protein), float(fat)),
        )


def get_meals(day):
    with conn() as c:
        return pd.read_sql_query(
            "SELECT meal_type, food, servings, calories, carbs, protein, fat "
            "FROM meal_log WHERE day = ? ORDER BY id", c, params=(str(day),)
        )


def clear_meals(day):
    with conn() as c:
        c.execute("DELETE FROM meal_log WHERE day = ?", (str(day),))


def daily_totals(days=7):
    with conn() as c:
        df = pd.read_sql_query(
            "SELECT day, SUM(calories) AS calories, SUM(carbs) AS carbs, "
            "SUM(protein) AS protein, SUM(fat) AS fat "
            "FROM meal_log WHERE day >= ? GROUP BY day ORDER BY day", c, params=(_since(days),)
        )
    if not df.empty:
        df["day"] = pd.to_datetime(df["day"])
    return df


# ---------- glucose ----------

def add_glucose(day, context, value, measured_at=None):
    if measured_at is not None and hasattr(measured_at, "strftime"):
        measured_at = measured_at.strftime("%H:%M:%S")

    with conn() as c:
        c.execute(
            """
            INSERT INTO glucose_log
                (day, context, value, measured_at)
            VALUES (?, ?, ?, ?)
            """,
            (str(day), context, float(value), measured_at),
        )


def get_glucose(days=30):
    with conn() as c:
        df = pd.read_sql_query(
            """
            SELECT * FROM glucose_log
            WHERE day >= ?
            ORDER BY day, measured_at, id
            """,
            c,
            params=(_since(days),),
        )

    if not df.empty:
        df["day"] = pd.to_datetime(df["day"])

    return df


def get_glucose_timed(days=30):
    with conn() as c:
        df = pd.read_sql_query(
            """
            SELECT day, measured_at, value, context
            FROM glucose_log
            WHERE day >= ? AND measured_at IS NOT NULL
              AND measured_at != ''
            ORDER BY day, measured_at, id
            """,
            c,
            params=(_since(days),),
        )

    if df.empty:
        return df.assign(ts=pd.Series(dtype="datetime64[ns]"))

    df["day"] = pd.to_datetime(df["day"])
    df["ts"] = pd.to_datetime(
        df["day"].dt.strftime("%Y-%m-%d")
        + " "
        + df["measured_at"].astype(str),
        errors="coerce",
    )

    df = df.dropna(subset=["ts"])
    return df.sort_values(["day", "ts"]).reset_index(drop=True)

        


# ---------- demo data ----------
def seed_demo():
    """Fake user + 2 weeks of fake data so the demo looks rich instantly.
    Replaces any existing logs (but keeps your medicines list)."""
    save_profile("Priya Sharma", 32, "Female", 160, 68, 88, 1, 2)
    random.seed(1)
    with conn() as c:
        for table in ("meal_log", "glucose_log", "activity_log", "intake_log"):
            c.execute(f"DELETE FROM {table}")
    for i in range(14):
        d = date.today() - timedelta(days=13 - i)
        save_activity(d, round(random.uniform(5, 8), 1),
                      random.choice([0, 0, 10, 20, 30, 45]),
                      random.randint(2000, 9000))
        rice = random.choice([1, 1.5, 2])
        add_meal(d, "Breakfast", "Poha (1 plate)", 1, 250, 40, 5, 8)
        add_meal(d, "Lunch", "Cooked white rice (1 cup)", rice, 200 * rice, 44 * rice, 4 * rice, 0.4 * rice)
        add_meal(d, "Lunch", "Dal (1 katori)", 1, 120, 18, 7, 2)
        add_meal(d, "Snack", "Chai with sugar (1 cup)", 1, 70, 11, 2, 2.5)
        add_meal(d, "Dinner", "Roti / chapati (1 medium)", 2, 200, 36, 6, 5)

        # Three timed readings a day, so the spike finder has before/after pairs
        fasting = round(100 + i * 0.7 + random.uniform(-8, 8))
        before_lunch = fasting + round(random.uniform(-3, 8))
        after_lunch = round(before_lunch + 14 + rice * 11 + random.uniform(-8, 10))
        add_glucose(d, "Fasting", fasting, "07:30:00")
        add_glucose(d, "Before meal", before_lunch, "13:00:00")
        add_glucose(d, "After meal", after_lunch, "14:30:00")

        save_intake(d, random.randint(4, 9), random.choice([0, 0, 1]), random.choice([1, 2, 2, 3]))


def clear_all():
    """Delete the profile and every log (medicines too)."""
    with conn() as c:
        for table in ("profile", "meal_log", "glucose_log", "activity_log",
                      "intake_log", "medicines", "medicine_taken"):
            c.execute(f"DELETE FROM {table}")


# ---------- water, tea, chai ----------
def get_intake(day):
    with conn() as c:
        row = c.execute(
            "SELECT water, tea, chai FROM intake_log WHERE day = ?", (str(day),)
        ).fetchone()
    if row:
        return {"water": row[0], "tea": row[1], "chai": row[2]}
    return {"water": 0, "tea": 0, "chai": 0}


def save_intake(day, water, tea, chai):
    with conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO intake_log VALUES (?,?,?,?)",
            (str(day), int(water), int(tea), int(chai)),
        )


def get_intake_history(days=7):
    with conn() as c:
        df = pd.read_sql_query(
            "SELECT * FROM intake_log WHERE day >= ? ORDER BY day", c, params=(_since(days),)
        )
    if not df.empty:
        df["day"] = pd.to_datetime(df["day"])
    return df


# ---------- medicines ----------
def add_medicine(name, dose, slot):
    with conn() as c:
        cur = c.execute(
            "INSERT INTO medicines(name, dose, slot) VALUES (?,?,?)", (name, dose, slot)
        )
        return cur.lastrowid


def get_medicines():
    with conn() as c:
        return pd.read_sql_query("SELECT id, name, dose, slot FROM medicines ORDER BY id", c)


def delete_medicine(med_id):
    with conn() as c:
        c.execute("DELETE FROM medicine_taken WHERE med_id = ?", (int(med_id),))
        c.execute("DELETE FROM medicines WHERE id = ?", (int(med_id),))


def get_taken(day):
    with conn() as c:
        rows = c.execute(
            "SELECT med_id FROM medicine_taken WHERE day = ?", (str(day),)
        ).fetchall()
    return {r[0] for r in rows}


def set_taken(day, med_id, taken):
    with conn() as c:
        if taken:
            c.execute("INSERT OR IGNORE INTO medicine_taken VALUES (?,?)", (str(day), int(med_id)))
        else:
            c.execute("DELETE FROM medicine_taken WHERE day = ? AND med_id = ?", (str(day), int(med_id)))