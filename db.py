# -*- coding: utf-8 -*-
"""
db.py – All database and CSV functions for HabitNourish.
"""

import csv
import hashlib
import os
import sqlite3
from datetime import date, timedelta


# ─────────────────────────────────────────────────────────────────────────────
# PATH HELPERS  (Android-safe)
# ─────────────────────────────────────────────────────────────────────────────
def get_data_dir():
    """Writable data directory — works on desktop and Android."""
    try:
        from android.storage import app_storage_path   # noqa
        return app_storage_path()
    except ImportError:
        return os.path.dirname(os.path.abspath(__file__))

def get_db_path():
    return os.path.join(get_data_dir(), "nutriguide.db")

def get_csv_path(filename):
    """Find a CSV: first in data dir (user-editable copy), then alongside script."""
    candidates = [
        os.path.join(get_data_dir(), filename),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), filename),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[1]


# ─────────────────────────────────────────────────────────────────────────────
# CSV FOOD LOADER
# ─────────────────────────────────────────────────────────────────────────────
def load_master_foods():
    """Returns list of dicts from master_foods.csv (per-100g values)."""
    foods = []
    path = get_csv_path("master_foods.csv")
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            foods.append({
                "type":     row["type"],
                "name":     row["name"],
                "calories": float(row["calories"]),
                "protein":  float(row["protein"]),
                "carbs":    float(row["carbs"]),
                "fat":      float(row["fat"]),
                "fiber":    float(row["fiber"]),
                "sugar":    float(row["sugar"]),
                "sodium":   float(row["sodium"]),
                "category": row["category"],
                "source":   "master",
            })
    return foods

def load_user_foods(email):
    """Returns user-created foods from user_foods.csv filtered by email."""
    foods = []
    path = get_csv_path("user_foods.csv")
    if not os.path.exists(path):
        return foods
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("created_by", "") == email:
                foods.append({
                    "type":     row["type"],
                    "name":     row["name"],
                    "calories": float(row["calories"]),
                    "protein":  float(row["protein"]),
                    "carbs":    float(row["carbs"]),
                    "fat":      float(row["fat"]),
                    "fiber":    float(row.get("fiber", 0)),
                    "sugar":    float(row.get("sugar", 0)),
                    "sodium":   float(row.get("sodium", 0)),
                    "category": row["category"],
                    "source":   "user",
                })
    return foods

def save_user_food(food_dict, email):
    """Append a new food to user_foods.csv."""
    path = get_csv_path("user_foods.csv")
    file_exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "type","name","calories","protein","carbs","fat",
            "fiber","sugar","sodium","category","created_by"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "type":       food_dict["type"],
            "name":       food_dict["name"],
            "calories":   food_dict["calories"],
            "protein":    food_dict["protein"],
            "carbs":      food_dict["carbs"],
            "fat":        food_dict["fat"],
            "fiber":      food_dict.get("fiber", 0),
            "sugar":      food_dict.get("sugar", 0),
            "sodium":     food_dict.get("sodium", 0),
            "category":   food_dict["category"],
            "created_by": email,
        })

def master_food_exists(name):
    """Case-insensitive check whether a food name is already in the master sheet."""
    target = name.strip().lower()
    return any(f["name"].strip().lower() == target for f in load_master_foods())

def save_master_food(food_dict):
    """Append a new food to master_foods.csv (shared, app-wide list).

    Returns (ok, error_message). Refuses duplicates by name (case-insensitive).
    """
    name = food_dict.get("name", "").strip()
    if not name:
        return False, "Food name is required."
    if master_food_exists(name):
        return False, f'"{name}" already exists in the master sheet.'

    path = get_csv_path("master_foods.csv")
    file_exists = os.path.exists(path)
    fieldnames = ["type", "name", "calories", "protein", "carbs",
                  "fat", "fiber", "sugar", "sodium", "category"]
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "type":     food_dict["type"],
            "name":     name,
            "calories": food_dict.get("calories", 0),
            "protein":  food_dict.get("protein", 0),
            "carbs":    food_dict.get("carbs", 0),
            "fat":      food_dict.get("fat", 0),
            "fiber":    food_dict.get("fiber", 0),
            "sugar":    food_dict.get("sugar", 0),
            "sodium":   food_dict.get("sodium", 0),
            "category": food_dict.get("category", "Custom"),
        })
    return True, None

