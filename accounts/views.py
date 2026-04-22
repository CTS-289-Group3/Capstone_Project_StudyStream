import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_http_methods
from django.http import JsonResponse
from django.utils.dateparse import parse_date, parse_datetime
from django.utils import timezone
from django.db.models import Q

from core.scheduling import (
    build_scheduled_item,
    delete_scheduled_item,
    get_schedule_conflict,
    schedule_conflict_to_dict,
    validate_schedule_items,
)
from home.workload_engine import recompute_and_persist_workload

from .forms import ProfileForm, WorkloadPreferencesForm
from .models import Assignment, AssignmentSubtask, CLASS_COLORS, Course, Profile, Semester, Tag, TimeBlock


ALLOWED_CLASS_COLORS = {hex_value for hex_value, _ in CLASS_COLORS}


def _parse_checkbox_value(raw_value, default=False):
    if raw_value is None:
        return default
    return str(raw_value).strip().lower() in {'1', 'true', 'yes', 'on'}


def _normalize_course_color(raw_value):
    color_value = (raw_value or '').strip().upper()
    if color_value in ALLOWED_CLASS_COLORS:
        return color_value
    return '#1E90FF'


def _parse_nonnegative_decimal(raw_value, default='0.0'):
    value = (raw_value or '').strip()
    if not value:
        return Decimal(default)
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)
    return parsed if parsed >= 0 else Decimal(default)


def _parse_due_date_value(raw_value):
    """Parse request due_date input and always return a timezone-aware datetime."""
    if not raw_value:
        return None

    parsed_value = parse_datetime(raw_value)
    if parsed_value is None:
        parsed_date = parse_date(raw_value)
        if parsed_date is None:
            return None
        parsed_value = datetime.combine(parsed_date, datetime.min.time())

    if timezone.is_naive(parsed_value):
        parsed_value = timezone.make_aware(parsed_value, timezone.get_current_timezone())
    return parsed_value


def _refresh_workload(user):
    # Keep workload density snapshots current whenever assignments change.
    return recompute_and_persist_workload(user, weeks=4)


def _schedule_conflict_response(conflict):
    payload = schedule_conflict_to_dict(conflict)
    return JsonResponse(
        {
            'success': False,
            'error': payload['message'],
            'conflict': payload['conflict'],
            'requested': payload['requested'],
            'suggestion': payload['suggestion'],
        },
        status=409,
    )


def _resolve_schedule_conflict(request, user, items, *, exclude_refs=None):
    conflict = get_schedule_conflict(user, items, exclude_refs=exclude_refs)
    if not conflict:
        return None

    replace_requested = _parse_checkbox_value(request.POST.get('replace_conflict'), default=False)
    conflict_kind = request.POST.get('conflict_kind', '').strip()
    conflict_id = request.POST.get('conflict_id', '').strip()

    if (
        replace_requested
        and conflict.replaceable
        and conflict.conflicting_item.kind_key == conflict_kind
        and str(conflict.conflicting_item.object_id) == conflict_id
    ):
        delete_scheduled_item(user, conflict.conflicting_item)
        return get_schedule_conflict(user, items, exclude_refs=exclude_refs)

    return conflict


