from dataclasses import dataclass
from datetime import datetime, time as dt_time, timedelta
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from accounts.models import Assignment, AssignmentSubtask, Profile, TimeBlock
from core.models import PersonalEvent, WorkShift


DEFAULT_BLOCK_DURATION = timedelta(hours=1)


@dataclass(frozen=True)
class ScheduledItem:
    kind: str
    kind_key: str
    object_id: int | None
    title: str
    start: datetime
    end: datetime
    local_ref: str | None = None


@dataclass(frozen=True)
class ScheduleConflict:
    requested_item: ScheduledItem
    conflicting_item: ScheduledItem
    suggestion_item: ScheduledItem | None
    message: str

    @property
    def replaceable(self):
        return self.conflicting_item.object_id is not None and self.conflicting_item.local_ref is None


def scheduled_item_to_dict(item):
    if item is None:
        return None
    return {
        "kind": item.kind,
        "kind_key": item.kind_key,
        "id": item.object_id,
        "title": item.title,
        "start": item.start.isoformat(),
        "end": item.end.isoformat(),
        "local_ref": item.local_ref,
    }


def schedule_conflict_to_dict(conflict):
    return {
        "message": conflict.message,
        "conflict": {
            **scheduled_item_to_dict(conflict.conflicting_item),
            "replaceable": conflict.replaceable,
        },
        "requested": scheduled_item_to_dict(conflict.requested_item),
        "suggestion": scheduled_item_to_dict(conflict.suggestion_item),
    }


def _to_aware(dt_value):
    if dt_value is None:
        return None
    if timezone.is_naive(dt_value):
        return timezone.make_aware(dt_value, timezone.get_current_timezone())
    return dt_value


def _duration_from_hours(raw_hours):
    if raw_hours in (None, ""):
        return DEFAULT_BLOCK_DURATION

    try:
        hours_value = Decimal(str(raw_hours))
    except (InvalidOperation, TypeError, ValueError):
        return DEFAULT_BLOCK_DURATION

    if hours_value <= 0:
        return DEFAULT_BLOCK_DURATION
    return timedelta(seconds=float(hours_value) * 3600)


def combine_local_date_time(date_value, time_value):
    if not date_value or not time_value:
        return None
    return timezone.make_aware(
        datetime.combine(date_value, time_value),
        timezone.get_current_timezone(),
    )


def _normalize_kind_key(kind):
    return str(kind or "item").strip().lower().replace(" ", "_")


def build_scheduled_item(kind, title, start, *, end=None, duration_hours=None, object_id=None, kind_key=None, local_ref=None):
    if not start:
        return None

    start_value = _to_aware(start)
    end_value = _to_aware(end) if end else start_value + _duration_from_hours(duration_hours)
    if end_value <= start_value:
        raise ValueError("End time must be after the start time.")

    return ScheduledItem(
        kind=kind,
        kind_key=kind_key or _normalize_kind_key(kind),
        object_id=object_id,
        title=(title or "Untitled").strip() or "Untitled",
        start=start_value,
        end=end_value,
        local_ref=local_ref,
    )


def _ref(kind, object_id):
    return (kind, object_id)


