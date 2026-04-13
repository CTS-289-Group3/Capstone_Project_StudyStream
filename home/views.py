import json
from calendar import monthrange
from datetime import date, time, timedelta

from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import Assignment, Course, Profile, Semester, Tag
from core.models import (
    PersonalEvent,
    RecurringPersonalEvent,
    RecurringJobTitle,
    RecurringWorkLocation,
    RecurringWorkShift,
    WorkShift,
)

from .forms import (
    PersonalEventForm,
    RecurringPersonalEventForm,
    RecurringJobTitleForm,
    RecurringWorkLocationForm,
    RecurringWorkShiftForm,
    WorkShiftForm,
)


def _parse_weekdays(raw_weekdays):
    if not raw_weekdays:
        return set()
    parsed = set()
    for value in raw_weekdays.split(","):
        value = value.strip()
        if not value:
            continue
        try:
            day_index = int(value)
        except ValueError:
            continue
        if 0 <= day_index <= 6:
            parsed.add(day_index)
    return parsed


def _generate_recurring_personal_occurrences(recurring_events, range_start, range_end):
    occurrences = []

    for recurring_event in recurring_events:
        if recurring_event.recurrence_pattern in {"weekly", "biweekly"}:
            weekdays = _parse_weekdays(recurring_event.weekdays)
            if not weekdays:
                weekdays = {recurring_event.start_date.weekday()}

            current_date = range_start
            while current_date <= range_end:
                if current_date < recurring_event.start_date:
                    current_date += timedelta(days=1)
                    continue

                if current_date.weekday() not in weekdays:
                    current_date += timedelta(days=1)
                    continue

                if recurring_event.recurrence_pattern == "biweekly":
                    weeks_since_start = (current_date - recurring_event.start_date).days // 7
                    if weeks_since_start % 2 != 0:
                        current_date += timedelta(days=1)
                        continue

                occurrences.append(
                    {
                        "title": recurring_event.title,
                        "event_date": current_date,
                        "start_time": recurring_event.start_time,
                        "end_time": recurring_event.end_time,
                        "location": recurring_event.location,
                        "recurrence_label": recurring_event.get_recurrence_pattern_display(),
                    }
                )
                current_date += timedelta(days=1)

        elif recurring_event.recurrence_pattern == "monthly":
            day_of_month = recurring_event.monthly_day or recurring_event.start_date.day
            year = range_start.year
            month = range_start.month

            while date(year, month, 1) <= range_end:
                max_day = monthrange(year, month)[1]
                candidate_date = date(year, month, min(day_of_month, max_day))

                if (
                    candidate_date >= range_start
                    and candidate_date <= range_end
                    and candidate_date >= recurring_event.start_date
                ):
                    occurrences.append(
                        {
                            "title": recurring_event.title,
                            "event_date": candidate_date,
                            "start_time": recurring_event.start_time,
                            "end_time": recurring_event.end_time,
                            "location": recurring_event.location,
                            "recurrence_label": recurring_event.get_recurrence_pattern_display(),
                        }
                    )

                if month == 12:
                    month = 1
                    year += 1
                else:
                    month += 1

    occurrences.sort(key=lambda item: (item["event_date"], item["start_time"] or time.min))
    return occurrences