# ─────────────────────────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────────────────────────
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/home/')

    if request.method == 'GET' and request.GET.get('next'):
        messages.error(request, 'Please sign in to continue.')

    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('/home/')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully. Please sign in.')
            return redirect('/accounts/login/')
        messages.error(request, 'Please fix the errors below and try again.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('/accounts/login/')


def home(request):
    return render(request, 'accounts/home.html')


@never_cache
@login_required(login_url='/accounts/login/')
def dashboard_view(request):
    return redirect('/home/')


@never_cache
@login_required(login_url='/accounts/login/')
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if created:
        profile.display_name = request.user.username
        profile.avatar_text = request.user.username[:1].upper()
        profile.save(update_fields=['display_name', 'avatar_text'])

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('/accounts/profile/')
    else:
        form = ProfileForm(instance=profile, user=request.user)
    return render(request, 'accounts/profile.html', {'form': form, 'profile': profile})


@never_cache
@login_required(login_url='/accounts/login/')
def settings_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if created:
        profile.display_name = request.user.username
        profile.avatar_text = request.user.username[:1].upper()
        profile.save(update_fields=['display_name', 'avatar_text'])

    if request.method == 'POST':
        workload_form = WorkloadPreferencesForm(request.POST, instance=profile)
        if workload_form.is_valid():
            workload_form.save()
            recompute_and_persist_workload(request.user, weeks=4)
            messages.success(request, 'Workload preferences updated successfully.')
            return redirect('/accounts/settings/')
    else:
        workload_form = WorkloadPreferencesForm(instance=profile)

    return render(request, 'accounts/settings.html', {'profile': profile, 'workload_form': workload_form})


# ─────────────────────────────────────────────────────────────
#  SEMESTER CRUD
# ─────────────────────────────────────────────────────────────
@login_required(login_url='/accounts/login/')
def semester_create(request):
    if request.method == 'POST':
        name       = request.POST.get('name', '').strip()
        start_date = request.POST.get('start_date') or None
        end_date   = request.POST.get('end_date') or None
        is_active  = request.POST.get('is_active') == 'on'

        if not name:
            return JsonResponse({'success': False, 'error': 'Name is required.'}, status=400)

        semester = Semester.objects.create(
            user=request.user,
            name=name,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active,
        )
        return JsonResponse({
            'success': True,
            'id': semester.id,
            'name': semester.name,
            'is_active': semester.is_active,
            'start_date': str(semester.start_date) if semester.start_date else '',
            'end_date':   str(semester.end_date) if semester.end_date else '',
        })
    return JsonResponse({'success': False, 'error': 'POST required.'}, status=405)


@login_required(login_url='/accounts/login/')
def semester_edit(request, pk):
    semester = get_object_or_404(Semester, pk=pk, user=request.user)
    if request.method == 'POST':
        semester.name       = request.POST.get('name', semester.name).strip()
        semester.start_date = request.POST.get('start_date') or None
        semester.end_date   = request.POST.get('end_date') or None
        semester.is_active  = request.POST.get('is_active') == 'on'
        semester.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)


@login_required(login_url='/accounts/login/')
def semester_delete(request, pk):
    semester = get_object_or_404(Semester, pk=pk, user=request.user)
    if request.method == 'POST':
        semester.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)


@login_required(login_url='/accounts/login/')
def semester_list_json(request):
    semesters = Semester.objects.filter(user=request.user).values(
        'id', 'name', 'is_active', 'start_date', 'end_date'
    )
    return JsonResponse({'semesters': list(semesters)})


# ─────────────────────────────────────────────────────────────
#  COURSE CRUD
# ─────────────────────────────────────────────────────────────
@login_required(login_url='/accounts/login/')
def course_create(request):
    if request.method == 'POST':
        semester_id = request.POST.get('semester')
        semester = get_object_or_404(Semester, pk=semester_id, user=request.user)

        course = Course.objects.create(
            user=request.user,
            semester=semester,
            course_code=request.POST.get('course_code', '').strip(),
            course_name=request.POST.get('course_name', '').strip(),
            color_hex=_normalize_course_color(request.POST.get('color_hex')),
            professor_name=request.POST.get('professor_name', '').strip(),
            professor_email=request.POST.get('professor_email', '').strip(),
            meeting_times=request.POST.get('meeting_times', '').strip(),
            weekly_study_hours=_parse_nonnegative_decimal(request.POST.get('weekly_study_hours'), '0.0'),
            canvas_url=request.POST.get('canvas_url', '').strip(),
        )
        return JsonResponse({
            'success': True,
            'id': course.id,
            'course_code': course.course_code,
            'course_name': course.course_name,
            'color_hex': course.color_hex,
            'weekly_study_hours': float(course.weekly_study_hours),
            'semester_id': semester.id,
            'semester_name': semester.name,
        })
    return JsonResponse({'success': False}, status=405)