def get_all_foods(email=""):
    """Master + user foods combined."""
    foods = load_master_foods()
    if email:
        foods += load_user_foods(email)
    return foods

def foods_by_type(meal_type, email=""):
    return [f for f in get_all_foods(email) if f["type"] == meal_type]

def scale_nutrients(food, grams):
    """Scale per-100g values to actual serving size."""
    factor = grams / 100.0
    return {k: round(food[k] * factor, 1) if isinstance(food[k], float) else food[k]
            for k in food}


# ─────────────────────────────────────────────────────────────────────────────
# DATABASE INIT
# ─────────────────────────────────────────────────────────────────────────────
def get_conn():
    return sqlite3.connect(get_db_path())

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        email       TEXT UNIQUE,
        mobile      TEXT UNIQUE,
        password    TEXT,
        name        TEXT,
        age         INTEGER,
        weight      REAL,
        height      REAL,
        gender      TEXT,
        activity    TEXT,
        goal        TEXT,
        diet_pref   TEXT,
        target      INTEGER DEFAULT 2000,
        reset_token TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS food_log(
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id   INTEGER,
        date      TEXT,
        meal      TEXT,
        food_name TEXT,
        grams     REAL,
        calories  REAL,
        protein   REAL,
        carbs     REAL,
        fat       REAL,
        fiber     REAL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")
    conn.commit()
    c.execute("""CREATE TABLE IF NOT EXISTS meal_plan(
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id   INTEGER,
        plan_date TEXT,
        meal      TEXT,
        food_name TEXT,
        grams     REAL,
        calories  REAL,
        protein   REAL,
        carbs     REAL,
        fat       REAL,
        fiber     REAL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")
    conn.commit()
    c.execute("""CREATE TABLE IF NOT EXISTS lifestyle_log(
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id       INTEGER,
        date          TEXT,
        sleep_hours   REAL,
        stress_level  INTEGER,
        exercise_min  INTEGER,
        water_liters  REAL,
        screen_hours  REAL,
        notes         TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")
    conn.commit()
    
    c.execute("""CREATE TABLE IF NOT EXISTS meal_plans(
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_name   TEXT UNIQUE,
        description TEXT,
        created_at  TEXT
    )""")
    conn.commit()
    
    c.execute("""CREATE TABLE IF NOT EXISTS meal_plan_items(
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id     INTEGER,
        day         INTEGER,
        meal_type   TEXT,
        food_name   TEXT,
        grams       REAL,
        calories    REAL,
        protein     REAL,
        carbs       REAL,
        fat         REAL,
        fiber       REAL,
        FOREIGN KEY(plan_id) REFERENCES meal_plans(id) ON DELETE CASCADE
    )""")
    conn.commit()
    
    c.execute("""CREATE TABLE IF NOT EXISTS user_selected_plan(
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER UNIQUE,
        plan_id     INTEGER,
        selected_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(plan_id) REFERENCES meal_plans(id)
    )""")
    conn.commit()

    c.execute("""CREATE TABLE IF NOT EXISTS user_targets(
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER UNIQUE,
        calories        INTEGER DEFAULT 2000,
        protein         REAL DEFAULT 50,
        carbs           REAL DEFAULT 260,
        fat             REAL DEFAULT 70,
        fiber           REAL DEFAULT 25,
        sugar           REAL DEFAULT 50,
        sleep_hours     REAL DEFAULT 8,
        exercise_min    INTEGER DEFAULT 30,
        water_liters    REAL DEFAULT 2.5,
        stress_level    INTEGER DEFAULT 5,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")
    conn.commit()

    # Migration guard: add missing columns safely
    existing = {row[1] for row in c.execute("PRAGMA table_info(food_log)")}
    for col, dtype in [("food_name","TEXT"), ("grams","REAL"),
                        ("fiber","REAL"), ("user_id","INTEGER"),
                        ("sugar","REAL")]:
        if col not in existing:
            c.execute(f"ALTER TABLE food_log ADD COLUMN {col} {dtype}")

    existing_u = {row[1] for row in c.execute("PRAGMA table_info(users)")}
    for col, dtype in [("reset_token","TEXT"), ("diet_pref","TEXT"),
                        ("target","INTEGER DEFAULT 2000")]:
        if col not in existing_u:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} {dtype}")

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# USER AUTH
# ─────────────────────────────────────────────────────────────────────────────
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def register_user(email, mobile, password, name):
    try:
        conn = get_conn()
        conn.execute(
            "INSERT INTO users(email,mobile,password,name) VALUES(?,?,?,?)",
            (email.lower().strip(), mobile.strip(), hash_pw(password), name))
        conn.commit()
        uid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return uid, None
    except sqlite3.IntegrityError:
        return None, "Email or mobile already registered."

def login_user(identifier, password):
    """identifier = email or mobile."""
    conn = get_conn()
    row = conn.execute(
        "SELECT id,name FROM users WHERE (email=? OR mobile=?) AND password=?",
        (identifier.lower().strip(), identifier.strip(), hash_pw(password))
    ).fetchone()
    conn.close()
    return row  # (id, name) or None

def set_reset_token(identifier, token):
    conn = get_conn()
    conn.execute(
        "UPDATE users SET reset_token=? WHERE email=? OR mobile=?",
        (token, identifier.lower().strip(), identifier.strip()))
    conn.commit()
    conn.close()

def reset_password(identifier, token, new_pw):
    conn = get_conn()
    row = conn.execute(
        "SELECT id FROM users WHERE (email=? OR mobile=?) AND reset_token=?",
        (identifier.lower().strip(), identifier.strip(), token)
    ).fetchone()
    if row:
        conn.execute("UPDATE users SET password=?,reset_token=NULL WHERE id=?",
                     (hash_pw(new_pw), row[0]))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def get_user_profile(user_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT name,age,weight,height,gender,activity,goal,diet_pref,target,email,mobile "
        "FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    if row:
        return dict(zip(
            ["name","age","weight","height","gender","activity",
             "goal","diet_pref","target","email","mobile"], row))
    return {}

def save_user_profile(user_id, p):
    conn = get_conn()
    conn.execute("""UPDATE users SET name=?,age=?,weight=?,height=?,
                    gender=?,activity=?,goal=?,diet_pref=?,target=?
                    WHERE id=?""",
                 (p["name"], p["age"], p["weight"], p["height"],
                  p["gender"], p["activity"], p["goal"], p["diet_pref"],
                  p["target"], user_id))
    conn.commit()
    conn.close()

def calc_target(p):
    ACTIVITY = {"Sedentary":1.2,"Lightly Active":1.375,
                "Moderately Active":1.55,"Very Active":1.725}
    GOAL = {"Lose Weight":-500,"Maintain Weight":0,"Gain Muscle":300}
    if p["gender"] == "Male":
        bmr = 88.362 + 13.397*p["weight"] + 4.799*p["height"] - 5.677*p["age"]
    else:
        bmr = 447.593 + 9.247*p["weight"] + 3.098*p["height"] - 4.330*p["age"]
    return round(bmr * ACTIVITY.get(p["activity"],1.2) + GOAL.get(p["goal"],0))


# ─────────────────────────────────────────────────────────────────────────────
# FOOD LOG
# ─────────────────────────────────────────────────────────────────────────────
def log_food(user_id, meal, food, grams):
    s = scale_nutrients(food, grams)
    conn = get_conn()
    conn.execute(
        "INSERT INTO food_log(user_id,date,meal,food_name,grams,calories,"
        "protein,carbs,fat,fiber) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (user_id, str(date.today()), meal, food["name"], grams,
         s["calories"], s["protein"], s["carbs"], s["fat"], s["fiber"]))
    conn.commit()
    conn.close()

def log_plan_item(user_id, meal, item):
    """Log a meal-plan item whose nutrient values are ALREADY scaled for its
    grams. Unlike log_food(), this does not re-scale (plan items store absolute
    values, not per-100g), so it inserts the values as-is."""
    conn = get_conn()
    conn.execute(
        "INSERT INTO food_log(user_id,date,meal,food_name,grams,calories,"
        "protein,carbs,fat,fiber) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (user_id, str(date.today()), meal, item["food_name"], item["grams"],
         item["calories"], item["protein"], item["carbs"],
         item["fat"], item["fiber"]))
    conn.commit()
    conn.close()

def delete_log_entry(entry_id):
    conn = get_conn()
    conn.execute("DELETE FROM food_log WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()

def update_log_entry(entry_id, new_grams):
    conn = get_conn()
    row = conn.execute(
        "SELECT grams,calories,protein,carbs,fat,fiber FROM food_log WHERE id=?",
        (entry_id,)).fetchone()
    if row and row[0]:
        factor = new_grams / row[0]
        conn.execute(
            "UPDATE food_log SET grams=?,calories=?,protein=?,carbs=?,fat=?,fiber=? "
            "WHERE id=?",
            (new_grams,
             round(row[1]*factor, 1), round(row[2]*factor, 1),
             round(row[3]*factor, 1), round(row[4]*factor, 1),
             round(row[5]*factor, 1), entry_id))
        conn.commit()
    conn.close()

def today_log(user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id,meal,food_name,grams,calories,protein,carbs,fat,fiber "
        "FROM food_log WHERE user_id=? AND date=? ORDER BY id DESC",
        (user_id, str(date.today()))).fetchall()
    conn.close()
    return [dict(zip(["id","meal","food_name","grams","calories",
                       "protein","carbs","fat","fiber"], r)) for r in rows]

def today_totals(user_id):
    rows = today_log(user_id)
    t = {"calories":0.0,"protein":0.0,"carbs":0.0,"fat":0.0,"fiber":0.0}
    for r in rows:
        for k in t:
            t[k] += r[k]
    return t

def week_log(user_id):
    """Last 7 days: returns list of (date_str, calories)."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT date, SUM(calories) FROM food_log WHERE user_id=? "
        "AND date >= ? GROUP BY date ORDER BY date",
        (user_id, str(date.today() - timedelta(days=6)))).fetchall()
    conn.close()
    return rows

def meal_breakdown(user_id):
    """Today's calories per meal type."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT meal, SUM(calories) FROM food_log WHERE user_id=? AND date=? "
        "GROUP BY meal", (user_id, str(date.today()))).fetchall()
    conn.close()
    return dict(rows)

def week_nutrients(user_id):
    """Last 7 days: per-day totals for all tracked nutrients."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT date, SUM(calories), SUM(protein), SUM(carbs), "
        "SUM(fat), SUM(fiber), SUM(COALESCE(sugar,0)) "
        "FROM food_log WHERE user_id=? AND date>=? "
        "GROUP BY date ORDER BY date",
        (user_id, str(date.today() - timedelta(days=6)))).fetchall()
    conn.close()
    result = {}
    for r in rows:
        result[r[0]] = {
            "calories": r[1] or 0, "protein": r[2] or 0,
            "carbs":    r[3] or 0, "fat":     r[4] or 0,
            "fiber":    r[5] or 0, "sugar":   r[6] or 0,
        }
    return result


# ─────────────────────────────────────────────────────────────────────────────
# MEAL PLAN
# ─────────────────────────────────────────────────────────────────────────────
def save_plan_entry(user_id, plan_date, meal, food, grams):
    s = scale_nutrients(food, grams)
    conn = get_conn()
    conn.execute(
        "INSERT INTO meal_plan(user_id,plan_date,meal,food_name,grams,"
        "calories,protein,carbs,fat,fiber) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (user_id, plan_date, meal, food["name"], grams,
         s["calories"], s["protein"], s["carbs"], s["fat"], s["fiber"]))
    conn.commit()
    conn.close()

def delete_plan_entry(entry_id):
    conn = get_conn()
    conn.execute("DELETE FROM meal_plan WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()

def get_plan_for_range(user_id, start_date, end_date):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id,plan_date,meal,food_name,grams,calories,protein,carbs,fat,fiber "
        "FROM meal_plan WHERE user_id=? AND plan_date>=? AND plan_date<=? "
        "ORDER BY plan_date,meal",
        (user_id, str(start_date), str(end_date))).fetchall()
    conn.close()
    return [dict(zip(["id","plan_date","meal","food_name","grams","calories",
                       "protein","carbs","fat","fiber"], r)) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# LIFESTYLE TRACKING
# ─────────────────────────────────────────────────────────────────────────────
def save_lifestyle_log(user_id, data):
    """Save or update lifestyle data for today."""
    conn = get_conn()
    today = str(date.today())
    existing = conn.execute(
        "SELECT id FROM lifestyle_log WHERE user_id=? AND date=?",
        (user_id, today)).fetchone()
    if existing:
        conn.execute(
            """UPDATE lifestyle_log SET sleep_hours=?, stress_level=?,
               exercise_min=?, water_liters=?, screen_hours=?, notes=?
               WHERE id=?""",
            (data.get("sleep_hours"), data.get("stress_level"),
             data.get("exercise_min"), data.get("water_liters"),
             data.get("screen_hours"), data.get("notes"), existing[0]))
    else:
        conn.execute(
            """INSERT INTO lifestyle_log (user_id, date, sleep_hours, stress_level,
               exercise_min, water_liters, screen_hours, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, today, data.get("sleep_hours"), data.get("stress_level"),
             data.get("exercise_min"), data.get("water_liters"),
             data.get("screen_hours"), data.get("notes")))
    conn.commit()
    conn.close()

def get_today_lifestyle(user_id):
    conn = get_conn()
    row = conn.execute(
        """SELECT sleep_hours, stress_level, exercise_min, water_liters,
           screen_hours, notes FROM lifestyle_log
           WHERE user_id=? AND date=?""",
        (user_id, str(date.today()))).fetchone()
    conn.close()
    if row:
        return {
            "sleep_hours":  row[0] or 0,
            "stress_level": row[1] or 0,
            "exercise_min": row[2] or 0,
            "water_liters": row[3] or 0,
            "screen_hours": row[4] or 0,
            "notes":        row[5] or ""
        }
    return None

def get_lifestyle_history(user_id, days=7):
    conn = get_conn()
    start_date = str(date.today() - timedelta(days=days-1))
    rows = conn.execute(
        """SELECT date, sleep_hours, stress_level, exercise_min,
           water_liters, screen_hours FROM lifestyle_log
           WHERE user_id=? AND date>=? ORDER BY date DESC""",
        (user_id, start_date)).fetchall()
    conn.close()
    return [{"date": r[0], "sleep_hours": r[1], "stress_level": r[2],
             "exercise_min": r[3], "water_liters": r[4], "screen_hours": r[5]}
            for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# 7-DAY MEAL PLANS (Pre-bundled plans stored in DB)
# ─────────────────────────────────────────────────────────────────────────────
def create_meal_plan(plan_name, description):
    """Create a new meal plan. Returns plan_id."""
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO meal_plans(plan_name, description, created_at) VALUES(?, ?, ?)",
            (plan_name, description, str(date.today())))
        conn.commit()
        plan_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return plan_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def add_meal_plan_item(plan_id, day, meal_type, food_name, grams, calories, protein, carbs, fat, fiber):
    """Add a food item to a meal plan."""
    conn = get_conn()
    conn.execute(
        """INSERT INTO meal_plan_items
           (plan_id, day, meal_type, food_name, grams, calories, protein, carbs, fat, fiber)
           VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (plan_id, day, meal_type, food_name, grams, calories, protein, carbs, fat, fiber))
    conn.commit()
    conn.close()

def get_all_meal_plans():
    """Get all available meal plans (metadata)."""
    conn = get_conn()
    rows = conn.execute("SELECT id, plan_name, description FROM meal_plans ORDER BY plan_name").fetchall()
    conn.close()
    return [{"id": r[0], "plan_name": r[1], "description": r[2]} for r in rows]

def get_meal_plan_detail(plan_id):
    """Get full details of a meal plan (all days and items)."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT day, meal_type, food_name, grams, calories, protein, carbs, fat, fiber
           FROM meal_plan_items WHERE plan_id=? ORDER BY day, 
           CASE meal_type WHEN 'Breakfast' THEN 1 WHEN 'Lunch' THEN 2 WHEN 'Dinner' THEN 3 ELSE 4 END""",
        (plan_id,)).fetchall()
    conn.close()
    
    result = {}
    for row in rows:
        day = row[0]
        if day not in result:
            result[day] = {"Breakfast": [], "Lunch": [], "Dinner": [], "Snacks": []}
        meal_type = row[1]
        result[day][meal_type].append({
            "food_name": row[2],
            "grams": row[3],
            "calories": row[4],
            "protein": row[5],
            "carbs": row[6],
            "fat": row[7],
            "fiber": row[8]
        })
    return result

def get_plan_for_day(plan_id, day):
    """Get meals for a specific day (1-7) from a meal plan."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT meal_type, food_name, grams, calories, protein, carbs, fat, fiber
           FROM meal_plan_items WHERE plan_id=? AND day=? ORDER BY 
           CASE meal_type WHEN 'Breakfast' THEN 1 WHEN 'Lunch' THEN 2 WHEN 'Dinner' THEN 3 ELSE 4 END""",
        (plan_id, day)).fetchall()
    conn.close()
    
    result = {"Breakfast": [], "Lunch": [], "Dinner": [], "Snacks": []}
    for row in rows:
        meal_type = row[0]
        result[meal_type].append({
            "food_name": row[1],
            "grams": row[2],
            "calories": row[3],
            "protein": row[4],
            "carbs": row[5],
            "fat": row[6],
            "fiber": row[7]
        })
    return result