def _iter_existing_items(user, exclude_refs=None):
    exclude_refs = exclude_refs or set()

    for assignment in Assignment.objects.filter(user=user).select_related("course"):
        if _ref("assignment", assignment.id) in exclude_refs:
            continue
        item = build_scheduled_item(
            "assignment",
            assignment.title,
            assignment.due_date,
            duration_hours=assignment.estimated_hours,
            object_id=assignment.id,
            kind_key="assignment",
        )
        if item:
            yield item

    for subtask in AssignmentSubtask.objects.filter(assignment__user=user).select_related("assignment"):
        if _ref("subtask", subtask.id) in exclude_refs:
            continue
        item = build_scheduled_item(
            "subtask",
            subtask.title,
            subtask.due_date,
            duration_hours=subtask.estimated_hours,
            object_id=subtask.id,
            kind_key="subtask",
        )
        if item:
            yield item

    for event in PersonalEvent.objects.filter(user=user):
        if _ref("personal_event", event.id) in exclude_refs:
            continue
        start = combine_local_date_time(event.event_date, event.start_time)
        item = build_scheduled_item(
            "personal event",
            event.title,
            start,
            end=combine_local_date_time(event.event_date, event.end_time),
            object_id=event.id,
            kind_key="personal_event",
        )
        if item:
            yield item

    for shift in WorkShift.objects.filter(user=user):
        if _ref("work_shift", shift.id) in exclude_refs:
            continue
        item = build_scheduled_item(
            "work shift",
            shift.employer_name or shift.job_title or "Work Shift",
            shift.shift_start,
            end=shift.shift_end,
            object_id=shift.id,
            kind_key="work_shift",
        )
        if item:
            yield item

    for block in TimeBlock.objects.filter(user=user):
        if _ref("time_block", block.id) in exclude_refs:
            continue
        item = build_scheduled_item(
            "time block",
            block.title,
            block.start_time,
            end=block.end_time,
            object_id=block.id,
            kind_key="time_block",
        )
        if item:
            yield item


def _items_overlap(left, right):
    return left.start < right.end and left.end > right.start


def _format_item(item):
    return f'{item.kind.title()} "{item.title}"'


def _round_up_datetime(dt_value, step_minutes=30):
    dt_value = _to_aware(dt_value)
    minute_remainder = dt_value.minute % step_minutes
    if minute_remainder == 0 and dt_value.second == 0 and dt_value.microsecond == 0:
        return dt_value
    delta = step_minutes - minute_remainder if minute_remainder else step_minutes
    return dt_value.replace(second=0, microsecond=0) + timedelta(minutes=delta)


def _find_suggested_slot(requested_item, occupied_items, *, start_from=None, horizon_days=14, step_minutes=30):
    duration = requested_item.end - requested_item.start
    search_start = _round_up_datetime(start_from or requested_item.start, step_minutes=step_minutes)
    search_end = search_start + timedelta(days=horizon_days)

    candidate_start = search_start
    while candidate_start < search_end:
        candidate_end = candidate_start + duration
        candidate = ScheduledItem(
            kind=requested_item.kind,
            kind_key=requested_item.kind_key,
            object_id=requested_item.object_id,
            title=requested_item.title,
            start=candidate_start,
            end=candidate_end,
            local_ref=requested_item.local_ref,
        )
        if not any(_items_overlap(candidate, occupied) for occupied in occupied_items):
            return candidate
        candidate_start += timedelta(minutes=step_minutes)

    return None


def _duration_from_time_window(start_time, end_time):
    start_dt = datetime.combine(datetime.today().date(), start_time)
    end_dt = datetime.combine(datetime.today().date(), end_time)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    return end_dt - start_dt