def _get_work_shift_quick_options(user):
    recurring_shifts = RecurringWorkShift.objects.filter(user=user, is_active=True).order_by("name")
    recurring_locations = RecurringWorkLocation.objects.filter(user=user, is_active=True).order_by("name")
    recurring_job_titles = RecurringJobTitle.objects.filter(user=user, is_active=True).order_by("title")
    recent_shifts = WorkShift.objects.filter(user=user).order_by("-created_at")

    location_options = []
    seen_locations = set()

    for recurring_location in recurring_locations.values_list("name", flat=True):
        normalized = recurring_location.strip().lower()
        if normalized in seen_locations:
            continue
        seen_locations.add(normalized)
        location_options.append(recurring_location.strip())

    for location in recent_shifts.values_list("location", flat=True):
        if not location:
            continue
        normalized = location.strip().lower()
        if normalized in seen_locations:
            continue
        seen_locations.add(normalized)
        location_options.append(location.strip())
        if len(location_options) >= 8:
            break

    job_title_options = []
    seen_job_titles = set()

    for recurring_job_title in recurring_job_titles.values_list("title", flat=True):
        normalized = recurring_job_title.strip().lower()
        if normalized in seen_job_titles:
            continue
        seen_job_titles.add(normalized)
        job_title_options.append(recurring_job_title.strip())

    for job_title in recent_shifts.values_list("job_title", flat=True):
        if not job_title:
            continue
        normalized = job_title.strip().lower()
        if normalized in seen_job_titles:
            continue
        seen_job_titles.add(normalized)
        job_title_options.append(job_title.strip())
        if len(job_title_options) >= 8:
            break

    shift_presets = [
        {"label": "Morning Shift (7:00 AM - 4:00 PM)", "start": "07:00", "end": "16:00"},
        {"label": "Mid Shift (10:00 AM - 7:00 PM)", "start": "10:00", "end": "19:00"},
    ]

    seen_ranges = {("07:00", "16:00"), ("10:00", "19:00")}

    for recurring in recurring_shifts:
        start_str = recurring.start_time.strftime("%H:%M")
        end_str = recurring.end_time.strftime("%H:%M")
        key = (start_str, end_str)
        seen_ranges.add(key)
        shift_presets.append({
            "label": f"Recurring: {recurring.name} ({recurring.start_time.strftime('%I:%M %p')} - {recurring.end_time.strftime('%I:%M %p')})",
            "start": start_str,
            "end": end_str,
            "location": recurring.location,
        })

    for start_time, end_time in recent_shifts.values_list("start_time", "end_time"):
        start_str = start_time.strftime("%H:%M")
        end_str = end_time.strftime("%H:%M")
        key = (start_str, end_str)
        if key in seen_ranges:
            continue
        seen_ranges.add(key)
        shift_presets.append({
            "label": f"Recent Shift ({start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')})",
            "start": start_str,
            "end": end_str,
        })
        if len(shift_presets) >= 6:
            break

    return {
        "location_options": location_options,
        "job_title_options": job_title_options,
        "shift_presets": shift_presets,
        "recurring_count": recurring_shifts.count(),
        "recurring_location_count": recurring_locations.count(),
        "recurring_job_title_count": recurring_job_titles.count(),
    }


