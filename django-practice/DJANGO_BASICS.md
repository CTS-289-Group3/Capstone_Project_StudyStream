# Django Basics: Commands and App Structure

This document explains common Django commands and the purpose of the files created when starting a new Django app. It is intended as a learning reference while building practice projects and larger applications like **StudyStream**.

---

# Django Command Reference

## Create Virtual Environment

```bash
python -m venv venv
```

**What it does**

Creates a Python virtual environment named `venv`.

**When to use it**

At the beginning of a new Python project.

**Why**

A virtual environment keeps project dependencies separate from your system Python installation.

---

## Activate Virtual Environment

### Windows

```bash
venv\Scripts\activate
```

### Linux / Codespaces / Mac

```bash
source venv/bin/activate
```

**What it does**

Activates the virtual environment so Python and pip use the project's packages.

**When to use it**

Before installing packages or running your Django project.

---

## Install Django

```bash
pip install django
```

**What it does**

Installs Django into the active virtual environment.

**When to use it**

After activating the virtual environment.

**Why**

Django must be installed before creating or running a Django project.

---

## Save Project Dependencies

```bash
pip freeze > requirements.txt
```

**What it does**

Records all installed packages into a `requirements.txt` file.

**When to use it**

After installing packages and whenever new dependencies are added.

**Why**

Allows others (or future-you) to recreate the exact environment.

---

## Create a Django Project

```bash
django-admin startproject config .
```

**What it does**

Creates the main Django project files.

**When to use it**

Once, after Django is installed.

**Why**

This generates the core Django configuration including settings and root URLs.

**Note**

The `.` prevents Django from creating nested folders and keeps the project structure cleaner.

---

## Create a Django App

```bash
python manage.py startapp tracker
```

**What it does**

Creates a new Django app named `tracker`.

**When to use it**

When adding a new feature module to your project.

**Why**

Django projects are composed of apps that each handle specific functionality.

Example apps for larger projects:

* `accounts`
* `tasks`
* `dashboard`
* `scheduling`

---

## Run the Development Server

```bash
python manage.py runserver
```

**What it does**

Starts the Django development server.

**When to use it**

Whenever you want to view the site in the browser.

**Default address**

```
http://127.0.0.1:8000
```

---

## Create Database Migration Files

```bash
python manage.py makemigrations
```

**What it does**

Creates migration files describing changes made to models.

**When to use it**

Whenever a model is created or modified in `models.py`.

**Why**

Django tracks database changes using migrations.

---

## Apply Database Migrations

```bash
python manage.py migrate
```

**What it does**

Applies migrations to the database.

**When to use it**

After running `makemigrations`.

**Why**

This creates or updates database tables.

---

## Create an Admin User

```bash
python manage.py createsuperuser
```

**What it does**

Creates an administrator account.

**When to use it**

After running migrations.

**Why**

Allows access to Django's built-in admin interface.

Admin panel URL:

```
/admin
```

Example:

```
http://127.0.0.1:8000/admin
```

---

## Change a User Password

```bash
python manage.py changepassword username
```

**What it does**

Resets the password for a specific user.

**When to use it**

When a password is forgotten or needs updating.

---

## Open the Django Shell

```bash
python manage.py shell
```

**What it does**

Opens an interactive Python shell with Django loaded.

**When to use it**

To inspect models or create data manually.

Example:

```python
from tracker.models import Assignment
Assignment.objects.all()
```

---

# Django App File Structure

Running the command:

```bash
python manage.py startapp tracker
```

Creates the following files.

---

## `__init__.py`

**Purpose**

Marks the folder as a Python package.

**Usage**

Usually not edited.

---

## `admin.py`

**Purpose**

Registers models so they appear in the Django admin panel.

**Example**

```python
from django.contrib import admin
from .models import Assignment

admin.site.register(Assignment)
```

**Why it matters**

Provides a quick interface for managing database records.

---

## `apps.py`

**Purpose**

Contains configuration for the Django app.

**Example**

```python
from django.apps import AppConfig

class TrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tracker'
```

**Usage**

Usually unchanged for simple projects.

---

## `models.py`

**Purpose**

Defines database tables using Python classes.

**Example**

```python
from django.db import models

class Assignment(models.Model):
    title = models.CharField(max_length=200)
    class_name = models.CharField(max_length=100)
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title
```

**Why it matters**

This file defines the structure of your application's data.

---

## `views.py`

**Purpose**

Handles the logic for responding to web requests.

**Example**

```python
from django.shortcuts import render

def home(request):
    return render(request, "tracker/home.html")
```

**Role**

Views connect:

```
URL → Logic → Response
```

---

## `tests.py`

**Purpose**

Contains automated tests for the application.

**Usage**

Optional for beginner projects but useful for larger applications.

---

## `migrations/`

**Purpose**

Stores migration files used to update the database schema.

**Important**

These files should not normally be edited manually.

---

# Additional Files You Will Often Create

Django generates basic files, but projects typically add more.

---

## `urls.py`

Defines URL routes for the app.

Example:

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
]
```

---

## `forms.py`

Defines Django forms used to collect user input.

Example:

```python
from django import forms
from .models import Assignment

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'class_name', 'due_date', 'completed']
```

---

## `templates/`

Contains HTML templates used to render pages.

Example structure:

```
tracker/templates/tracker/
```

Example file:

```
home.html
```

---

# How Django Components Work Together

A typical request flow:

```
User visits URL
      ↓
urls.py routes the request
      ↓
views.py handles logic
      ↓
models.py retrieves or stores data
      ↓
templates render HTML
      ↓
User sees the result
```

---

# Summary

Key Django components:

| Component | Responsibility      |
| --------- | ------------------- |
| models    | database structure  |
| views     | application logic   |
| urls      | routing             |
| templates | user interface      |
| forms     | data input          |
| admin     | database management |

Understanding these pieces is the foundation for building larger Django applications such as **StudyStream**.
