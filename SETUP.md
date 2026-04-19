# StudyStream – Setup & Migration Guide

## ⚡ Quick Start (Fresh Install)

```bash
# 1. Activate your virtual environment
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # Mac/Linux

# 2. Apply all migrations (REQUIRED before first use)
python manage.py migrate

# 3. Run the server
python manage.py runserver
```

## ❗ Fix: "no such table: auth_user" Error

If you see this error when registering or logging in, you just need to run migrations:

```bash
python manage.py migrate
```

This creates all the database tables (auth_user, accounts_profile, etc.).

## Dark / Light Mode

- The theme toggle (☀️/🌙) in the navbar persists your preference across all pages via localStorage.
- Default is dark mode.

## New Features in This Build

- **Merged Semester + Course section** on the Dashboard — expand a semester to see/add courses inline
- **Dark/Light mode** on every page, synced via localStorage
- **Shared design system** (`ss-shared.css` + `ss-shared.js`) applied to all 18 templates
- **Back button** (← Dashboard) in the navbar on every sub-page
- **Anamorphic lens flare** effect on all page banners
- **Glass pill navbar** and footer on all pages