@login_required(login_url='/accounts/login/')
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk, user=request.user)
    if request.method == 'POST':
        semester_id = request.POST.get('semester')
        if semester_id:
            course.semester = get_object_or_404(Semester, pk=semester_id, user=request.user)
        course.course_code     = request.POST.get('course_code', course.course_code).strip()
        course.course_name     = request.POST.get('course_name', course.course_name).strip()
        course.color_hex       = _normalize_course_color(request.POST.get('color_hex', course.color_hex))
        course.professor_name  = request.POST.get('professor_name', course.professor_name).strip()
        course.professor_email = request.POST.get('professor_email', course.professor_email).strip()
        course.meeting_times   = request.POST.get('meeting_times', course.meeting_times).strip()
        course.weekly_study_hours = _parse_nonnegative_decimal(
            request.POST.get('weekly_study_hours', str(course.weekly_study_hours)),
            str(course.weekly_study_hours),
        )
        course.canvas_url      = request.POST.get('canvas_url', course.canvas_url).strip()
        course.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)


@login_required(login_url='/accounts/login/')
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk, user=request.user)
    if request.method == 'POST':
        course.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)


@login_required(login_url='/accounts/login/')
def course_list_json(request):
    courses = Course.objects.filter(user=request.user).select_related('semester').values(
        'id', 'course_code', 'course_name', 'color_hex',
        'semester__id', 'semester__name', 'professor_name', 'meeting_times', 'weekly_study_hours'
    )
    return JsonResponse({'courses': list(courses)})


# ─────────────────────────────────────────────────────────────
#  TAG CRUD
# ─────────────────────────────────────────────────────────────
@login_required(login_url='/accounts/login/')
def tag_create(request):
    if request.method == 'POST':
        name      = request.POST.get('name', '').strip()
        color_hex = request.POST.get('color_hex', '#1E90FF')
        if not name:
            return JsonResponse({'success': False, 'error': 'Name required.'}, status=400)
        tag, created = Tag.objects.get_or_create(user=request.user, name=name, defaults={'color_hex': color_hex})
        return JsonResponse({'success': True, 'id': tag.id, 'name': tag.name, 'color_hex': tag.color_hex})
    return JsonResponse({'success': False}, status=405)


@login_required(login_url='/accounts/login/')
def tag_list_json(request):
    tags = Tag.objects.filter(user=request.user).values('id', 'name', 'color_hex')
    return JsonResponse({'tags': list(tags)})


@login_required(login_url='/accounts/login/')
def tag_delete(request, pk):
    tag = get_object_or_404(Tag, pk=pk, user=request.user)
    if request.method == 'POST':
        tag.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)


