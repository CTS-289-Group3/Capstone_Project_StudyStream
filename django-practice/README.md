# Django Practice Project -- Assignment Tracker

This repository contains a small **practice Django project** used to
explore the basics of Django development. It demonstrates simple
features such as:

-   Setting up a Django project
-   Creating an app
-   Defining models
-   Using migrations
-   Running the development server
-   Using the Django admin panel

This project is meant for experimentation and learning before building
larger applications like **StudyStream**.

------------------------------------------------------------------------

# Project Overview

The project includes a simple app called **tracker** that demonstrates:

-   Basic Django app structure
-   A model for tracking assignments
-   Admin panel management
-   Simple views and templates

Example model fields:

-   Assignment title
-   Class name
-   Due date
-   Completion status

------------------------------------------------------------------------

# Prerequisites

Before running the project, make sure you have:

-   Python **3.10+**
-   Git installed
-   Either:
    -   **Visual Studio Code**
    -   **GitHub Codespaces**

------------------------------------------------------------------------

# Getting Started

## 1. Clone the Repository

``` bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

------------------------------------------------------------------------

# Option 1: Run Locally with VS Code

## Step 1: Create a Virtual Environment

``` bash
python -m venv venv
```

## Step 2: Activate the Virtual Environment

### Windows

``` bash
venv\Scripts\activate
```

### Mac / Linux

``` bash
source venv/bin/activate
```

You should now see `(venv)` at the start of your terminal prompt.

------------------------------------------------------------------------

## Step 3: Install Dependencies

``` bash
pip install -r requirements.txt
```

If the requirements file is missing:

``` bash
pip install django
```

------------------------------------------------------------------------

## Step 4: Run Database Migrations

``` bash
python manage.py migrate
```

This creates the SQLite database and required tables.

------------------------------------------------------------------------

## Step 5: Create an Admin User

``` bash
python manage.py createsuperuser
```

Follow the prompts to create a username and password.

------------------------------------------------------------------------

## Step 6: Start the Development Server

``` bash
python manage.py runserver
```

Open:

http://127.0.0.1:8000

Admin panel:

http://127.0.0.1:8000/admin

------------------------------------------------------------------------

# Option 2: Run with GitHub Codespaces

## Step 1

Open the repository on GitHub.

Click:

Code → Codespaces → Create codespace on main

------------------------------------------------------------------------

## Step 2: Create Virtual Environment

``` bash
python3 -m venv venv
```

## Step 3: Activate the Environment

``` bash
source venv/bin/activate
```

## Step 4: Install Dependencies

``` bash
pip install -r requirements.txt
```

If needed:

``` bash
pip install django
```

## Step 5: Run Migrations

``` bash
python manage.py migrate
```

## Step 6: Create Admin User

``` bash
python manage.py createsuperuser
```

## Step 7: Run the Server

``` bash
python manage.py runserver
```

Codespaces will forward **port 8000** automatically.

------------------------------------------------------------------------

# Project Structure

    django-practice/
    │
    ├── manage.py
    ├── requirements.txt
    ├── db.sqlite3
    │
    ├── config/
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    │
    └── tracker/
        ├── admin.py
        ├── models.py
        ├── views.py
        ├── urls.py
        └── migrations/

------------------------------------------------------------------------

# Common Commands

Start server

``` bash
python manage.py runserver
```

Create migrations after editing models

``` bash
python manage.py makemigrations
```

Apply migrations

``` bash
python manage.py migrate
```

Create admin user

``` bash
python manage.py createsuperuser
```

Open Django shell

``` bash
python manage.py shell
```

------------------------------------------------------------------------

# Learning Goals

This project helps demonstrate:

-   Django project structure
-   Models and migrations
-   URL routing
-   Views and templates
-   Django admin interface
-   Basic web application workflow

------------------------------------------------------------------------

# Contributing / Experimenting

Feel free to:

-   add new fields to the Assignment model
-   build additional pages
-   experiment with templates
-   add forms for creating assignments
-   improve styling with CSS

This repository is meant to be a **sandbox for learning Django basics**.

------------------------------------------------------------------------

# Future Ideas

Possible improvements:

-   Assignment creation form
-   Edit / delete assignments
-   Assignment filtering by class
-   Dashboard summary
-   User authentication
-   Improved UI styling

------------------------------------------------------------------------

# Author

Created as a Django learning project for **CSC‑289 Capstone
preparation**.
