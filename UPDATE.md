# StudyStream Update Log

## 2026-04-22

### Schedule Conflict UX and Behavior
- Fixed conflict-resolution flow so selecting `Replace Existing Item` or `Use Suggested Time` reliably applies changes and refreshes dashboard state.
- Added StudyStream-style schedule warning modal to Add Work Shift form page with:
  - `Keep Current Schedule`
  - `Replace Existing Item`
- Enabled replace-on-conflict behavior for Add Work Shift form submissions.

### Workload Preferences (User Settings)
- Added workload preference fields to `Profile`:
  - `sleep_hours_per_night`
  - `sleep_start_time`
  - `sleep_end_time`
  - `personal_time_hours_per_week`
  - `family_time_hours_per_week`
  - `commute_time_hours_per_week`
- Added settings form to edit these values in `accounts/settings/`.
- Workload analysis now uses these user-specific preferences when computing available weekly study time.
- Schedule suggestion logic now avoids sleep and reserved personal/family/commute windows.

### Online Course Workload Support
- Added `weekly_study_hours` to `Course` for async/online classes without fixed meeting times.
- Wired the new field through:
  - course create/edit/list APIs
  - dashboard course modal UI
  - dashboard course JSON serialization
- Workload engine now includes `weekly_study_hours` in class-hour totals.

### Dashboard UX Improvements
- Added `View Courses` option under semester/courses `Manage` menu.
- Added current-course management modal with quick edit/add actions.
- Added hover detail card for each course chip in semester/courses bubble showing:
  - course code + name
  - professor
  - meeting times
  - weekly async study hours
- Fixed workload warning card to reflect current summary status even when alerts list is empty.

### Documentation Cleanup
- Consolidated setup docs into `README.md` and removed `SETUP.md`.
- Added `docs/project-structure.md` with folder diagram and Django file-role explanations.
- Updated `docs/database-erd.md` to match current models.
- Added a simplified presentation-friendly ERD section.

### Tests and Migrations
- Added/updated tests for:
  - conflict resolution behaviors
  - settings preference persistence
  - workload preference calculations
  - online course weekly-hour workload inclusion
- Added migrations:
  - `accounts.0007_profile_workload_preferences`
  - `accounts.0008_course_weekly_study_hours`

## 2026-04-18

### Workload Density Engine + Forecast
- Added workload engine to compute weekly snapshots, utilization ratio, and status bands (GREEN/YELLOW/RED).
- Added 4-week forecast output with alert and recommendation payloads.
- Added persistence to `WorkloadAnalysis` with one record per user/week.
- Added command support:
  - `python manage.py run_workload_analysis`
  - `python manage.py run_workload_analysis --user-id <id>`
  - `python manage.py run_workload_analysis --weeks <n>`

### Assignment + Subtask Schema Upgrade
- Assignment changes:
  - added `assignment_id` UUID
  - renamed `priority` -> `priority_level`
  - renamed `is_major` -> `is_major_project`
  - renamed `completion_pct` -> `completion_percentage`
  - added `due_time`, `submission_link`, `contributes_to_workload`
- Subtask changes:
  - added `subtask_id` UUID
  - renamed `sequence_order` -> `step_order`
  - renamed `milestone_date` -> `due_date`
  - added `due_time`, `completion_percentage`

### Work Shift Data Model + Form Modernization
- WorkShift improvements:
  - `shift_id` UUID
  - `employer_name`
  - `shift_start` / `shift_end` datetime fields
  - `is_confirmed`, `is_recurring`, `recurrence_pattern`
  - derived `duration_hours`
- Updated add/edit work-shift flows to use datetime scheduling and trigger workload recomputation.

### Dashboard / Planner UX Improvements
- Planner tabbed views: All / Assignments / Events.
- Compact assignment status bubble UI with one-click status cycling.
- Improved due-date display metadata.
- Added inline subtask editing for title, due date/time, and estimated hours.
- Added workload summary and density widgets with current-week and upcoming-week signals.

### Color and Theme Updates
- Split course color palette from schedule color palette.
- Expanded selectable colors for course/schedule contexts.
- Improved light-mode bubble contrast.
- Scoped light-mode overrides to `[data-theme="light"]`.

### API and Integration Updates
- Added subtask edit endpoint: `accounts/api/subtasks/<pk>/edit/`.
- Expanded assignment/subtask API payloads to include upgraded fields.
- Triggered workload recomputation on assignment/work-shift create/edit/delete/status changes.

## 2026-04-16

### Dark Mode Dropdown Fix
- Fixed form dropdown text visibility in dark mode.
- Added `color-scheme: dark` handling for select inputs in scheduling-related forms.

### Add Work Shift: Recurring Template Feature
- Added support for creating shifts from recurring templates.
- Added recurrence options:
  - weekly
  - biweekly
  - monthly
- Added recurrence end date support.
- Added auto-fill of start/end time and location from selected recurring template.
- Added multi-shift generation based on selected recurrence pattern.