# ─────────────────────────────────────────────────────────────
#  ASSIGNMENT CRUD
# ─────────────────────────────────────────────────────────────
@login_required(login_url='/accounts/login/')
def assignment_create(request):
    if request.method == 'POST':
        course_id = request.POST.get('course')
        course    = get_object_or_404(Course, pk=course_id, user=request.user)

        due_date_raw = request.POST.get('due_date', '')
        if not due_date_raw:
            return JsonResponse({'success': False, 'error': 'Due date is required.'}, status=400)

        due_date = _parse_due_date_value(due_date_raw)
        if due_date is None:
            return JsonResponse({'success': False, 'error': 'Invalid due date format.'}, status=400)

        items_to_validate = [
            build_scheduled_item(
                'assignment',
                request.POST.get('title', '').strip(),
                due_date,
                duration_hours=request.POST.get('estimated_hours') or None,
                local_ref='assignment',
            )
        ]

        subtask_titles = request.POST.getlist('subtask_title[]')
        subtask_due_dates = request.POST.getlist('subtask_due_date[]')
        subtask_estimated_hours = request.POST.getlist('subtask_estimated_hours[]')
        for i, st in enumerate(subtask_titles):
            st = st.strip()
            if not st:
                continue
            raw_subtask_due_date = subtask_due_dates[i].strip() if i < len(subtask_due_dates) else ''
            if not raw_subtask_due_date:
                continue
            parsed_subtask_due_date = _parse_due_date_value(raw_subtask_due_date)
            if parsed_subtask_due_date is None:
                return JsonResponse({'success': False, 'error': 'Invalid subtask due date format.'}, status=400)
            raw_estimated = subtask_estimated_hours[i].strip() if i < len(subtask_estimated_hours) else ''
            items_to_validate.append(
                build_scheduled_item(
                    'subtask',
                    st,
                    parsed_subtask_due_date,
                    duration_hours=raw_estimated or None,
                    local_ref=f'subtask:{i}',
                )
            )

        conflict = _resolve_schedule_conflict(request, request.user, items_to_validate)
        if conflict:
            return _schedule_conflict_response(conflict)

        assignment = Assignment.objects.create(
            user=request.user,
            course=course,
            title=request.POST.get('title', '').strip(),
            description=request.POST.get('description', '').strip(),
            assignment_type=request.POST.get('assignment_type', 'other'),
            due_date=due_date,
            due_time=request.POST.get('due_time', '').strip(),
            estimated_hours=request.POST.get('estimated_hours') or None,
            status=request.POST.get('status', 'not_started'),
            priority_level=request.POST.get('priority_level') or request.POST.get('priority', 'medium'),
            is_major_project=_parse_checkbox_value(
                request.POST.get('is_major_project', request.POST.get('is_major')),
                default=False,
            ),
            canvas_link=request.POST.get('canvas_link', '').strip(),
            rubric_link=request.POST.get('rubric_link', '').strip(),
            submission_link=request.POST.get('submission_link', '').strip(),
            contributes_to_workload=_parse_checkbox_value(
                request.POST.get('contributes_to_workload'),
                default=True,
            ),
        )

        # Tags
        tag_ids = request.POST.getlist('tags')
        if tag_ids:
            valid_tags = Tag.objects.filter(pk__in=tag_ids, user=request.user)
            assignment.tags.set(valid_tags)

        # Subtasks
        subtask_due_times = request.POST.getlist('subtask_due_time[]')
        for i, st in enumerate(subtask_titles):
            st = st.strip()
            if st:
                raw_due_date = subtask_due_dates[i].strip() if i < len(subtask_due_dates) else ''
                due_date = _parse_due_date_value(raw_due_date) if raw_due_date else None
                due_time = subtask_due_times[i].strip() if i < len(subtask_due_times) else ''
                raw_estimated = subtask_estimated_hours[i].strip() if i < len(subtask_estimated_hours) else ''
                AssignmentSubtask.objects.create(
                    assignment=assignment,
                    title=st,
                    step_order=i,
                    due_date=due_date,
                    due_time=due_time,
                    estimated_hours=raw_estimated or None,
                )

        _refresh_workload(request.user)

        return JsonResponse({
            'success': True,
            'id': assignment.id,
            'assignment_id': str(assignment.assignment_id),
            'title': assignment.title,
            'course_code': course.course_code,
            'course_color': course.color_hex,
            'due_date': str(assignment.due_date),
            'status': assignment.status,
            'priority': assignment.priority_level,
            'priority_level': assignment.priority_level,
            'is_major': assignment.is_major_project,
            'is_major_project': assignment.is_major_project,
            'completion_pct': assignment.completion_percentage,
            'completion_percentage': assignment.completion_percentage,
        })
    return JsonResponse({'success': False}, status=405)