def _build_preference_blocks(user, range_start, range_end):
    profile = Profile.objects.filter(user=user).only(
        "sleep_hours_per_night",
        "sleep_start_time",
        "sleep_end_time",
        "personal_time_hours_per_week",
        "family_time_hours_per_week",
        "commute_time_hours_per_week",
    ).first()
    if not profile:
        return []

    blocks = []
    day_cursor = (range_start - timedelta(days=1)).date()
    day_limit = (range_end + timedelta(days=1)).date()

    sleep_start = profile.sleep_start_time or dt_time(23, 0)
    if profile.sleep_end_time:
        sleep_duration = _duration_from_time_window(sleep_start, profile.sleep_end_time)
    else:
        sleep_hours = profile.sleep_hours_per_night if profile.sleep_hours_per_night is not None else Decimal("7.0")
        sleep_duration = timedelta(hours=float(sleep_hours)) if sleep_hours > 0 else timedelta(0)

    personal_hours = profile.personal_time_hours_per_week or Decimal("0.0")
    family_hours = profile.family_time_hours_per_week or Decimal("0.0")
    commute_hours = profile.commute_time_hours_per_week or Decimal("0.0")
    reserved_daily_hours = (Decimal(str(personal_hours)) + Decimal(str(family_hours)) + Decimal(str(commute_hours))) / Decimal("7.0")

    if reserved_daily_hours > Decimal("16.0"):
        reserved_daily_hours = Decimal("16.0")

    while day_cursor <= day_limit:
        if sleep_duration > timedelta(0):
            sleep_start_dt = timezone.make_aware(datetime.combine(day_cursor, sleep_start), timezone.get_current_timezone())
            sleep_end_dt = sleep_start_dt + sleep_duration
            blocks.append(
                ScheduledItem(
                    kind="sleep",
                    kind_key="sleep",
                    object_id=None,
                    title="Sleep",
                    start=sleep_start_dt,
                    end=sleep_end_dt,
                    local_ref="profile:sleep",
                )
            )

        if reserved_daily_hours > 0:
            reserved_start_dt = timezone.make_aware(datetime.combine(day_cursor, dt_time(18, 0)), timezone.get_current_timezone())
            reserved_end_dt = reserved_start_dt + _duration_from_hours(reserved_daily_hours)
            blocks.append(
                ScheduledItem(
                    kind="reserved time",
                    kind_key="reserved_time",
                    object_id=None,
                    title="Family/Personal/Commute Time",
                    start=reserved_start_dt,
                    end=reserved_end_dt,
                    local_ref="profile:reserved",
                )
            )

        day_cursor += timedelta(days=1)

    return blocks


def get_schedule_conflict(user, items, *, exclude_refs=None):
    candidates = [item for item in items if item is not None]
    existing_items = list(_iter_existing_items(user, exclude_refs=exclude_refs))

    if candidates:
        earliest_start = min(candidate.start for candidate in candidates)
        latest_end = max(candidate.end for candidate in candidates)
        preference_blocks = _build_preference_blocks(user, earliest_start, latest_end + timedelta(days=14))
    else:
        preference_blocks = []

    for index, item in enumerate(candidates):
        for existing in existing_items:
            if _items_overlap(item, existing):
                suggestion = _find_suggested_slot(
                    item,
                    existing_items + [other for other in candidates if other is not item] + preference_blocks,
                    start_from=existing.end,
                )
                return ScheduleConflict(
                    requested_item=item,
                    conflicting_item=existing,
                    suggestion_item=suggestion,
                    message=f'{_format_item(item)} overlaps with existing {_format_item(existing)}. Only one item can occupy a time block.',
                )

        for other in candidates[index + 1:]:
            if _items_overlap(item, other):
                suggestion = _find_suggested_slot(
                    item,
                    existing_items + [candidate for candidate in candidates if candidate is not item] + preference_blocks,
                    start_from=other.end,
                )
                return ScheduleConflict(
                    requested_item=item,
                    conflicting_item=other,
                    suggestion_item=suggestion,
                    message=f'{_format_item(item)} overlaps with {_format_item(other)}. Only one item can occupy a time block.',
                )

    return None


def validate_schedule_items(user, items, *, exclude_refs=None):
    conflict = get_schedule_conflict(user, items, exclude_refs=exclude_refs)
    return conflict.message if conflict else None


def delete_scheduled_item(user, item):
    if item.object_id is None:
        raise ValueError("Only persisted scheduled items can be replaced.")

    if item.kind_key == "assignment":
        Assignment.objects.filter(user=user, pk=item.object_id).delete()
        return
    if item.kind_key == "subtask":
        AssignmentSubtask.objects.filter(assignment__user=user, pk=item.object_id).delete()
        return
    if item.kind_key == "personal_event":
        PersonalEvent.objects.filter(user=user, pk=item.object_id).delete()
        return
    if item.kind_key == "work_shift":
        WorkShift.objects.filter(user=user, pk=item.object_id).delete()
        return
    if item.kind_key == "time_block":
        TimeBlock.objects.filter(user=user, pk=item.object_id).delete()
        return

    raise ValueError(f"Unsupported scheduled item kind: {item.kind_key}")