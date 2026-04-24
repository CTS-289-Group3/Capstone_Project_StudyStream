# StudyStream Project Structure Guide

This guide explains the main Django folders and files in this repository so new contributors can navigate quickly.

## High-level folder diagram

```text
Capstone_Project_StudyStream/
|-- manage.py
|-- requirements.txt
|-- db.sqlite3
|-- README.md
|-- UPDATE.md
|-- docs/
|   |-- database-erd.md
|   |-- program-flowchart.md
|   `-- project-structure.md
|-- studystream/
|   |-- __init__.py
|   |-- settings.py
|   |-- urls.py
|   |-- asgi.py
|   `-- wsgi.py
|-- accounts/
|   |-- admin.py
|   |-- apps.py
|   |-- context_processors.py
|   |-- forms.py
|   |-- models.py
|   |-- tests.py
|   |-- urls.py
|   |-- views.py
|   |-- migrations/
|   |-- management/commands/seed_demo_data.py
|   |-- static/accounts/
|   `-- templates/accounts/
|-- core/
|   |-- admin.py
|   |-- apps.py
|   |-- models.py
|   |-- scheduling.py
|   |-- tests.py
|   |-- views.py
|   `-- migrations/
`-- home/
    |-- admin.py
    |-- apps.py
    |-- forms.py
    |-- models.py
    |-- tests.py
    |-- urls.py
    |-- views.py
    |-- workload_config.py
    |-- workload_engine.py
    |-- migrations/
    |-- management/commands/run_workload_analysis.py
    `-- templates/home/
```

## Django basics in this project

- `models.py`: database table definitions (Django ORM models)
- `views.py`: request handlers (business logic for each URL)
- `urls.py`: route mapping from URL path to a view
- `forms.py`: form definitions + validation logic
- `admin.py`: Django admin registration
- `tests.py`: unit/integration tests
- `migrations/`: schema history for database changes
- `templates/`: HTML templates
- `static/`: CSS, JS, images

## Top-level files

| Path | Purpose |
|---|---|
| `manage.py` | Django command entry point (`runserver`, `migrate`, `test`, etc.). |
| `requirements.txt` | Python dependencies for the app. |
| `db.sqlite3` | Local SQLite database file for development. |
| `README.md` | Main project documentation and setup instructions. |
| `UPDATE.md` | Additional project update notes/changelog content. |

## Project package: `studystream/`

| Path | Purpose |
|---|---|
| `studystream/settings.py` | Global Django configuration: apps, middleware, DB, templates, static config. |
| `studystream/urls.py` | Root URL router that includes app-level URL files. |
| `studystream/asgi.py` | ASGI application entry point (async server deployments). |
| `studystream/wsgi.py` | WSGI application entry point (traditional server deployments). |
| `studystream/__init__.py` | Marks the folder as a Python package. |

## App: `accounts/` (academic data + auth-connected features)

| Path | Purpose |
|---|---|
| `accounts/models.py` | Core academic models: Profile, Semester, Course, Assignment, Subtask, Tag, TimeBlock. |
| `accounts/views.py` | Account pages + APIs for semester/course/assignment/tag/subtask operations. |
| `accounts/urls.py` | URL patterns for auth pages and `/accounts/api/...` endpoints. |
| `accounts/forms.py` | Profile and workload preference forms + validation. |
| `accounts/context_processors.py` | Injects shared context values into templates. |
| `accounts/admin.py` | Admin panel registrations for `accounts` models. |
| `accounts/tests.py` | Tests for schedule conflict APIs and preference/workload behavior. |
| `accounts/apps.py` | Django app config metadata. |
| `accounts/migrations/` | Database migration history for `accounts` tables. |
| `accounts/management/commands/seed_demo_data.py` | CLI command to seed demo user/data quickly. |
| `accounts/templates/accounts/base.html` | Shared base template/layout for account-facing pages. |
| `accounts/templates/accounts/login.html` | Login page template. |
| `accounts/templates/accounts/register.html` | Registration page template. |
| `accounts/templates/accounts/profile.html` | Profile editing page template. |
| `accounts/templates/accounts/settings.html` | Settings page template (including workload preferences). |
| `accounts/static/accounts/css/ss-shared.css` | Shared design system CSS used across pages. |
| `accounts/static/accounts/js/ss-shared.js` | Shared frontend interactions/menu/theme scripts. |
| `accounts/static/accounts/images/` | Images/icons used by templates. |

## App: `core/` (scheduling and shared domain models)

| Path | Purpose |
|---|---|
| `core/models.py` | Work/personal event models, recurring templates, and workload analysis model. |
| `core/scheduling.py` | Conflict detection, replacement logic, and suggestion generation helpers. |
| `core/admin.py` | Admin registrations for core models. |
| `core/tests.py` | Tests for core-level behavior (if/when added). |
| `core/views.py` | Reserved for core-specific views (minimal currently). |
| `core/apps.py` | Django app config metadata. |
| `core/migrations/` | Database migration history for `core` tables. |

## App: `home/` (dashboard + calendar + workload UI)

| Path | Purpose |
|---|---|
| `home/views.py` | Dashboard rendering, calendar APIs, and event/work shift edit APIs. |
| `home/urls.py` | URL routing for `/home/...` pages and API endpoints. |
| `home/workload_engine.py` | Weekly workload computation, utilization status, recommendations, and alerts. |
| `home/workload_config.py` | Workload thresholds/colors/notification template settings. |
| `home/forms.py` | Forms for personal events, work shifts, and recurring templates. |
| `home/models.py` | Currently minimal (domain models are mostly in `accounts` and `core`). |
| `home/admin.py` | Home app admin setup. |
| `home/tests.py` | Dashboard/calendar/work shift behavior tests. |
| `home/apps.py` | Django app config metadata. |
| `home/migrations/` | Migration history for `home` app tables. |
| `home/management/commands/run_workload_analysis.py` | CLI command to recompute workload forecasts. |
| `home/templates/home/home.html` | Main dashboard SPA-like page (planner/calendar/workload widgets). |
| `home/templates/home/work_shift_form.html` | Work shift create page. |
| `home/templates/home/personal_event_form.html` | Personal event create page. |
| `home/templates/home/partials/navbar.html` | Shared navbar partial used by home templates. |

## How requests flow (quick mental model)

1. Browser hits URL in `studystream/urls.py` or app `urls.py`.
2. Django calls the matched function in `views.py`.
3. View reads/writes models in `models.py`.
4. View returns HTML template (`templates/...`) or JSON for frontend JS.
5. Frontend JS in templates/static can call API routes for updates.

## Useful commands for exploring structure

```bash
# Show top-level folders and files
find . -maxdepth 2 -type f | sort

# Run migrations and server
python manage.py migrate
python manage.py runserver

# Run test suites
python manage.py test accounts.tests
python manage.py test home.tests
```