@login_required(login_url='/accounts/login/')
def assignment_edit(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, user=request.user)
    if request.method == 'POST':
        course_id = request.POST.get('course')
        if course_id:
            assignment.course = get_object_or_404(Course, pk=course_id, user=request.user)
        new_title = request.POST.get('title', assignment.title).strip()
        new_description = request.POST.get('description', assignment.description).strip()
        new_assignment_type = request.POST.get('assignment_type', assignment.assignment_type)
        due_date_raw               = request.POST.get('due_date')
        new_due_date = assignment.due_date
        if due_date_raw:
            due_date = _parse_due_date_value(due_date_raw)
            if due_date is None:
                return JsonResponse({'success': False, 'error': 'Invalid due date format.'}, status=400)
            new_due_date = due_date
        new_due_time = request.POST.get('due_time', assignment.due_time).strip()
        new_estimated_hours = request.POST.get('estimated_hours') or None
        new_status = request.POST.get('status', assignment.status)
        new_priority_level = request.POST.get('priority_level') or request.POST.get('priority', assignment.priority_level)
        new_is_major_project = _parse_checkbox_value(
            request.POST.get('is_major_project', request.POST.get('is_major')),
            default=assignment.is_major_project,
        )
        new_canvas_link = request.POST.get('canvas_link', assignment.canvas_link).strip()
        new_rubric_link = request.POST.get('rubric_link', assignment.rubric_link).strip()
        new_submission_link = request.POST.get('submission_link', assignment.submission_link).strip()
        new_contributes_to_workload = _parse_checkbox_value(
            request.POST.get('contributes_to_workload'),
            default=assignment.contributes_to_workload,
        )

        subtask_titles = request.POST.getlist('subtask_title[]')
        subtask_due_dates = request.POST.getlist('subtask_due_date[]')
        subtask_estimated_hours = request.POST.getlist('subtask_estimated_hours[]')

        items_to_validate = [
            build_scheduled_item(
                'assignment',
                new_title,
                new_due_date,
                duration_hours=new_estimated_hours,
                object_id=assignment.id,
                local_ref='assignment',
            )
        ]
        for i, st in enumerate(subtask_titles):
            st = st.strip()
            if not st:
                continue
            raw_subtask_due_date = subtask_due_dates[i].strip() if i < len(subtask_due_dates) else ''
            if not raw_subtask_due_date:
                continue
            parsed_subtask_due_date = _parse_due_date_value(raw_subtask_due_date)
            if parsed_subtask_due_date is None:
                return JsonResponse({'success': False, 'error': 'Invalid subtask due date format.'}, status=400)
            raw_estimated = subtask_estimated_hours[i].strip() if i < len(subtask_estimated_hours) else ''
            items_to_validate.append(
                build_scheduled_item(
                    'subtask',
                    st,
                    parsed_subtask_due_date,
                    duration_hours=raw_estimated or None,
                    local_ref=f'subtask:{i}',
                )
            )

        exclude_refs = {('assignment', assignment.id)}
        exclude_refs.update(('subtask', subtask.id) for subtask in assignment.subtasks.all())
        conflict = _resolve_schedule_conflict(request, request.user, items_to_validate, exclude_refs=exclude_refs)
        if conflict:
            return _schedule_conflict_response(conflict)

        assignment.title = new_title
        assignment.description = new_description
        assignment.assignment_type = new_assignment_type
        assignment.due_date = new_due_date
        assignment.due_time = new_due_time
        assignment.estimated_hours = new_estimated_hours
        assignment.status = new_status
        assignment.priority_level = new_priority_level
        assignment.is_major_project = new_is_major_project
        assignment.canvas_link = new_canvas_link
        assignment.rubric_link = new_rubric_link
        assignment.submission_link = new_submission_link
        assignment.contributes_to_workload = new_contributes_to_workload
        assignment.save()

        tag_ids = request.POST.getlist('tags')
        valid_tags = Tag.objects.filter(pk__in=tag_ids, user=request.user)
        assignment.tags.set(valid_tags)

        # Subtasks (replace existing ordering/content from modal payload)
        subtask_due_times = request.POST.getlist('subtask_due_time[]')
        assignment.subtasks.all().delete()
        for i, st in enumerate(subtask_titles):
            st = st.strip()
            if st:
                raw_due_date = subtask_due_dates[i].strip() if i < len(subtask_due_dates) else ''
                due_date = _parse_due_date_value(raw_due_date) if raw_due_date else None
                due_time = subtask_due_times[i].strip() if i < len(subtask_due_times) else ''
                raw_estimated = subtask_estimated_hours[i].strip() if i < len(subtask_estimated_hours) else ''
                AssignmentSubtask.objects.create(
                    assignment=assignment,
                    title=st,
                    step_order=i,
                    due_date=due_date,
                    due_time=due_time,
                    estimated_hours=raw_estimated or None,
                )

        _refresh_workload(request.user)

        return JsonResponse({'success': True})
    # GET — return data for edit form
    tags = list(assignment.tags.values('id', 'name', 'color_hex'))
    subtasks = []
    for st in assignment.subtasks.all().order_by('step_order'):
        subtasks.append({
            'id': st.id,
            'subtask_id': str(st.subtask_id),
            'title': st.title,
            'description': st.description,
            'status': st.status,
            'step_order': st.step_order,
            'sequence_order': st.step_order,
            'course_color': assignment.course.color_hex,
            'due_date': st.due_date.strftime('%Y-%m-%dT%H:%M') if st.due_date else '',
            'due_time': st.due_time,
            'estimated_hours': str(st.estimated_hours) if st.estimated_hours else '',
            'completion_percentage': st.completion_percentage,
            'started_at': st.started_at.isoformat() if st.started_at else None,
            'completed_at': st.completed_at.isoformat() if st.completed_at else None,
        })
    return JsonResponse({
        'id': assignment.id,
        'assignment_id': str(assignment.assignment_id),
        'title': assignment.title,
        'description': assignment.description,
        'assignment_type': assignment.assignment_type,
        'due_date': assignment.due_date.strftime('%Y-%m-%dT%H:%M') if assignment.due_date else '',
        'due_time': assignment.due_time,
        'estimated_hours': str(assignment.estimated_hours) if assignment.estimated_hours else '',
        'status': assignment.status,
        'priority': assignment.priority_level,
        'priority_level': assignment.priority_level,
        'is_major': assignment.is_major_project,
        'is_major_project': assignment.is_major_project,
        'completion_pct': assignment.completion_percentage,
        'completion_percentage': assignment.completion_percentage,
        'canvas_link': assignment.canvas_link,
        'rubric_link': assignment.rubric_link,
        'submission_link': assignment.submission_link,
        'contributes_to_workload': assignment.contributes_to_workload,
        'course_id': assignment.course_id,
        'tags': tags,
        'subtasks': subtasks,
    })


