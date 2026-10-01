# NutriGuide — Setup & Run Guide

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10.x | Must be 3.10. Download from python.org |
| pip | Latest | Comes with Python |

> **Windows users:** During Python installation, check the box **"Add Python to PATH"**

---

## Project Files

Make sure you have all these files in the same folder:

```
DietApp/
  main.py           ← main application
  master_foods.csv  ← food database (per 100g values)
  user_foods.csv    ← user-created foods (auto-managed)
  requirements.txt  ← Python dependencies
```

Do NOT include `nutriguide.db` — each user gets their own fresh database on first run.

---

## Setup (One Time Only)

Open a terminal / command prompt in the project folder and run:

```
pip install -r requirements.txt
```

This installs Kivy and KivyMD. It will take a few minutes on first install.

### Windows-specific note
If you see an error about Visual C++ or missing DLLs, also run:
```
pip install kivy-deps.sdl2 kivy-deps.glew kivy-deps.angle
```

---

## Run the App

```
python main.py
```

The app window will open at phone size (390×844).

---

## First Time Use

1. Click **Register New Account**
2. Enter your name, email or mobile, and a password
3. Fill in your profile (age, weight, height, activity level, goal)
4. Start logging food from the **Diet Plan** screen

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: kivy` | Run `pip install -r requirements.txt` again |
| App opens then immediately closes | Check terminal for error — most likely a missing CSV file |
| `sqlite3.OperationalError: no such column` | Delete `nutriguide.db` and rerun — DB will be recreated fresh |
| Blank white screen | Make sure `master_foods.csv` is in the same folder as `main.py` |
| Slow first launch | Normal — Kivy compiles shaders on first run |

---

## Notes

- All data is stored locally in `nutriguide.db` (SQLite) — no internet required
- Custom foods added by the user are saved in `user_foods.csv`
- The app works on Windows, Mac, and Linux without any changes
