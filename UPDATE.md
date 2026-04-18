# Updates - April 16, 2026

## Dark Mode Dropdown Fix
- Fixed white text visibility issue in form dropdown menus in dark mode
- Added `color-scheme: dark` CSS to all form select elements
- Updated all form templates:
  - `recurring_shift_form.html`
  - `work_shift_form.html`
  - `personal_event_form.html`
  - `recurring_personal_event_form.html`
  - `recurring_job_title_form.html`
  - `recurring_location_form.html`

## Add Work Shift - Recurring Template Feature
- Added ability to create shifts from recurring shift templates
- Users can select between:
  - **One-time shift** (default)
  - **Recurring shift template**

### Recurrence Options
When selecting "Recurring shift template", users can now:
1. Select a saved recurring template
2. Choose repeat pattern:
   - Weekly (every 7 days)
   - Every 2 Weeks (every 14 days)
   - Monthly (same day each month)
3. Set an end date for the recurring shifts

### Auto-Fill Feature
- Start time, end time, and location are automatically filled from the selected template
- Multiple individual shifts are generated based on the recurrence pattern
- All shifts appear on the dashboard calendar

### Updated Files
- `home/forms.py` - Added `WorkShiftForm` fields for recurrence
- `home/views.py` - Updated `add_work_shift` view to generate multiple shifts
- `home/templates/home/work_shift_form.html` - Added UI for recurrence controls

## Updates - April 18, 2026

## Workload Density Engine + Forecast
- Added a centralized workload engine that computes weekly workload snapshots, utilization ratio, and status bands (GREEN/YELLOW/RED)
- Added 4-week forecast output with workload alerts and recommendation payloads
- Added persistence to WorkloadAnalysis with one row per user/week
- Added management command to recompute workload for all users or a single user:
  - `python manage.py run_workload_analysis`
  - `python manage.py run_workload_analysis --user-id <id>`
  - `python manage.py run_workload_analysis --weeks <n>`

## Assignment + Subtask Schema Upgrade
- Assignment model updates:
  - Added `assignment_id` UUID
  - Renamed `priority` -> `priority_level`
  - Renamed `is_major` -> `is_major_project`
  - Renamed `completion_pct` -> `completion_percentage`
  - Added `due_time`, `submission_link`, `contributes_to_workload`
- Subtask model updates:
  - Added `subtask_id` UUID
  - Renamed `sequence_order` -> `step_order`
  - Renamed `milestone_date` -> `due_date`
  - Added `due_time`, `completion_percentage`
- New migrations added for these upgrades in Accounts and Core apps

## Work Shift Data Model + Form Modernization
- WorkShift now supports richer scheduling fields:
  - `shift_id` UUID
  - `employer_name`
  - `shift_start` / `shift_end` datetime fields
  - `is_confirmed`, `is_recurring`, `recurrence_pattern`
  - Auto-derived `duration_hours`
- Add/Edit work shift flows updated to use datetime-based scheduling and to recompute workload after changes
- Work shift form updated from separate date/time fields to start/end datetime fields

## Dashboard / Planner UX Improvements
- Planner redesigned with tabbed views: All / Assignments / Events
- Assignment rows changed to compact bubble-style status icons
- Added one-click assignment status cycling (not started -> in progress -> complete)
- Improved due-date display metadata for assignment rows (weekday + month/day + optional label)
- Added inline subtask editing for title, due date/time, and estimated hours
- Added workload summary card and workload density widget with:
  - current-week utilization
  - assignment/work/available-study hour breakdown
  - upcoming week indicator
  - workload warning summary
- Updated week-bucket logic for stats to align with Monday-Sunday behavior

## Color and Theme Improvements
- Split color palettes so course colors are distinct from personal/work schedule colors
- Expanded to at least 8 selectable color options for course and schedule contexts
- Softened light-mode bubble backgrounds and borders to reduce glare
- Fixed dark mode leakage by scoping light-mode styles to `[data-theme="light"]`

## API and Backend Integration Updates
- Added subtask edit endpoint:
  - `accounts/api/subtasks/<pk>/edit/`
- Assignment and subtask API responses now include upgraded schema fields
- Workload recomputation is now triggered on assignment/work-shift create/edit/delete/status updates
- Added workload constants/config payloads to dashboard context

## Seed Data + Admin + Documentation
- Expanded demo seed command with richer assignment/subtask/timeblock/workload sample data
- Registered WorkloadAnalysis in Django admin
- Updated README with workload analysis command usage
- Updated ERD documentation in `docs/database-erd.md` to reflect the current Accounts/Core/Auth schema and relationships