def home_view(request):
    user = request.user
    profile = Profile.objects.filter(user=user).first()
    profile_display_name = (profile.display_name if profile and profile.display_name else user.username)
    profile_avatar_text = (profile.avatar_text[:1].upper() if profile and profile.avatar_text else profile_display_name[:1].upper())
    now = timezone.now()
    week_end = now + timedelta(days=7)

    semesters = list(
        Semester.objects.filter(user=user).values('id', 'name', 'is_active', 'start_date', 'end_date')
    )
    active_sem = Semester.objects.filter(user=user, is_active=True).first()
    courses = list(
        Course.objects.filter(user=user)
        .select_related('semester')
        .values(
            'id',
            'course_code',
            'course_name',
            'color_hex',
            'semester__id',
            'semester__name',
            'professor_name',
            'meeting_times',
        )
    )
    tags = list(Tag.objects.filter(user=user).values('id', 'name', 'color_hex'))

    all_assignments = Assignment.objects.filter(user=user).select_related('course').prefetch_related('tags', 'subtasks')

    assignments_data = []
    for assignment in all_assignments.order_by('due_date'):
        assignments_data.append(
            {
                'id': assignment.id,
                'title': assignment.title,
                'course_id': assignment.course_id,
                'course_code': assignment.course.course_code,
                'course_name': assignment.course.course_name,
                'course_color': assignment.course.color_hex,
                'due_date': assignment.due_date.isoformat(),
                'status': assignment.status,
                'priority': assignment.priority,
                'completion_pct': assignment.completion_pct,
                'is_major': assignment.is_major,
                'assignment_type': assignment.assignment_type,
                'subtask_count': assignment.subtasks.count(),
                'subtask_done': assignment.subtasks.filter(status='complete').count(),
                'tags': [
                    {'id': tag.id, 'name': tag.name, 'color_hex': tag.color_hex}
                    for tag in assignment.tags.all()
                ],
            }
        )

    due_this_week = all_assignments.filter(
        due_date__gte=now,
        due_date__lte=week_end,
        status__in=['not_started', 'in_progress'],
    ).count()
    completed = all_assignments.filter(status='complete').count()
    overdue = all_assignments.filter(
        due_date__lt=now,
        status__in=['not_started', 'in_progress'],
    ).count()
    active_courses = Course.objects.filter(user=user, semester__is_active=True).count()

    work_shifts_data = []
    for shift in WorkShift.objects.filter(user=user).order_by('shift_date', 'start_time'):
        work_shifts_data.append({
            'id': shift.id,
            'title': shift.job_title or 'Work Shift',
            'shift_date': shift.shift_date.isoformat(),
            'start_time': shift.start_time.strftime('%H:%M'),
            'end_time': shift.end_time.strftime('%H:%M'),
            'location': shift.location,
            'color_hex': shift.color_hex or '#10b981',
        })

    today_local = timezone.localdate()

    one_time_personal = PersonalEvent.objects.filter(
        user=user,
        event_date__gte=today_local,
        event_date__lte=today_local + timedelta(days=90),
    ).order_by('event_date', 'start_time')

    recurring_personal = RecurringPersonalEvent.objects.filter(user=user, is_active=True)

    personal_events_data = []
    for event in one_time_personal:
        personal_events_data.append({
            'title': event.title,
            'event_date': event.event_date.isoformat(),
            'start_time': event.start_time.strftime('%H:%M') if event.start_time else None,
            'location': event.location or '',
            'recurrence_label': '',
            'color_hex': event.color_hex or '#FCAF17',
        })
    for occ in _generate_recurring_personal_occurrences(recurring_personal, today_local, today_local + timedelta(days=90)):
        personal_events_data.append({
            'title': occ['title'],
            'event_date': occ['event_date'].isoformat(),
            'start_time': occ['start_time'].strftime('%H:%M') if occ['start_time'] else None,
            'location': occ.get('location', '') or '',
            'recurrence_label': occ.get('recurrence_label', ''),
            'color_hex': '#FCAF17',
        })
    personal_events_data.sort(key=lambda e: (e['event_date'], e['start_time'] or ''))

    context = {
        'user': user,
        'profile_display_name': profile_display_name,
        'profile_avatar_text': profile_avatar_text,
        'semesters_json': json.dumps(semesters, cls=DjangoJSONEncoder),
        'courses_json': json.dumps(courses, cls=DjangoJSONEncoder),
        'assignments_json': json.dumps(assignments_data, cls=DjangoJSONEncoder),
        'tags_json': json.dumps(tags, cls=DjangoJSONEncoder),
        'work_shifts_json': json.dumps(work_shifts_data, cls=DjangoJSONEncoder),
        'personal_events_json': json.dumps(personal_events_data, cls=DjangoJSONEncoder),
        'active_sem_id': active_sem.id if active_sem else None,
        'stats': {
            'due_this_week': due_this_week,
            'completed': completed,
            'overdue': overdue,
            'active_courses': active_courses,
        },
    }
    return render(request, 'home/home.html', context)


@login_required
def dashboard(request):
    today = timezone.localdate()
    range_end = today + timedelta(days=90)

    one_time_personal_events = PersonalEvent.objects.filter(user=request.user, event_date__gte=today)
    recurring_personal_events = RecurringPersonalEvent.objects.filter(user=request.user, is_active=True)
    work_shifts = WorkShift.objects.filter(user=request.user)

    personal_events = []
    for personal_event in one_time_personal_events:
        personal_events.append(
            {
                "title": personal_event.title,
                "event_date": personal_event.event_date,
                "start_time": personal_event.start_time,
                "end_time": personal_event.end_time,
                "location": personal_event.location,
                "recurrence_label": "",
            }
        )

    personal_events.extend(
        _generate_recurring_personal_occurrences(recurring_personal_events, today, range_end)
    )
    personal_events.sort(key=lambda item: (item["event_date"], item["start_time"] or time.min))

    calendar_events = []

    for event in personal_events:
        if event.get("start_time") and event.get("end_time"):
            calendar_events.append({
                "title": event["title"],
                "start": f"{event['event_date']}T{event['start_time']}",
                "end": f"{event['event_date']}T{event['end_time']}",
                "classNames": ["personal-event"],
            })
        else:
            calendar_events.append({
                "title": event["title"],
                "start": str(event["event_date"]),
                "allDay": True,
                "classNames": ["personal-event"],
            })

    for shift in work_shifts:
        calendar_events.append({
            "title": f"Work: {shift.job_title}" if shift.job_title else "Work Shift",
            "start": f"{shift.shift_date}T{shift.start_time}",
            "end": f"{shift.shift_date}T{shift.end_time}",
            "color": shift.color_hex or "#10b981",
            "classNames": ["work-event"],
        })

    context = {
        "calendar_events": calendar_events,
        "total_events": len(calendar_events),
        "personal_events": personal_events,
        "work_shifts": work_shifts,
    }

    return render(request, "home/dashboard.html", context)


