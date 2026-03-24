from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from core.models import PersonalEvent, WorkShift
import json


def home_view(request):
    return render(request, "home/home.html")


@login_required
def dashboard(request):
    personal_events = PersonalEvent.objects.filter(user=request.user)
    work_shifts = WorkShift.objects.filter(user=request.user)

    calendar_events = []

    for event in personal_events:
        if event.start_time and event.end_time:
            calendar_events.append({
                "title": event.title,
                "start": f"{event.event_date}T{event.start_time}",
                "end": f"{event.event_date}T{event.end_time}",
            })
        else:
            calendar_events.append({
                "title": event.title,
                "start": str(event.event_date),
                "allDay": True,
            })

    for shift in work_shifts:
        calendar_events.append({
            "title": f"Work: {shift.job_title}" if shift.job_title else "Work Shift",
            "start": f"{shift.shift_date}T{shift.start_time}",
            "end": f"{shift.shift_date}T{shift.end_time}",
        })

    context = {
        "calendar_events_json": json.dumps(calendar_events),
        "personal_events": personal_events,
        "work_shifts": work_shifts,
    }

    return render(request, "home/dashboard.html", context)