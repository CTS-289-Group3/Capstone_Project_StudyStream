# Capstone_Project_StudyStream
StudyStream capstone project for group 3!

> **Important:** After cloning and creating your `.venv`, you **must** run migrations before starting the server or you will get database errors.
> ```bash
> python manage.py migrate
> ```
> See [Step 3](#3-run-django-setup-commands) below for the full setup order.

## Local setup

### 1) Create and activate a virtual environment

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2) Install Dependencies

```bash
pip install django python-dotenv
```

### 3) Run Django setup commands

Use these in order when setting up the project for the first time:

```bash
# Run after creating or changing models
python manage.py makemigrations

# Run after makemigrations to apply changes to the database
python manage.py migrate

# Run once to create an admin login account
python manage.py createsuperuser

# Run any time you want to start the development server
python manage.py runserver
```

Then open: http://127.0.0.1:8000/

## Pages

| URL | Description |
|---|---|
| `http://127.0.0.1:8000/` | Public landing page |
| `http://127.0.0.1:8000/home/` | Assignment dashboard — Semesters, Courses, and Assignments |
| `http://127.0.0.1:8000/dashboard/` | Work shifts and personal events calendar |
| `http://127.0.0.1:8000/accounts/login/` | Sign in |
| `http://127.0.0.1:8000/accounts/register/` | Create account |
| `http://127.0.0.1:8000/accounts/profile/` | Edit profile |
| `http://127.0.0.1:8000/admin/` | Django admin |

## Academic tracking (new)

The assignment dashboard at `/home/` lets you:

1. Create a **Semester** (e.g. Fall 2026) from the sidebar
2. Add **Courses** under that semester — each gets a color used throughout the UI
3. Add **Assignments** with a due date/time, type, priority, subtasks, and tags
4. Track progress — stat cards for Due This Week, Completed, Overdue, and Active Courses update live after every change

## Database models

### `accounts` app
- **Profile** — bio, major, year *(existing)*
- **Semester** — academic term with start/end dates and active flag
- **Course** — linked to a Semester; stores code, name, professor, Canvas URL, color
- **Tag** — custom color labels for assignments
- **Assignment** — due date/time, type, status, priority, subtasks, tags, completion %
- **AssignmentSubtask** — ordered steps; auto-updates parent completion on save

### `core` app *(existing)*
- **WorkShift**, **PersonalEvent**, **RecurringWorkShift**, **RecurringWorkLocation**, **RecurringJobTitle**, **RecurringPersonalEvent**

## Assignment API endpoints

All require login and are scoped to the current user.

```
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