@login_required
def add_personal_event(request):
    if request.method == "POST":
        form = PersonalEventForm(request.POST)
        if form.is_valid():
            if form.cleaned_data.get("recurring_enabled"):
                form.save_recurring_event(request.user)
            else:
                form.save_personal_event(request.user)
            return redirect("dashboard")
    else:
        form = PersonalEventForm()

    return render(request, "home/personal_event_form.html", {"form": form})


@login_required
def recurring_personal_event_list(request):
    recurring_personal_events = RecurringPersonalEvent.objects.filter(user=request.user).order_by(
        "-updated_at", "title"
    )
    return render(
        request,
        "home/recurring_personal_event_list.html",
        {"recurring_personal_events": recurring_personal_events},
    )


@login_required
def add_recurring_personal_event(request):
    if request.method == "POST":
        form = RecurringPersonalEventForm(request.POST)
        if form.is_valid():
            recurring_personal_event = form.save(commit=False)
            recurring_personal_event.user = request.user
            recurring_personal_event.save()
            return redirect("recurring_personal_event_list")
    else:
        form = RecurringPersonalEventForm()

    context = {
        "form": form,
        "page_title": "Add Recurring Personal Event",
        "submit_label": "Save Recurring Event",
    }
    return render(request, "home/recurring_personal_event_form.html", context)


@login_required
def edit_recurring_personal_event(request, event_id):
    recurring_personal_event = get_object_or_404(RecurringPersonalEvent, id=event_id, user=request.user)

    if request.method == "POST":
        form = RecurringPersonalEventForm(request.POST, instance=recurring_personal_event)
        if form.is_valid():
            form.save()
            return redirect("recurring_personal_event_list")
    else:
        form = RecurringPersonalEventForm(instance=recurring_personal_event)

    context = {
        "form": form,
        "page_title": "Edit Recurring Personal Event",
        "submit_label": "Update Recurring Event",
    }
    return render(request, "home/recurring_personal_event_form.html", context)


@login_required
def delete_recurring_personal_event(request, event_id):
    recurring_personal_event = get_object_or_404(RecurringPersonalEvent, id=event_id, user=request.user)
    if request.method == "POST":
        recurring_personal_event.delete()
    return redirect("recurring_personal_event_list")


@login_required
def add_work_shift(request):
    quick_options = _get_work_shift_quick_options(request.user)

    if request.method == "POST":
        form = WorkShiftForm(request.POST)
        if form.is_valid():
            shift = form.save(commit=False)
            shift.user = request.user
            shift.save()
            return redirect("dashboard")
    else:
        form = WorkShiftForm()

    context = {
        "form": form,
        "location_options": quick_options["location_options"],
        "job_title_options": quick_options["job_title_options"],
        "shift_presets": quick_options["shift_presets"],
        "recurring_count": quick_options["recurring_count"],
        "recurring_location_count": quick_options["recurring_location_count"],
        "recurring_job_title_count": quick_options["recurring_job_title_count"],
    }
    return render(request, "home/work_shift_form.html", context)


@login_required
def recurring_shift_list(request):
    recurring_shifts = RecurringWorkShift.objects.filter(user=request.user).order_by("-updated_at", "name")
    return render(request, "home/recurring_shift_list.html", {"recurring_shifts": recurring_shifts})


@login_required
def add_recurring_shift(request):
    if request.method == "POST":
        form = RecurringWorkShiftForm(request.POST)
        if form.is_valid():
            recurring_shift = form.save(commit=False)
            recurring_shift.user = request.user
            recurring_shift.save()
            return redirect("recurring_shift_list")
    else:
        form = RecurringWorkShiftForm()

    context = {
        "form": form,
        "page_title": "Add Recurring Shift",
        "submit_label": "Save Recurring Shift",
    }
    return render(request, "home/recurring_shift_form.html", context)


