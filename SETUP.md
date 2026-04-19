document.getElementById('fc-week-banner')# StudyStream — Codespace Setup Guide

Follow these steps after opening the repo in a GitHub Codespace.

---

## 1. Open the Codespace

1. Go to the repo on GitHub: `CTS-289-Group3/Capstone_Project_StudyStream`
2. Click the green **Code** button → **Codespaces** tab → **Create codespace on `feature/calendar-experiments`**
3. Wait for the codespace to fully load (~1 min)

---

## 2. Open the Terminal

Press `` Ctrl + ` `` to open the integrated terminal.

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Reset the Database (important if `db.sqlite3` already exists)

If a `db.sqlite3` file is already present, delete it first to start clean:

```bash
rm -f db.sqlite3
python manage.py migrate
```

If there is no existing database file, just run:

```bash
python manage.py migrate
```

---

## 5. Load Demo Data

```bash
python manage.py seed_demo_data
```

This creates a demo account and populates the app with sample courses, assignments, and shifts.

**Demo credentials:**
| Field    | Value              |
|----------|--------------------|
| Username | `tessab`           |
| Password | `StudyStream123!`  |

---

## 6. Start the Dev Server

```bash
python manage.py runserver
```

---

## 7. Open the App

- Click **Open in Browser** when the popup appears in the bottom-right corner, **or**
- Go to the **Ports** tab (next to Terminal), find port `8000`, and click the globe icon 🌐

---

## 8. Sign In

Use the demo credentials from Step 5, or create your own account via the **Create one free** link on the sign-in page.
