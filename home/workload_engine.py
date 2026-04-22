from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import Assignment, Course, Profile
from core.models import WorkShift, WorkloadAnalysis

from .workload_config import NOTIFICATIONS, WORKLOAD_DENSITY_COLORS

WEEK_HOURS = Decimal("168.00")
SLEEP_HOURS = Decimal("49.00")
PERSONAL_HOURS = Decimal("14.00")

DAY_NAME_TO_INDEX = {
    "MON": 0,
    "TUE": 1,
    "WED": 2,
    "THU": 3,
    "FRI": 4,
    "SAT": 5,
    "SUN": 6,
}


def week_start(day_value: date) -> date:
    return day_value - timedelta(days=day_value.weekday())


def _to_decimal(value, default: str = "0.00") -> Decimal:
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _parse_clock_token(token: str):
    clean = token.strip().lower().replace(".", "")
    if not clean:
        return None
    for fmt in ("%I:%M%p", "%I%p", "%H:%M", "%H"):
        try:
            return datetime.strptime(clean, fmt).time()
        except ValueError:
            continue
    return None


def _extract_day_indexes(meeting_times: str):
    text = (meeting_times or "").upper()
    days = set()

    # Explicit day names and abbreviations.
    for token, idx in DAY_NAME_TO_INDEX.items():
        if re.search(rf"\b{token}\b", text):
            days.add(idx)
    alias_map = {
        "MONDAY": 0,
        "TUESDAY": 1,
        "WEDNESDAY": 2,
        "THURSDAY": 3,
        "FRIDAY": 4,
        "SATURDAY": 5,
        "SUNDAY": 6,
        "M": 0,
        "T": 1,
        "W": 2,
        "R": 3,
        "F": 4,
        "S": 5,
        "U": 6,
    }
    for alias, idx in alias_map.items():
        if re.search(rf"\b{alias}\b", text):
            days.add(idx)

    if days:
        return days

    # Compressed format like MWF 9:00-9:50 or TR 1:30-2:45.
    first_digit_idx = re.search(r"\d", text)
    prefix = text if first_digit_idx is None else text[: first_digit_idx.start()]
    compact = re.sub(r"[^A-Z]", "", prefix)
    for char in compact:
        if char in alias_map:
            days.add(alias_map[char])
    return days


