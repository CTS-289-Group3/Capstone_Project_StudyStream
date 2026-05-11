# StudyStream

**Course:** CSC 289 -- Programming Capstone, Spring 2026
**Team:** CTS-289 Group 3
**Repository:** https://github.com/CTS-289-Group3/Capstone_Project_StudyStream
**Final Submission:** May 2026

---

## Project Overview

StudyStream is a web-based academic planning application that helps college students stop wondering what they are forgetting. It brings together coursework, work schedules, and personal commitments into one unified system.

It is designed for college students who juggle 4 to 6 classes, work schedules, group projects with unclear roles, and personal commitments. StudyStream goes beyond task lists by breaking big assignments into steps, scheduling work time rather than just due dates, predicting overload before it happens, and integrating school, work, and life into one system.

StudyStream is more than a task manager. It reduces academic overwhelm, supports executive function, prevents last-minute crisis cycles, and turns chaos into clarity.

As of the final submission, the application includes working user authentication with email-based password reset, full CRUD for semesters, courses, assignments with subtasks, work shifts, and personal events, a scheduling conflict engine that prevents time-block overlaps, and a workload analysis engine that computes weekly utilization and generates proactive recommendations.

---

## Team Roster & Roles

| Name | GitHub | Primary Role | Main Contribution |
|---|---|---|---|
| Haylee Paredes (Lee) | HayleeSophia77 | Auth Lead / Backend | Built the complete authentication system including login, register, logout, and email-based password reset. Authored the accounts data models and contributed to Git workflow coordination across the team. |
| Teresa (Tessa) | thearn1981 | Frontend Lead / Scrum Master | Primary driver of the dashboard UI, calendar features, recurring events, and workload display. Managed the majority of merges and branch coordination throughout the project. |
| Kaheel | KaheelR | Backend / Profiles | Built the user profile page and added the profile navigation button to the dashboard. |
| Aryan | aryan-kandula | Backend / UI | Contributed semester, course, and assignment models and CRUD dashboard with a glassmorphic UI redesign. |

---

## Product Vision

### Target Users / Personas

#### Persona 1: Emma, the Pre-Med Student

Emma is a pre-med student dealing with multiple exams, labs, and a heavy overall workload. Her schedule is demanding and leaves little room for error. She needs a system that helps her see everything at once and warns her when an upcoming week is going to be unmanageable before it arrives, not after she is already overwhelmed.

#### Persona 2: Marcus, the Working Student

Marcus is a working student with irregular shifts and a constantly changing schedule. His biggest challenge is that work hours eat into study time in unpredictable ways week to week. He needs a tool that accounts for his work schedule when calculating how much study time he actually has, not just what is theoretically left after class.

### Core Value Proposition

StudyStream goes beyond task lists. Most apps only track due dates. StudyStream schedules actual work time, breaks big assignments into manageable steps, and predicts overload before it happens. It integrates school, work, and life into one system so students always know what is coming and have a plan to handle it. Structure first. Clarity always.

### Feature Scope

| Feature | Status |
|---|---|
| User registration and login | Implemented |
| Email-based password reset (Gmail SMTP) | Implemented |
| User profile with avatar and bio | Implemented |
| Workload preferences (sleep, personal time, commute) | Implemented |
| Semester CRUD | Implemented |
| Course CRUD with color coding and professor info | Implemented |
| Assignment CRUD with priority, type, and links | Implemented |
| Assignment subtask tracking with completion percentage | Implemented |
| Tag system (color-coded, per-user) | Implemented |
| Work shift logging (manual entry) | Implemented |
| Recurring work shift templates | Implemented |
| Personal event logging | Implemented |
| Recurring personal event templates | Implemented |
| Schedule conflict detection and suggestion | Implemented |
| Weekly workload analysis (utilization ratio, green/yellow/red) | Implemented |
| Deadline cluster detection | Implemented |
| Workload-based recommendations | Implemented |
| Time block scheduling | Partial (model complete, full UI not finalized) |
| Public deployment | In Progress |
| Email notifications for red/yellow weeks | Partial (alert logic built, delivery not wired) |
| Mobile-responsive UI | Partial |