@login_required
def edit_recurring_shift(request, shift_id):
    recurring_shift = get_object_or_404(RecurringWorkShift, id=shift_id, user=request.user)

    if request.method == "POST":
        form = RecurringWorkShiftForm(request.POST, instance=recurring_shift)
        if form.is_valid():
            form.save()
            return redirect("recurring_shift_list")
    else:
        form = RecurringWorkShiftForm(instance=recurring_shift)

    context = {
        "form": form,
        "page_title": "Edit Recurring Shift",
        "submit_label": "Update Recurring Shift",
    }
    return render(request, "home/recurring_shift_form.html", context)


@login_required
def delete_recurring_shift(request, shift_id):
    recurring_shift = get_object_or_404(RecurringWorkShift, id=shift_id, user=request.user)
    if request.method == "POST":
        recurring_shift.delete()
    return redirect("recurring_shift_list")


@login_required
def recurring_location_list(request):
    recurring_locations = RecurringWorkLocation.objects.filter(user=request.user).order_by("-updated_at", "name")
    return render(request, "home/recurring_location_list.html", {"recurring_locations": recurring_locations})


@login_required
def add_recurring_location(request):
    if request.method == "POST":
        form = RecurringWorkLocationForm(request.POST)
        if form.is_valid():
            recurring_location = form.save(commit=False)
            recurring_location.user = request.user
            recurring_location.save()
            return redirect("recurring_location_list")
    else:
        form = RecurringWorkLocationForm()

    context = {
        "form": form,
        "page_title": "Add Recurring Location",
        "submit_label": "Save Recurring Location",
    }
    return render(request, "home/recurring_location_form.html", context)


@login_required
def edit_recurring_location(request, location_id):
    recurring_location = get_object_or_404(RecurringWorkLocation, id=location_id, user=request.user)

    if request.method == "POST":
        form = RecurringWorkLocationForm(request.POST, instance=recurring_location)
        if form.is_valid():
            form.save()
            return redirect("recurring_location_list")
    else:
        form = RecurringWorkLocationForm(instance=recurring_location)

    context = {
        "form": form,
        "page_title": "Edit Recurring Location",
        "submit_label": "Update Recurring Location",
    }
    return render(request, "home/recurring_location_form.html", context)


@login_required
def delete_recurring_location(request, location_id):
    recurring_location = get_object_or_404(RecurringWorkLocation, id=location_id, user=request.user)
    if request.method == "POST":
        recurring_location.delete()
    return redirect("recurring_location_list")


@login_required
def recurring_job_title_list(request):
    recurring_job_titles = RecurringJobTitle.objects.filter(user=request.user).order_by("-updated_at", "title")
    return render(request, "home/recurring_job_title_list.html", {"recurring_job_titles": recurring_job_titles})


@login_required
def add_recurring_job_title(request):
    if request.method == "POST":
        form = RecurringJobTitleForm(request.POST)
        if form.is_valid():
            recurring_job_title = form.save(commit=False)
            recurring_job_title.user = request.user
            recurring_job_title.save()
            return redirect("recurring_job_title_list")
    else:
        form = RecurringJobTitleForm()

    context = {
        "form": form,
        "page_title": "Add Recurring Job Title",
        "submit_label": "Save Recurring Job Title",
    }
    return render(request, "home/recurring_job_title_form.html", context)


@login_required
def edit_recurring_job_title(request, title_id):
    recurring_job_title = get_object_or_404(RecurringJobTitle, id=title_id, user=request.user)

    if request.method == "POST":
        form = RecurringJobTitleForm(request.POST, instance=recurring_job_title)
        if form.is_valid():
            form.save()
            return redirect("recurring_job_title_list")
    else:
        form = RecurringJobTitleForm(instance=recurring_job_title)

    context = {
        "form": form,
        "page_title": "Edit Recurring Job Title",
        "submit_label": "Update Recurring Job Title",
    }
    return render(request, "home/recurring_job_title_form.html", context)


@login_required
def delete_recurring_job_title(request, title_id):
    recurring_job_title = get_object_or_404(RecurringJobTitle, id=title_id, user=request.user)
    if request.method == "POST":
        recurring_job_title.delete()
    return redirect("recurring_job_title_list")