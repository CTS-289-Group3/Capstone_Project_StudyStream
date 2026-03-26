# 🐛 Bug Report + ✨ Feature Request: Calendar & UI Improvements

## Summary
Several calendar bugs and UX issues identified during Sprint 2 review. This issue tracks all fixes and improvements to be delivered in a single feature branch.

---

## 🐛 Bugs

### Calendar
- [ ] **Calendar hours cut off at 8pm** — The week and day views only render 7am–8pm (14 slots). Assignments with due times of 9pm, 10pm, or 11pm snap incorrectly to the 8pm row.
- [ ] **Week view renders blank** — The `addCell()` helper is called inside `renderWeekCal()` but was never defined, causing the entire week grid to throw a JS error and appear empty.
- [ ] **Month cell `calOffset` uses wrong divisor** — Month-view day click calculates offset using `7*86400000` (week divisor) instead of `86400000` (day divisor), causing the wrong day to load in day view.

### Modals
- [ ] **Edit modal opens immediately on task click** — Clicking a task jumps straight into the edit form with no chance to preview. This is disorienting and causes accidental edits.
- [ ] **Edit modal overflows screen** — On laptop screens < 900px tall, the assignment modal is taller than the viewport with no scroll fallback. Bottom buttons are unreachable.

### Landing Page
- [ ] **Hero headline is plain text** — The landing page shows "Your semester, your shifts, your stream." as a typographic headline instead of the StudyStream logo image.

---

## ✨ Features / Improvements

- [ ] **Extend calendar to 11pm** — Show time slots 7am–11pm (17 slots) in both week and day views.
- [ ] **Clickable day headers in week view** — Clicking a day name or date number in the week grid should navigate to the day view for that date.
- [ ] **Clickable day cells in month view** — Already partially implemented; ensure correct day offset.
- [ ] **Task view modal (read-only first)** — Clicking a task name or a calendar event opens a clean read-only detail panel. Edit and Delete buttons inside the modal give access to those actions.
- [ ] **Month view event click** → opens task view modal (not edit).
- [ ] **Logo in navbar and footer** — Use the horizontal text logo (`logo_navbar.png`) in the top nav; use the stacked icon logo (`logo_icon.png`) in the footer.
- [ ] **Shorten landing page** — Reduce section padding so the page feels tighter and more focused.

---

## Affected Files
- `home/templates/home/home.html`
- `accounts/templates/accounts/home.html`
- `accounts/templates/accounts/base.html`
- `accounts/static/accounts/images/logo_navbar.png` *(new)*
- `accounts/static/accounts/images/logo_icon.png` *(new)*

---

## Acceptance Criteria
- [ ] Calendar week + day views show slots from 7am through 11pm
- [ ] Assignment at 9pm appears in the 9pm row, not at 8pm
- [ ] Week view renders correctly (no JS errors)
- [ ] Clicking a day header/date in week view opens that day in day view
- [ ] Clicking a calendar event or task title opens the task view modal
- [ ] Task view modal shows all details: course, status, due date, type, tags, progress, subtasks
- [ ] Edit and Delete buttons inside the view modal work correctly
- [ ] Assignment edit modal is scrollable on screens < 900px tall
- [ ] Landing page hero shows the logo image instead of text headline
- [ ] Navbar shows horizontal text logo; footer shows icon logo
