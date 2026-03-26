# home/views.py
import json
from datetime import timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from accounts.models import Semester, Course, Assignment, Tag


@login_required(login_url='/accounts/login/')
def home_view(request):
    user = request.user
    now  = timezone.now()
    week_end = now + timedelta(days=7)

    # Core querysets
    semesters   = list(Semester.objects.filter(user=user).values('id', 'name', 'is_active', 'start_date', 'end_date'))
    active_sem  = Semester.objects.filter(user=user, is_active=True).first()
    courses     = list(Course.objects.filter(user=user).select_related('semester').values(
        'id', 'course_code', 'course_name', 'color_hex', 'semester__id', 'semester__name',
        'professor_name', 'meeting_times'
    ))
    tags = list(Tag.objects.filter(user=user).values('id', 'name', 'color_hex'))

    # Assignments
    all_assignments = Assignment.objects.filter(user=user).select_related('course').prefetch_related('tags', 'subtasks')

    assignments_data = []
    for a in all_assignments.order_by('due_date'):
        assignments_data.append({
            'id': a.id,
            'title': a.title,
            'course_id': a.course_id,
            'course_code': a.course.course_code,
            'course_name': a.course.course_name,
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

    # Stats
    due_this_week = all_assignments.filter(due_date__gte=now, due_date__lte=week_end, status__in=['not_started', 'in_progress']).count()
    completed     = all_assignments.filter(status='complete').count()
    overdue       = all_assignments.filter(due_date__lt=now, status__in=['not_started', 'in_progress']).count()
    active_courses = Course.objects.filter(user=user, semester__is_active=True).count()

    context = {
        'user': user,
        'semesters_json':   json.dumps(semesters),
        'courses_json':     json.dumps(courses),
        'assignments_json': json.dumps(assignments_data),
        'tags_json':        json.dumps(tags),
        'active_sem_id':    active_sem.id if active_sem else None,
        'stats': {
            'due_this_week':  due_this_week,
            'completed':      completed,
            'overdue':        overdue,
            'active_courses': active_courses,
        },
    }
    return render(request, 'home/home.html', context)