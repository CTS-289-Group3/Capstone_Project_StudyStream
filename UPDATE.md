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