@login_required(login_url='/accounts/login/')
def assignment_delete(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, user=request.user)
    if request.method == 'POST':
        assignment.delete()
        _refresh_workload(request.user)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)


@login_required(login_url='/accounts/login/')
def assignment_status_update(request, pk):
    """Quick status toggle (AJAX)."""
    assignment = get_object_or_404(Assignment, pk=pk, user=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('status', 'complete')
        assignment.status = new_status
        if new_status == 'complete':
            assignment.completion_percentage = 100
            assignment.completed_at   = timezone.now()
        assignment.save()
        _refresh_workload(request.user)
        return JsonResponse({
            'success': True,
            'status': assignment.status,
            'completion_pct': assignment.completion_percentage,
            'completion_percentage': assignment.completion_percentage,
        })
    return JsonResponse({'success': False}, status=405)


@login_required(login_url='/accounts/login/')
def assignment_list_json(request):
    qs = Assignment.objects.filter(user=request.user).select_related('course').prefetch_related('tags', 'subtasks')
    data = []
    for a in qs:
        subtasks = []
        for st in a.subtasks.all().order_by('step_order'):
            subtasks.append({
                'id': st.id,
                'subtask_id': str(st.subtask_id),
                'title': st.title,
                'description': st.description,
                'status': st.status,
                'step_order': st.step_order,
                'sequence_order': st.step_order,
                'course_color': a.course.color_hex,
                'due_date': st.due_date.isoformat() if st.due_date else None,
                'due_time': st.due_time,
                'estimated_hours': float(st.estimated_hours) if st.estimated_hours is not None else None,
                'completion_percentage': st.completion_percentage,
                'started_at': st.started_at.isoformat() if st.started_at else None,
                'completed_at': st.completed_at.isoformat() if st.completed_at else None,
            })
        data.append({
            'id': a.id,
            'assignment_id': str(a.assignment_id),
            'title': a.title,
            'description': a.description,
            'course_id': a.course_id,
            'course_code': a.course.course_code,
            'course_color': a.course.color_hex,
            'due_date': a.due_date.isoformat(),
            'due_time': a.due_time,
            'estimated_hours': float(a.estimated_hours) if a.estimated_hours is not None else None,
            'status': a.status,
            'priority': a.priority_level,
            'priority_level': a.priority_level,
            'completion_pct': a.completion_percentage,
            'completion_percentage': a.completion_percentage,
            'is_major': a.is_major_project,
            'is_major_project': a.is_major_project,
            'assignment_type': a.assignment_type,
            'canvas_link': a.canvas_link,
            'rubric_link': a.rubric_link,
            'submission_link': a.submission_link,
            'contributes_to_workload': a.contributes_to_workload,
            'subtask_count': a.subtasks.count(),
            'subtask_done': a.subtasks.filter(status='complete').count(),
            'subtasks': subtasks,
            'tags': [{'id': t.id, 'name': t.name, 'color_hex': t.color_hex} for t in a.tags.all()],
        })
    return JsonResponse({'assignments': data})


# ─────────────────────────────────────────────────────────────
#  SUBTASK CRUD
# ─────────────────────────────────────────────────────────────
@login_required(login_url='/accounts/login/')
def subtask_create(request, assignment_pk):
    assignment = get_object_or_404(Assignment, pk=assignment_pk, user=request.user)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            return JsonResponse({'success': False, 'error': 'Title required.'}, status=400)
        parsed_due_date = _parse_due_date_value(request.POST.get('due_date')) if request.POST.get('due_date') else None
        conflict_error = validate_schedule_items(
            request.user,
            [
                build_scheduled_item(
                    'subtask',
                    title,
                    parsed_due_date,
                    duration_hours=request.POST.get('estimated_hours') or None,
                    local_ref='subtask',
                )
            ],
        )
        if conflict_error:
            conflict = get_schedule_conflict(
                request.user,
                [
                    build_scheduled_item(
                        'subtask',
                        title,
                        parsed_due_date,
                        duration_hours=request.POST.get('estimated_hours') or None,
                        local_ref='subtask',
                    )
                ],
            )
            return _schedule_conflict_response(conflict)
        order = assignment.subtasks.count()
        subtask = AssignmentSubtask.objects.create(
            assignment=assignment,
            title=title,
            description=request.POST.get('description', '').strip(),
            step_order=order,
            due_date=parsed_due_date,
            due_time=request.POST.get('due_time', '').strip(),
            estimated_hours=request.POST.get('estimated_hours') or None,
        )
        return JsonResponse({
            'success': True,
            'id': subtask.id,
            'subtask_id': str(subtask.subtask_id),
            'title': subtask.title,
            'status': subtask.status,
            'step_order': subtask.step_order,
            'sequence_order': subtask.step_order,
            'course_color': assignment.course.color_hex,
            'completion_percentage': subtask.completion_percentage,
        })
    return JsonResponse({'success': False}, status=405)


@login_required(login_url='/accounts/login/')
def subtask_edit(request, pk):
    subtask = get_object_or_404(AssignmentSubtask, pk=pk)
    if subtask.assignment.user != request.user:
        return JsonResponse({'success': False}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)

    title = request.POST.get('title', subtask.title).strip()
    if not title:
        return JsonResponse({'success': False, 'error': 'Title required.'}, status=400)

    raw_due_date = request.POST.get('due_date', '')
    due_date = _parse_due_date_value(raw_due_date) if raw_due_date else None

    conflict_error = validate_schedule_items(
        request.user,
        [
            build_scheduled_item(
                'subtask',
                title,
                due_date,
                duration_hours=request.POST.get('estimated_hours') or None,
                object_id=subtask.id,
                local_ref='subtask',
            )
        ],
        exclude_refs={('subtask', subtask.id)},
    )
    if conflict_error:
        conflict = get_schedule_conflict(
            request.user,
            [
                build_scheduled_item(
                    'subtask',
                    title,
                    due_date,
                    duration_hours=request.POST.get('estimated_hours') or None,
                    object_id=subtask.id,
                    local_ref='subtask',
                )
            ],
            exclude_refs={('subtask', subtask.id)},
        )
        return _schedule_conflict_response(conflict)

    subtask.title = title
    subtask.description = request.POST.get('description', subtask.description).strip()
    subtask.due_date = due_date
    subtask.due_time = request.POST.get('due_time', subtask.due_time).strip()
    subtask.estimated_hours = request.POST.get('estimated_hours') or None
    subtask.save()

    return JsonResponse({
        'success': True,
        'id': subtask.id,
        'subtask_id': str(subtask.subtask_id),
        'title': subtask.title,
        'description': subtask.description,
        'status': subtask.status,
        'step_order': subtask.step_order,
        'sequence_order': subtask.step_order,
        'course_color': subtask.assignment.course.color_hex,
        'due_date': subtask.due_date.isoformat() if subtask.due_date else None,
        'due_time': subtask.due_time,
        'estimated_hours': float(subtask.estimated_hours) if subtask.estimated_hours is not None else None,
        'completion_percentage': subtask.completion_percentage,
    })


@login_required(login_url='/accounts/login/')
def subtask_toggle(request, pk):
    subtask = get_object_or_404(AssignmentSubtask, pk=pk)
    # Check ownership via assignment
    if subtask.assignment.user != request.user:
        return JsonResponse({'success': False}, status=403)
    if request.method == 'POST':
        subtask.status = 'complete' if subtask.status != 'complete' else 'not_started'
        if subtask.status == 'complete':
            subtask.completed_at = timezone.now()
            if not subtask.started_at:
                subtask.started_at = timezone.now()
        else:
            subtask.completed_at = None
        subtask.save()
        return JsonResponse({
            'success': True,
            'status': subtask.status,
            'subtask_completion_percentage': subtask.completion_percentage,
            'completion_pct': subtask.assignment.completion_percentage,
            'completion_percentage': subtask.assignment.completion_percentage,
        })
    return JsonResponse({'success': False}, status=405)


@login_required(login_url='/accounts/login/')
def subtask_delete(request, pk):
    subtask = get_object_or_404(AssignmentSubtask, pk=pk)
    if subtask.assignment.user != request.user:
        return JsonResponse({'success': False}, status=403)
    if request.method == 'POST':
        subtask.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)


@login_required(login_url='/accounts/login/')
def subtask_list_json(request, assignment_pk):
    assignment = get_object_or_404(Assignment, pk=assignment_pk, user=request.user)
    subtasks = []
    for st in assignment.subtasks.all().order_by('step_order'):
        subtasks.append({
            'id': st.id,
            'subtask_id': str(st.subtask_id),
            'title': st.title,
            'description': st.description,
            'status': st.status,
            'step_order': st.step_order,
            'sequence_order': st.step_order,
            'course_color': assignment.course.color_hex,
            'due_date': st.due_date.isoformat() if st.due_date else None,
            'due_time': st.due_time,
            'estimated_hours': float(st.estimated_hours) if st.estimated_hours is not None else None,
            'completion_percentage': st.completion_percentage,
            'started_at': st.started_at.isoformat() if st.started_at else None,
            'completed_at': st.completed_at.isoformat() if st.completed_at else None,
        })
    return JsonResponse({
        'subtasks': subtasks,
        'completion_pct': assignment.completion_percentage,
        'completion_percentage': assignment.completion_percentage,
    })