---

## User Stories

Stories are grouped by feature area. Statuses: Done / In Progress / Not Started.

### Authentication & User Setup

| User Story | Board Item | Status |
|---|---|---|
| As a student, I want to register and log in to the app so that my schedule and assignments are private to me. | User Registration, Login, and Basic Dashboard (#3) | Done |
| As a student, I want a basic dashboard after logging in so that I have a central place to view my academic information. | User Registration, Login, and Basic Dashboard (#3) | Done |
| As a student, I want to reset my password by email so that I am not locked out of my account if I forget it. | Fix up registration page and add forgot password stuff (#9) | In Progress |
| As a student, I want a user profile page so that I can personalize my account information. | Make user profiles (#10) | Done |
| As a student, I want to configure my workload preferences so that the app accounts for my sleep, commute, and personal time. | Feature: YAML Configuration Settings (#17) | Backlog |

### Academic Tracking

| User Story | Board Item | Status |
|---|---|---|
| As a student, I want to create and manage semesters so that my courses are organized by term. | Feature: Semester Management (#13) | Done |
| As a student, I want to add and manage my courses so that I can track all my class information in one place. | Feature: Course Management (#14) | Done |
| As a student, I want to create and manage assignments for each course so that I know what is due and when. | Feature: Assignment Management (#15) | Done |
| As a student, I want semester, course, and assignment data stored together so that the app can calculate my full academic workload. | Academic Tracking Layer -- Semester, Course and Assignment Databases + Dashboard UI Overhaul (#22) | Done |

### Calendar & Schedule

| User Story | Board Item | Status |
|---|---|---|
| As a student, I want a calendar view of my schedule so that I can see my assignments, shifts, and events at a glance. | Feature: Calendar and Schedule Management (#11) | Done |
| As a student, I want a workspace dashboard so that I can view and manage all parts of my schedule in one place. | Feature: Workspace Dashboard (#12) | Done |
| As a student, I want my personal events and work shifts to display on the calendar so that my full week is visible. | fixes/personal and work shift forms (#27) | In Progress |

---

## System Architecture

### Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.x | Primary programming language |
| Django 6.0.4 | Web framework -- routing, ORM, templating, auth |
| SQLite | Development database (file-based, no setup required) |
| python-dotenv 1.2.2 | Environment variable management for credentials |
| Gmail SMTP | Email backend for password reset delivery |
| HTML / CSS / JavaScript | Frontend templates (server-rendered via Django template engine) |
| GitHub Codespaces | Development and testing environment |

Django was chosen because it provides a batteries-included ORM, built-in authentication system, and a PasswordResetView that could be wired directly to Gmail SMTP, saving significant development time on the auth subsystem.

### Application Structure

| App / Package | Contents |
|---|---|
| studystream/ | Project configuration: settings, root URL routing |
| accounts/ | Auth, user profile, and all academic data (Semester, Course, Assignment, Subtask, Tag, Profile) |
| core/ | Calendar and scheduling domain (WorkShift, PersonalEvent, WorkloadAnalysis, recurring templates) |
| home/ | Dashboard and workload (workload engine, dashboard views, shift and event CRUD) |

Request flow: A user request hits `studystream/urls.py`, which routes to either `accounts.urls` or `home.urls`. Views in `accounts/views.py` handle auth and all academic data via AJAX JSON endpoints. The workload engine (`home/workload_engine.py`) is called as a side effect any time assignments or shifts change, persisting a WorkloadAnalysis snapshot to the database.

### Route Map

#### accounts/ routes

| Route | Method | Description | Auth Required |
|---|---|---|---|
| /accounts/login/ | GET, POST | User login | No |
| /accounts/register/ | GET, POST | New user registration | No |
| /accounts/logout/ | GET | Log out and redirect | Yes |
| /accounts/profile/ | GET, POST | View and edit user profile | Yes |
| /accounts/settings/ | GET, POST | Workload preferences | Yes |
| /accounts/password-reset/ | GET, POST | Request password reset email | No |
| /accounts/password-reset/\<uidb64\>/\<token\>/ | GET, POST | Set new password via token link | No |
| /accounts/api/semesters/ | GET | List all semesters (JSON) | Yes |
| /accounts/api/semesters/create/ | POST | Create semester | Yes |
| /accounts/api/courses/ | GET | List all courses (JSON) | Yes |
| /accounts/api/courses/create/ | POST | Create course | Yes |
| /accounts/api/assignments/ | GET | List all assignments (JSON) | Yes |
| /accounts/api/assignments/create/ | POST | Create assignment | Yes |
| /accounts/api/assignments/\<pk\>/status/ | POST | Quick status toggle | Yes |
| /accounts/api/subtasks/\<pk\>/toggle/ | POST | Toggle subtask complete or incomplete | Yes |

#### home/ routes

| Route | Method | Description | Auth Required |
|---|---|---|---|
| /home/ | GET | Main dashboard | Yes |
| /home/dashboard/add/work-shift/ | GET, POST | Add work shift | Yes |
| /home/dashboard/add/personal-event/ | GET, POST | Add personal event | Yes |
| /home/dashboard/recurring-shifts/ | GET | List recurring shift templates | Yes |
| /home/dashboard/recurring-shifts/add/ | GET, POST | Create recurring shift template | Yes |
| /home/api/workload/summary/ | GET | Workload forecast (JSON) | Yes |
| /home/api/work-shifts/ | GET | List work shifts (JSON) | Yes |
| /home/api/personal-events/ | GET | List personal events (JSON) | Yes |

---

## Data Model

### Entity Relationship Diagram

The full ERD is available in `docs/database-erd.md` in the project repository and renders on GitHub.

### Data Dictionary

#### accounts_assignment (key columns)

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK, auto | Row identifier |
| assignment_id | UUID | Unique | Stable public identifier used in API responses |
| course_id | Integer | FK to course | Parent course |
| user_id | Integer | FK to auth_user | Owner |
| title | String(255) | Not null | Assignment title |
| due_date | DateTime | Not null, TZ-aware | Deadline; used by conflict and workload engines |
| estimated_hours | Decimal(4,1) | Nullable | Time estimate; drives workload utilization calculation |
| status | String(20) | Choices | not_started / in_progress / complete |
| priority_level | String(10) | Choices | low / medium / high / critical |
| is_major_project | Boolean | Default False | Flags high-weight assignments for deadline cluster detection |
| completion_percentage | Integer | 0-100 | Auto-computed from subtask completions via save() override |
| contributes_to_workload | Boolean | Default True | Allows excluding low-stakes items from the calculation |

#### core_workloadanalysis (key columns)

| Column | Type | Constraints | Description |
|---|---|---|---|
| analysis_id | UUID | PK | Stable identifier for this snapshot |
| user_id | Integer | FK to auth_user | Owner |
| week_start_date | Date | Unique per user | Monday that begins the analyzed week |
| utilization_ratio | Decimal(4,3) | Nullable | assignment_hours divided by available_study_hours |
| week_status | String(10) | GREEN/YELLOW/RED | Derived from utilization ratio thresholds |
| deadline_cluster_detected | Boolean | Default False | True if 3 or more major assignments fall within 48 hours |
| recommended_actions | JSON | Default list | Structured recommendations from the workload engine |
| alert_sent | Boolean | Default False | Tracks whether the user was notified about this week |

### Key Relationships

User to Semester to Course to Assignment to Subtask is the primary academic hierarchy. Each level cascades on delete. Every record also carries a direct user_id foreign key so ownership can be checked without traversing the full chain, a deliberate decision to simplify authorization in view code.

Assignment and Tag is a many-to-many relationship managed through `accounts_assignment_tags`. Tags are per-user and reusable across assignments within the same account.

WorkloadAnalysis stores one computed snapshot per user per week. The unique constraint on (user, week_start_date) is enforced at the database level using Django's UniqueConstraint.

---

## Key Features & Implementation Notes

### Email-Based Password Reset

#### What it does

A user who has forgotten their password can request a reset link from the login page. StudyStream sends an email containing a single-use token link. Clicking the link takes the user to a form where they set a new password. The link expires after use or after a configurable time window.

#### How it works

Django's built-in PasswordResetView and PasswordResetConfirmView were wired into `accounts/urls.py` with custom templates. The email backend was configured in `settings.py` to use Gmail SMTP with credentials loaded from a `.env` file via python-dotenv. Credentials are never hardcoded in the source code.

#### Challenges

Django's default password reset email generates a link using `request.get_host()`, which in a Codespaces environment returns the internal container hostname rather than the public URL. This was fixed by passing `extra_email_context` with the correct domain to the view. The Gmail App Password setup also required enabling two-factor authentication on the Google account before an app-specific password could be generated.

---

### Schedule Conflict Detection Engine

#### What it does

When a user creates or edits an assignment, work shift, or personal event, the application checks whether the proposed time block overlaps with anything already on their schedule. If a conflict is found, the API returns a detailed response with information about what conflicts and a suggested alternative time slot.

#### How it works

All schedulable items are represented as ScheduledItem dataclasses with a start and end datetime. The engine checks for overlap using a standard interval condition. When a conflict is detected, it searches forward in 30-minute increments to find the next available slot that fits the requested duration. The engine also incorporates user preference blocks such as sleep, commute, and personal time.

#### Challenges

The initial version only checked new items against existing database records. This caused a bug where multiple subtasks submitted in one request could not conflict with each other because none were in the database yet. The fix was to validate all items in the current request against each other as well as against existing records before any are written.

---

### Workload Analysis Engine

#### What it does

StudyStream computes a weekly workload snapshot showing total class hours, total work hours, total assignment hours due that week, available study hours, and a utilization ratio. Weeks are color-coded green under 60 percent, yellow from 60 to 85 percent, and red above 85 percent. The engine also detects deadline clusters and generates plain-language recommendations.

#### How it works

The engine is triggered as a side effect of any change to assignments or work shifts. Available study hours are calculated as 168 minus class hours, work hours, sleep hours, personal hours, family hours, and commute hours. Class hours are parsed from a free-text meeting times field on each course using a regex-based parser.

#### Challenges

The meeting times parsing was harder than expected. Students enter class schedules in inconsistent formats. The initial implementation failed on inputs like T/TH or time ranges that omit AM/PM from the start time. The final parser handles these with regex matching and fallback logic.

---

### Cascading Completion Percentage

#### What it does

When a student checks off a subtask, the parent assignment completion percentage updates automatically. If an assignment has four subtasks and two are marked complete, the assignment shows 50 percent. No manual input required.

#### How it works

The AssignmentSubtask save method is overridden to call `assignment.update_completion()` after every save. `update_completion()` queries the subtask count and completion count, then writes the result back to the assignment using `update_fields` to avoid unnecessary database writes.

#### Challenges

The first version computed completion inside the view, meaning the percentage was only accurate after a full page reload. Moving the calculation into the model save hook meant it was always current, including when subtasks were toggled via the AJAX endpoint.

---

### User-Scoped Authorization

#### What it does

Every piece of user data in StudyStream is strictly scoped to the authenticated user. A logged-in user cannot access, modify, or delete another user's data even by guessing a valid primary key in the URL.

#### How it works

All views that operate on user-owned records use `get_object_or_404` with the `user=request.user` condition. This returns a 404 instead of a 403, which is the standard convention for not revealing whether the record exists at all. All views that modify data are also decorated with the `login_required` decorator.

---

## Deployment

StudyStream was developed and tested in GitHub Codespaces using Django's built-in development server.

### Required Environment Variables

| Key | Description |
|---|---|
| SECRET_KEY | Django secret key for cryptographic signing |
| EMAIL_HOST_USER | Gmail address used as the SMTP sender |
| EMAIL_HOST_PASSWORD | Gmail App Password (not the account password) |
| DEBUG | Set to False in production |
| ALLOWED_HOSTS | Comma-separated list of allowed hostnames |
| CODESPACE_DOMAIN | The public-facing domain used in password reset emails |

### Deployment Steps

1. Clone the repository from https://github.com/CTS-289-Group3/Capstone_Project_StudyStream
2. Create a virtual environment and install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and populate the required variables listed above
4. Run migrations: `python manage.py migrate`
5. (Optional) Seed demo data: `python manage.py seed_demo_data`
6. Start the server: `python manage.py runserver`

### Known Gotchas

- The Codespaces domain used in password reset emails should be stored in the `.env` file as `CODESPACE_DOMAIN` and loaded via `os.getenv` rather than hardcoded in `urls.py`. Update this value whenever a new Codespace is created.
- `DEBUG` must be set to `False` in production, and `STATIC_ROOT` must be configured with a `collectstatic` step for static files to be served correctly.
- The intended production platform is Render or Railway using PostgreSQL. Switching from SQLite requires no code changes but `dj-database-url` configuration needs to be added to `settings.py`.

---

## Lessons Learned & Retrospective

### Haylee (Lee) Paredes -- Auth & Backend

The biggest thing I learned was how much a well-designed data model simplifies everything that comes after it. I also had never configured SMTP in a web application before, so wiring up the email-based password reset end-to-end with real Gmail delivery was the part of the project I am most proud of. If I could go back, I would push for the team to agree on consistent naming conventions for API endpoints earlier, since some inconsistencies came up later that had to be patched.

### Teresa (Tessa) -- Frontend Lead / Scrum Master

I learned a lot during this project, especially about Scrum workflows and using Django. While Django was challenging at first, it became much easier once things started to come together. One thing I would improve is group communication. In-person meetings worked best, but when that was not possible, messages on Discord were sometimes missed. I also want to keep improving my HTML skills. Overall, I am proud of what Group 3 accomplished. We built something that works well and looks good.

### Kaheel -- Backend / Profiles

From this capstone class, I developed stronger collaboration skills through group work, gained experience using Django, and bettered my understanding to compose and structure projects effectively. One area I would approach differently in the future is time management. I would plan my schedule more carefully to dedicate more consistent time to contributing to the project. Overall, I'm proud of the final product my group created and the effort we put into bringing it together.

### Aryan -- Backend / UI

Working on StudyStream pushed me to apply and deepen skills I had been building across my Python, Java, and AI coursework in ways that felt genuinely practical. While I came in with a solid foundation in object-oriented programming and had experimented with AI integration in prior projects, this was my first time architecting a full Django web application from the ground up -- connecting models, views, URLs, and templates into a cohesive, database-backed system. I learned how much complexity lives in the details: getting form redirects to behave correctly, structuring CSS design systems for consistency across pages, and making frontend interactions feel polished rather than just functional. If I could do it over, I would invest more time upfront in planning a clean URL and template structure, rather than refactoring it mid-project -- technical debt compounds fast in a team setting. What I'm most proud of is the UI work: I built a glassmorphic design system with animated cards, anamorphic nav effects, and a unified visual language across every page, turning what could have been a plain student tool into something that actually looks and feels like a real app.

---

## Appendices

### Appendix A -- Project Structure Reference

### Appendix B -- Full ERD

![ERD Diagram](images/Appendix%20B.pdf)

### Appendix C -- Demo Data

The repository includes a management command that seeds the database with realistic demo data:

This creates sample users, semesters, courses, assignments, and work shifts that demonstrate the workload analysis and conflict detection features without manual data entry.
```
python manage.py seed_demo_data
```
### Appendix D -- GitHub Project Board

![Project Board](images/Appendix%20D.png)

### Appendix E -- Code Excerpts

Key code files are included as printed appendices in the physical binder. Files covered: `accounts/views.py` (excerpts), `accounts/urls.py`, `accounts/models.py`, `core/models.py`, `core/scheduling.py`, `home/workload_engine.py` (key functions), `home/workload_config.py`, and `studystream/settings.py`.