def save_user_selected_plan(user_id, plan_id):
    """Save the user's selected meal plan."""
    conn = get_conn()
    existing = conn.execute(
        "SELECT id FROM user_selected_plan WHERE user_id=?", (user_id,)).fetchone()
    if existing:
        conn.execute(
            "UPDATE user_selected_plan SET plan_id=?, selected_at=? WHERE user_id=?",
            (plan_id, str(date.today()), user_id))
    else:
        conn.execute(
            "INSERT INTO user_selected_plan(user_id, plan_id, selected_at) VALUES(?, ?, ?)",
            (user_id, plan_id, str(date.today())))
    conn.commit()
    conn.close()

def get_user_selected_plan(user_id):
    """Get the meal plan selected by the user."""
    conn = get_conn()
    row = conn.execute(
        "SELECT plan_id FROM user_selected_plan WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row[0] if row else None


# ─────────────────────────────────────────────────────────────────────────────
# USER TARGETS
# ─────────────────────────────────────────────────────────────────────────────
def get_user_targets(user_id):
    """Get user's custom targets or defaults if not set."""
    conn = get_conn()
    row = conn.execute(
        """SELECT calories, protein, carbs, fat, fiber, sugar,
           sleep_hours, exercise_min, water_liters, stress_level
           FROM user_targets WHERE user_id=?""", (user_id,)).fetchone()
    conn.close()
    if row:
        return {
            "calories": row[0],
            "protein": row[1],
            "carbs": row[2],
            "fat": row[3],
            "fiber": row[4],
            "sugar": row[5],
            "sleep_hours": row[6],
            "exercise_min": row[7],
            "water_liters": row[8],
            "stress_level": row[9],
        }
    # Return defaults
    return {
        "calories": 2000,
        "protein": 50,
        "carbs": 260,
        "fat": 70,
        "fiber": 25,
        "sugar": 50,
        "sleep_hours": 8,
        "exercise_min": 30,
        "water_liters": 2.5,
        "stress_level": 5,
    }

def save_user_targets(user_id, targets):
    """Save or update user's custom targets."""
    conn = get_conn()
    existing = conn.execute(
        "SELECT id FROM user_targets WHERE user_id=?", (user_id,)).fetchone()
    if existing:
        conn.execute(
            """UPDATE user_targets SET calories=?, protein=?, carbs=?, fat=?,
               fiber=?, sugar=?, sleep_hours=?, exercise_min=?, water_liters=?,
               stress_level=? WHERE user_id=?""",
            (targets.get("calories", 2000),
             targets.get("protein", 50),
             targets.get("carbs", 260),
             targets.get("fat", 70),
             targets.get("fiber", 25),
             targets.get("sugar", 50),
             targets.get("sleep_hours", 8),
             targets.get("exercise_min", 30),
             targets.get("water_liters", 2.5),
             targets.get("stress_level", 5),
             user_id))
    else:
        conn.execute(
            """INSERT INTO user_targets
               (user_id, calories, protein, carbs, fat, fiber, sugar,
                sleep_hours, exercise_min, water_liters, stress_level)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id,
             targets.get("calories", 2000),
             targets.get("protein", 50),
             targets.get("carbs", 260),
             targets.get("fat", 70),
             targets.get("fiber", 25),
             targets.get("sugar", 50),
             targets.get("sleep_hours", 8),
             targets.get("exercise_min", 30),
             targets.get("water_liters", 2.5),
             targets.get("stress_level", 5)))
    conn.commit()
    conn.close()
