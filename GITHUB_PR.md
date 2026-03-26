# Pull Request: Calendar Fixes + UI Improvements

**Branch:** `feature/calendar-ui-improvements`
**Base branch:** `main`
**Closes:** #[INSERT_ISSUE_NUMBER]

---

## 📋 What This PR Does

This PR resolves all bugs and implements the UI improvements listed in the linked issue. Changes span the calendar, task interaction, landing page, and logo system.

---

## 🔧 Changes by File

### `home/templates/home/home.html` (Main dashboard)

| Change | Detail |
|---|---|
| Extended calendar hours | 14 slots (7am–8pm) → 17 slots (7am–11pm) in both week and day views |
| Fixed `addCell` missing | Added `addCell()` helper so week view renders correctly |
| Fixed month-click offset | Changed divisor from `7*86400000` to `86400000` |
| Clickable week day headers | Day name + date number now navigate to day view on click |
| Clickable month events | Month event chips open task view modal |
| Task view modal (new) | Read-only detail panel with Edit/Delete buttons — opened on task name click |
| Calendar events open view | Week + day view events open task view modal instead of edit form |
| Adaptive edit modal | `max-height: min(90vh, 700px)` prevents overflow on small screens |
| Added `openTaskView()` | New JS function — fetches subtask progress live and displays full task detail |

### `accounts/templates/accounts/home.html` (Landing page)

| Change | Detail |
|---|---|
| Logo hero | Replaced text headline with `<img>` of `logo_navbar.png` (dark/light aware) |
| Shorter sections | Reduced `padding` on features, who, how, and CTA sections |
| Mockup card logo | Uses `logo_icon.png` (stacked icon) in the hero app mockup |

### `accounts/templates/accounts/base.html` (Global nav + footer)

| Change | Detail |
|---|---|
| Navbar logo | Now uses `logo_navbar.png` (horizontal text logo) |
| Footer logo | Now uses `logo_icon.png` (stacked icon logo), height 36px |

### `accounts/static/accounts/images/` (Static assets)

| File | Description |
|---|---|
| `logo_navbar.png` | Horizontal text logo — used in top nav bar |
| `logo_icon.png` | Stacked icon logo — used in footer and app mockup |

---

## 🧪 Testing Checklist

**Calendar**
- [ ] Add an assignment with due time 9:30 PM — appears in 9pm slot
- [ ] Add an assignment with due time 11:00 PM — appears in 11pm slot
- [ ] Week view loads without JS errors (open browser console to verify)
- [ ] Click "Mon" header in week view → navigates to that Monday in day view
- [ ] Click "15" date number in week view → navigates to day view for the 15th
- [ ] Click a day in month view → correct day opens in day view

**Task Interaction**
- [ ] Click any task title → task view modal opens (not edit form)
- [ ] Task view modal shows: course badge, status, due date, type, tags, description, progress bar, subtasks
- [ ] Click "Edit" inside task view modal → closes view modal, opens edit form pre-filled
- [ ] Click "Delete" inside task view modal → deletes and closes
- [ ] Click a calendar event (week/day/month view) → task view modal opens
- [ ] Edit modal on a 768px-height screen — bottom buttons visible via scroll

**Landing Page**
- [ ] Hero shows StudyStream logo image, not text
- [ ] Logo switches between dark/light mode correctly

**Nav + Footer**
- [ ] Navbar shows horizontal text logo
- [ ] Footer shows stacked icon logo
- [ ] Both look correct in dark mode AND light mode

---

## 📸 Screenshots

> Attach before/after screenshots of:
> 1. Calendar week view (showing 11pm slots)
> 2. Task view modal
> 3. Landing page hero with logo
> 4. Navbar / footer logos

---

## 💬 Notes for Reviewers

- The `addCell` fix is critical — without it, week view is completely broken. It was referenced in `renderWeekCal()` but never defined.
- `openTaskView()` makes a live `fetch` call to `/accounts/api/assignments/{id}/subtasks/` to show up-to-date subtask progress — this requires the user to be logged in (already enforced by Django's `@login_required`).
- Logo image paths use Django's `{% static %}` tag — make sure `collectstatic` is run if deploying.

---

## How to Review Locally

```bash
git checkout feature/calendar-ui-improvements
pip install -r requirements.txt  # or pipenv install
python manage.py migrate
python manage.py runserver
```

Then visit `http://127.0.0.1:8000/` to test the landing page and `http://127.0.0.1:8000/home/` (after login) for the dashboard.
