import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_http_methods
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q

from .models import Semester, Course, Assignment, AssignmentSubtask, Tag, TimeBlock


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
            color_hex=request.POST.get('color_hex', '#3b82f6'),
            professor_name=request.POST.get('professor_name', '').strip(),
            professor_email=request.POST.get('professor_email', '').strip(),
            meeting_times=request.POST.get('meeting_times', '').strip(),
            canvas_url=request.POST.get('canvas_url', '').strip(),
        )
        return JsonResponse({
            'success': True,
            'id': course.id,
            'course_code': course.course_code,
            'course_name': course.course_name,
            'color_hex': course.color_hex,
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
        course.color_hex       = request.POST.get('color_hex', course.color_hex)
        course.professor_name  = request.POST.get('professor_name', course.professor_name).strip()
        course.professor_email = request.POST.get('professor_email', course.professor_email).strip()
        course.meeting_times   = request.POST.get('meeting_times', course.meeting_times).strip()
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
        'semester__id', 'semester__name', 'professor_name', 'meeting_times'
    )
    return JsonResponse({'courses': list(courses)})


# ─────────────────────────────────────────────────────────────
#  TAG CRUD
# ─────────────────────────────────────────────────────────────
@login_required(login_url='/accounts/login/')
def tag_create(request):
    if request.method == 'POST':
        name      = request.POST.get('name', '').strip()
        color_hex = request.POST.get('color_hex', '#3b82f6')
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

        assignment = Assignment.objects.create(
            user=request.user,
            course=course,
            title=request.POST.get('title', '').strip(),
            description=request.POST.get('description', '').strip(),
            assignment_type=request.POST.get('assignment_type', 'other'),
            due_date=due_date_raw,
            estimated_hours=request.POST.get('estimated_hours') or None,
            status=request.POST.get('status', 'not_started'),
            priority=request.POST.get('priority', 'medium'),
            is_major=request.POST.get('is_major') == 'on',
            canvas_link=request.POST.get('canvas_link', '').strip(),
        )

        # Tags
        tag_ids = request.POST.getlist('tags')
        if tag_ids:
            valid_tags = Tag.objects.filter(pk__in=tag_ids, user=request.user)
            assignment.tags.set(valid_tags)

        # Subtasks
        subtask_titles = request.POST.getlist('subtask_title[]')
        for i, st in enumerate(subtask_titles):
            st = st.strip()
            if st:
                AssignmentSubtask.objects.create(
                    assignment=assignment,
                    title=st,
                    sequence_order=i,
                )

        return JsonResponse({
            'success': True,
            'id': assignment.id,
            'title': assignment.title,
            'course_code': course.course_code,
            'course_color': course.color_hex,
            'due_date': str(assignment.due_date),
            'status': assignment.status,
            'priority': assignment.priority,
        })
    return JsonResponse({'success': False}, status=405)


@login_required(login_url='/accounts/login/')
def assignment_edit(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, user=request.user)
    if request.method == 'POST':
        course_id = request.POST.get('course')
        if course_id:
            assignment.course = get_object_or_404(Course, pk=course_id, user=request.user)
        assignment.title           = request.POST.get('title', assignment.title).strip()
        assignment.description     = request.POST.get('description', assignment.description).strip()
        assignment.assignment_type = request.POST.get('assignment_type', assignment.assignment_type)
        due_date_raw               = request.POST.get('due_date')
        if due_date_raw:
            assignment.due_date = due_date_raw
        assignment.estimated_hours = request.POST.get('estimated_hours') or None
        assignment.status          = request.POST.get('status', assignment.status)
        assignment.priority        = request.POST.get('priority', assignment.priority)
        assignment.is_major        = request.POST.get('is_major') == 'on'
        assignment.canvas_link     = request.POST.get('canvas_link', assignment.canvas_link).strip()
        assignment.save()

        tag_ids = request.POST.getlist('tags')
        valid_tags = Tag.objects.filter(pk__in=tag_ids, user=request.user)
        assignment.tags.set(valid_tags)

        return JsonResponse({'success': True})
    # GET — return data for edit form
    tags = list(assignment.tags.values('id', 'name', 'color_hex'))
    subtasks = list(assignment.subtasks.values('id', 'title', 'status', 'sequence_order'))
    return JsonResponse({
        'id': assignment.id,
        'title': assignment.title,
        'description': assignment.description,
        'assignment_type': assignment.assignment_type,
        'due_date': assignment.due_date.strftime('%Y-%m-%dT%H:%M') if assignment.due_date else '',
        'estimated_hours': str(assignment.estimated_hours) if assignment.estimated_hours else '',
        'status': assignment.status,
        'priority': assignment.priority,
        'is_major': assignment.is_major,
        'canvas_link': assignment.canvas_link,
        'course_id': assignment.course_id,
        'tags': tags,
        'subtasks': subtasks,
    })


@login_required(login_url='/accounts/login/')
def assignment_delete(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, user=request.user)
    if request.method == 'POST':
        assignment.delete()
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
            assignment.completion_pct = 100
            assignment.completed_at   = timezone.now()
        assignment.save()
        return JsonResponse({'success': True, 'status': assignment.status, 'completion_pct': assignment.completion_pct})
    return JsonResponse({'success': False}, status=405)


@login_required(login_url='/accounts/login/')
def assignment_list_json(request):
    qs = Assignment.objects.filter(user=request.user).select_related('course').prefetch_related('tags', 'subtasks')
    data = []
    for a in qs:
        data.append({
            'id': a.id,
            'title': a.title,
            'course_id': a.course_id,
            'course_code': a.course.course_code,
            'course_color': a.course.color_hex,
            'due_date': a.due_date.isoformat(),
            'status': a.status,
            'priority': a.priority,
            'completion_pct': a.completion_pct,
            'is_major': a.is_major,
            'assignment_type': a.assignment_type,
            'subtask_count': a.subtasks.count(),
            'subtask_done': a.subtasks.filter(status='complete').count(),
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
        order = assignment.subtasks.count()
        subtask = AssignmentSubtask.objects.create(
            assignment=assignment,
            title=title,
            description=request.POST.get('description', '').strip(),
            sequence_order=order,
            estimated_hours=request.POST.get('estimated_hours') or None,
        )
        return JsonResponse({'success': True, 'id': subtask.id, 'title': subtask.title, 'status': subtask.status})
    return JsonResponse({'success': False}, status=405)


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
        subtask.save()
        return JsonResponse({'success': True, 'status': subtask.status,
                             'completion_pct': subtask.assignment.completion_pct})
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
    subtasks = list(assignment.subtasks.values(
        'id', 'title', 'description', 'status', 'sequence_order', 'estimated_hours'
    ))
    return JsonResponse({'subtasks': subtasks, 'completion_pct': assignment.completion_pct})