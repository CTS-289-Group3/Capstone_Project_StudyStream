# Capstone_Project_StudyStream
StudyStream capstone project for group 3!

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

### 2) Install Django

```bash
pip install django
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
