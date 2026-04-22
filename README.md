# StudyStream

StudyStream is a Django-based student planning app for tracking semesters, courses, assignments, work shifts, and personal events, with workload analysis and forecasting.

Useful docs:

- [Project Structure Guide](docs/project-structure.md)
- [Database ERD](docs/database-erd.md)

## Quick Start (Codespaces)

1. Open the repository in GitHub Codespaces.
2. In the terminal, run:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data --fresh
python manage.py runserver
```

3. Open port `8000` in the browser.

Default seeded user:

```text
Username: tessab
Password: StudyStream123!
```

## Local Setup

### 1. Create and activate a virtual environment

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Apply database migrations

```bash
python manage.py migrate
```

### 4. (Optional) Seed demo data

```bash
python manage.py seed_demo_data --fresh
```

### 5. Run the dev server

```bash
python manage.py runserver
```

Open: http://127.0.0.1:8000/

## Useful Commands

### Workload analysis

```bash
# Recompute workload forecast for all active users
python manage.py run_workload_analysis

# Recompute for one user
python manage.py run_workload_analysis --user-id 1

# Recompute a custom forecast horizon
python manage.py run_workload_analysis --weeks 6
```

### Demo data

```bash
# Seed a custom account and reset existing data for that user
python manage.py seed_demo_data --username qa_user --password TestPass123! --email qa@example.com --fresh

# Merge demo data into an existing user without clearing current records
python manage.py seed_demo_data --username qa_user --password TestPass123!
```

## Main Pages

| URL | Description |
|---|---|
| `http://127.0.0.1:8000/` | Public landing page |
| `http://127.0.0.1:8000/home/` | Main dashboard (planner, calendar, workload widgets) |
| `http://127.0.0.1:8000/accounts/login/` | Sign in |
| `http://127.0.0.1:8000/accounts/register/` | Create account |
| `http://127.0.0.1:8000/accounts/profile/` | Profile |
| `http://127.0.0.1:8000/accounts/settings/` | Settings and workload preferences |
| `http://127.0.0.1:8000/admin/` | Django admin |

## Core Features

1. Semester and course management
2. Assignment tracking with subtasks and tags
3. Work shift and personal event scheduling
4. Conflict detection with replace/suggest actions
5. Workload forecasting (GREEN/YELLOW/RED), deadline cluster detection, and recommendations

## API Endpoints (Assignments/Courses)

All endpoints require login and are user-scoped.

```text
/accounts/api/semesters/                         GET
/accounts/api/semesters/create/                  POST
/accounts/api/semesters/<id>/edit/               POST
/accounts/api/semesters/<id>/delete/             POST

/accounts/api/courses/                           GET
/accounts/api/courses/create/                    POST
/accounts/api/courses/<id>/edit/                 POST
/accounts/api/courses/<id>/delete/               POST

/accounts/api/tags/                              GET
/accounts/api/tags/create/                       POST
/accounts/api/tags/<id>/delete/                  POST

/accounts/api/assignments/                       GET
/accounts/api/assignments/create/                POST
/accounts/api/assignments/<id>/edit/             GET/POST
/accounts/api/assignments/<id>/delete/           POST
/accounts/api/assignments/<id>/status/           POST

/accounts/api/assignments/<id>/subtasks/         GET
/accounts/api/assignments/<id>/subtasks/create/  POST
/accounts/api/subtasks/<id>/toggle/              POST
/accounts/api/subtasks/<id>/delete/              POST
```