def _extract_duration_hours(meeting_times: str) -> Decimal:
    text = (meeting_times or "").strip()
    if not text:
        return Decimal("0.00")

    match = re.search(
        r"(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*[-\u2013]\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return Decimal("0.00")

    start_raw, end_raw = match.group(1).strip(), match.group(2).strip()
    start_has_meridiem = bool(re.search(r"(am|pm)$", start_raw, flags=re.IGNORECASE))
    end_meridiem_match = re.search(r"(am|pm)$", end_raw, flags=re.IGNORECASE)
    if not start_has_meridiem and end_meridiem_match:
        start_raw = f"{start_raw}{end_meridiem_match.group(1)}"

    start_time = _parse_clock_token(start_raw)
    end_time = _parse_clock_token(end_raw)
    if not start_time or not end_time:
        return Decimal("0.00")

    start_dt = datetime.combine(date.today(), start_time)
    end_dt = datetime.combine(date.today(), end_time)
    if end_dt <= start_dt:
        end_dt += timedelta(hours=12)

    duration_hours = Decimal(str((end_dt - start_dt).total_seconds() / 3600)).quantize(Decimal("0.01"))
    return max(duration_hours, Decimal("0.00"))


def _compute_weekly_class_hours(user) -> Decimal:
    total = Decimal("0.00")
    courses = Course.objects.filter(user=user, semester__is_active=True).only("meeting_times", "weekly_study_hours")
    for course in courses:
        duration = _extract_duration_hours(course.meeting_times)
        if duration <= 0:
            total += _to_decimal(course.weekly_study_hours)
            continue
        day_count = len(_extract_day_indexes(course.meeting_times))
        if day_count <= 0:
            total += _to_decimal(course.weekly_study_hours)
            continue
        total += (duration * Decimal(day_count)) + _to_decimal(course.weekly_study_hours)
    return total.quantize(Decimal("0.01"))


def _get_capacity_preferences(user):
    profile = Profile.objects.filter(user=user).only(
        'sleep_hours_per_night',
        'personal_time_hours_per_week',
        'family_time_hours_per_week',
        'commute_time_hours_per_week',
    ).first()

    if not profile:
        return {
            'sleep_hours_per_week': SLEEP_HOURS,
            'personal_hours_per_week': PERSONAL_HOURS,
            'family_hours_per_week': Decimal('0.00'),
            'commute_hours_per_week': Decimal('0.00'),
        }

    sleep_hours_per_week = (_to_decimal(profile.sleep_hours_per_night, '7.0') * Decimal('7.0')).quantize(Decimal('0.01'))
    return {
        'sleep_hours_per_week': sleep_hours_per_week,
        'personal_hours_per_week': _to_decimal(profile.personal_time_hours_per_week, '14.0').quantize(Decimal('0.01')),
        'family_hours_per_week': _to_decimal(profile.family_time_hours_per_week, '0.0').quantize(Decimal('0.01')),
        'commute_hours_per_week': _to_decimal(profile.commute_time_hours_per_week, '0.0').quantize(Decimal('0.01')),
    }


def _compute_weekly_snapshot(user, week_start_date: date):
    week_end_date = week_start_date + timedelta(days=7)
    assignments = list(
        Assignment.objects.filter(
            user=user,
            contributes_to_workload=True,
            status__in=["not_started", "in_progress"],
            due_date__date__gte=week_start_date,
            due_date__date__lt=week_end_date,
        )
        .select_related("course")
        .order_by("due_date")
    )

    assignment_count = len(assignments)
    major_assignments = [a for a in assignments if _to_decimal(a.estimated_hours) > Decimal("4.0")]
    major_assignment_count = len(major_assignments)

    total_assignment_hours = Decimal("0.00")
    for assignment in assignments:
        total_assignment_hours += _to_decimal(assignment.estimated_hours)

    work_shifts = WorkShift.objects.filter(
        user=user,
        shift_date__gte=week_start_date,
        shift_date__lt=week_end_date,
    ).only("shift_start", "shift_end")
    total_work_hours = Decimal("0.00")
    for shift in work_shifts:
        total_work_hours += _to_decimal(shift.duration_hours)

    total_class_hours = _compute_weekly_class_hours(user)
    preferences = _get_capacity_preferences(user)
    reserved_hours = (
        preferences['sleep_hours_per_week']
        + preferences['personal_hours_per_week']
        + preferences['family_hours_per_week']
        + preferences['commute_hours_per_week']
    )
    available_study_hours = (
        WEEK_HOURS - total_class_hours - total_work_hours - reserved_hours
    ).quantize(Decimal("0.01"))
    available_study_hours = max(Decimal("0.00"), available_study_hours)

    utilization_ratio = Decimal("0.000")
    if available_study_hours > 0:
        utilization_ratio = (total_assignment_hours / available_study_hours).quantize(Decimal("0.001"))

    if utilization_ratio < Decimal("0.600"):
        week_status = WorkloadAnalysis.STATUS_GREEN
    elif utilization_ratio < Decimal("0.850"):
        week_status = WorkloadAnalysis.STATUS_YELLOW
    else:
        week_status = WorkloadAnalysis.STATUS_RED

    deadline_cluster_detected = False
    due_datetimes = [a.due_date for a in major_assignments if a.due_date]
    for idx in range(0, max(0, len(due_datetimes) - 2)):
        if due_datetimes[idx + 2] - due_datetimes[idx] <= timedelta(hours=48):
            deadline_cluster_detected = True
            break

    is_overloaded = week_status == WorkloadAnalysis.STATUS_RED
    iso_year, iso_week, _ = week_start_date.isocalendar()

    return {
        "week_start_date": week_start_date,
        "week_number": iso_week,
        "year": iso_year,
        "total_class_hours": total_class_hours,
        "total_work_hours": total_work_hours.quantize(Decimal("0.01")),
        "total_assignment_hours": total_assignment_hours.quantize(Decimal("0.01")),
        "available_study_hours": available_study_hours,
        "utilization_ratio": utilization_ratio,
        "week_status": week_status,
        "assignment_count": assignment_count,
        "major_assignment_count": major_assignment_count,
        "deadline_cluster_detected": deadline_cluster_detected,
        "is_overloaded": is_overloaded,
        "recommended_actions": [],
        "assignments": assignments,
    }


def _attach_recommendations(snapshots):
    green_indexes = [idx for idx, snap in enumerate(snapshots) if snap["week_status"] == WorkloadAnalysis.STATUS_GREEN]

    for idx, snap in enumerate(snapshots):
        recommendations = list(snap.get("recommended_actions", []))
        if snap["week_status"] == WorkloadAnalysis.STATUS_YELLOW:
            recommendations.append(
                {
                    "action": "plan_ahead",
                    "message": "This week is heavy. Reserve blocks now for larger assignments.",
                }
            )

        if snap["week_status"] == WorkloadAnalysis.STATUS_RED:
            if green_indexes:
                target_idx = min(green_indexes, key=lambda green_idx: abs(green_idx - idx))
                target = snapshots[target_idx]
                move_candidates = sorted(
                    snap.get("assignments", []),
                    key=lambda assignment: _to_decimal(assignment.estimated_hours),
                    reverse=True,
                )[:2]
                titles = ", ".join(candidate.title for candidate in move_candidates if candidate.title)
                if titles:
                    message = (
                        f"Move early work from Week {snap['week_number']} into Week {target['week_number']}: {titles}."
                    )
                else:
                    message = (
                        f"Shift prep from Week {snap['week_number']} into Week {target['week_number']} to reduce load."
                    )
                recommendations.append(
                    {
                        "action": "redistribute_work",
                        "target_week_number": target["week_number"],
                        "message": message,
                    }
                )
            else:
                recommendations.append(
                    {
                        "action": "reduce_load",
                        "message": "No nearby green week is available. Start all major tasks earlier this week.",
                    }
                )

        if snap["deadline_cluster_detected"]:
            recommendations.append(
                {
                    "action": "start_early",
                    "message": "Major deadlines are clustered within 48 hours. Start prep immediately.",
                }
            )

        snap["recommended_actions"] = recommendations


def _build_alerts_from_forecast(snapshots, today: date):
    alerts = []
    config = NOTIFICATIONS.get("workload_alerts", {})

    for snap in snapshots:
        days_until_week = (snap["week_start_date"] - today).days

        if snap["week_status"] == WorkloadAnalysis.STATUS_YELLOW and config.get("yellow_week", {}).get("enabled"):
            tmpl = config["yellow_week"]
            advance_days = int(tmpl.get("advance_notice_days", 14))
            if 0 <= days_until_week <= advance_days:
                alerts.append(
                    {
                        "type": "yellow_week",
                        "week_start_date": snap["week_start_date"],
                        "week_number": snap["week_number"],
                        "title": tmpl.get("title", "Heads up"),
                        "message": tmpl.get("message", "").format(
                            week_number=snap["week_number"],
                            assignment_count=snap["assignment_count"],
                            total_hours=snap["total_assignment_hours"],
                        ),
                        "color": WORKLOAD_DENSITY_COLORS[WorkloadAnalysis.STATUS_YELLOW],
                    }
                )

        if snap["week_status"] == WorkloadAnalysis.STATUS_RED and config.get("red_week", {}).get("enabled"):
            tmpl = config["red_week"]
            advance_days = int(tmpl.get("advance_notice_days", 14))
            if 0 <= days_until_week <= advance_days:
                alerts.append(
                    {
                        "type": "red_week",
                        "week_start_date": snap["week_start_date"],
                        "week_number": snap["week_number"],
                        "title": tmpl.get("title", "Warning").format(week_number=snap["week_number"]),
                        "message": tmpl.get("message", "").format(
                            week_number=snap["week_number"],
                            assignment_count=snap["assignment_count"],
                            total_hours=snap["total_assignment_hours"],
                            available_hours=snap["available_study_hours"],
                        ),
                        "color": WORKLOAD_DENSITY_COLORS[WorkloadAnalysis.STATUS_RED],
                    }
                )

        if snap["deadline_cluster_detected"] and config.get("deadline_cluster", {}).get("enabled"):
            tmpl = config["deadline_cluster"]
            advance_days = int(tmpl.get("advance_notice_days", 14))
            if 0 <= days_until_week <= advance_days:
                other_count = max(0, snap["assignment_count"] - snap["major_assignment_count"])
                alerts.append(
                    {
                        "type": "deadline_cluster",
                        "week_start_date": snap["week_start_date"],
                        "week_number": snap["week_number"],
                        "title": tmpl.get("title", "Deadline cluster"),
                        "message": tmpl.get("message", "").format(
                            major_count=snap["major_assignment_count"],
                            other_count=other_count,
                            week_number=snap["week_number"],
                        ),
                        "color": WORKLOAD_DENSITY_COLORS[WorkloadAnalysis.STATUS_RED],
                    }
                )

    alerts.sort(key=lambda item: (item["week_start_date"], item["type"]))
    return alerts


def _serialize_snapshot(snapshot):
    return {
        "week_start_date": snapshot["week_start_date"],
        "week_number": snapshot["week_number"],
        "year": snapshot["year"],
        "status": snapshot["week_status"],
        "density_color": WORKLOAD_DENSITY_COLORS[snapshot["week_status"]],
        "utilization_ratio": float(snapshot["utilization_ratio"]),
        "utilization_percent": round(float(snapshot["utilization_ratio"]) * 100, 1),
        "total_class_hours": float(snapshot["total_class_hours"]),
        "total_work_hours": float(snapshot["total_work_hours"]),
        "total_assignment_hours": float(snapshot["total_assignment_hours"]),
        "available_study_hours": float(snapshot["available_study_hours"]),
        "assignment_count": snapshot["assignment_count"],
        "major_assignment_count": snapshot["major_assignment_count"],
        "deadline_cluster_detected": snapshot["deadline_cluster_detected"],
        "is_overloaded": snapshot["is_overloaded"],
        "recommended_actions": snapshot["recommended_actions"],
    }


def recompute_and_persist_workload(user, start_day: date | None = None, weeks: int = 4):
    if weeks < 1:
        weeks = 1

    today = start_day or timezone.localdate()
    first_week_start = week_start(today)

    snapshots = []
    for week_offset in range(weeks):
        current_week_start = first_week_start + timedelta(days=week_offset * 7)
        snapshots.append(_compute_weekly_snapshot(user, current_week_start))

    _attach_recommendations(snapshots)
    alerts = _build_alerts_from_forecast(snapshots, today)

    alert_weeks = {alert["week_start_date"] for alert in alerts}
    for snapshot in snapshots:
        defaults = {
            "week_number": snapshot["week_number"],
            "year": snapshot["year"],
            "total_class_hours": snapshot["total_class_hours"],
            "total_work_hours": snapshot["total_work_hours"],
            "total_assignment_hours": snapshot["total_assignment_hours"],
            "available_study_hours": snapshot["available_study_hours"],
            "utilization_ratio": snapshot["utilization_ratio"],
            "week_status": snapshot["week_status"],
            "assignment_count": snapshot["assignment_count"],
            "major_assignment_count": snapshot["major_assignment_count"],
            "deadline_cluster_detected": snapshot["deadline_cluster_detected"],
            "is_overloaded": snapshot["is_overloaded"],
            "recommended_actions": snapshot["recommended_actions"],
        }

        analysis, _ = WorkloadAnalysis.objects.update_or_create(
            user=user,
            week_start_date=snapshot["week_start_date"],
            defaults=defaults,
        )

        if snapshot["week_start_date"] in alert_weeks and not analysis.alert_sent:
            analysis.alert_sent = True
            analysis.alert_sent_at = timezone.now()
            analysis.save(update_fields=["alert_sent", "alert_sent_at", "updated_at"])

    forecast = [_serialize_snapshot(snapshot) for snapshot in snapshots]
    current_summary = forecast[0] if forecast else {}

    return {
        "summary": current_summary,
        "forecast": forecast,
        "alerts": alerts,
    }


def recompute_all_users_workload(start_day: date | None = None, weeks: int = 4):
    user_model = get_user_model()
    processed = 0
    for user in user_model.objects.filter(is_active=True).iterator():
        recompute_and_persist_workload(user, start_day=start_day, weeks=weeks)
        processed += 1
    return processed
