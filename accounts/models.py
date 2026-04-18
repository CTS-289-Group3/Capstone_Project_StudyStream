from django.db import models
from django.contrib.auth.models import User
import uuid


# ─────────────────────────────────────────────────────────────
#  SEMESTER
# ─────────────────────────────────────────────────────────────
class Semester(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='semesters')
    name        = models.CharField(max_length=100)          # "Fall 2026"
    start_date  = models.DateField(null=True, blank=True)
    end_date    = models.DateField(null=True, blank=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.user.username})"


# ─────────────────────────────────────────────────────────────
#  COURSE
# ─────────────────────────────────────────────────────────────
CLASS_COLORS = [
    ('#DC143C', 'Crimson (Red Pin)'),
    ('#1E90FF', 'Ocean (Blue Pin)'),
    ('#228B22', 'Forest (Green Pin)'),
    ('#FFD700', 'Sunflower (Yellow Pin)'),
    ('#8B00FF', 'Violet (Purple Pin)'),
    ('#FF8C00', 'Tangerine (Orange Pin)'),
    ('#008080', 'Teal (Teal Pin)'),
    ('#FF69B4', 'Rose (Pink Pin)'),
]

class Course(models.Model):
    semester        = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='courses')
    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    course_code     = models.CharField(max_length=20)
    course_name     = models.CharField(max_length=200)
    color_hex       = models.CharField(max_length=7, choices=CLASS_COLORS, default='#1E90FF')
    professor_name  = models.CharField(max_length=100, blank=True)
    professor_email = models.EmailField(blank=True)
    office_hours    = models.TextField(blank=True)
    canvas_url      = models.URLField(blank=True)
    syllabus_url    = models.URLField(blank=True)
    meeting_times   = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['course_code']

    def __str__(self):
        return f"{self.course_code}: {self.course_name}"


# ─────────────────────────────────────────────────────────────
#  TAG
# ─────────────────────────────────────────────────────────────
TAG_COLORS = [
    ('#ef4444', 'Red'),
    ('#f97316', 'Orange'),
    ('#f59e0b', 'Amber'),
    ('#10b981', 'Green'),
    ('#06b6d4', 'Teal'),
    ('#3b82f6', 'Blue'),
    ('#8b5cf6', 'Purple'),
    ('#ec4899', 'Pink'),
    ('#6b7280', 'Gray'),
]

class Tag(models.Model):
    user      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags')
    name      = models.CharField(max_length=50)
    color_hex = models.CharField(max_length=7, default='#3b82f6')

    class Meta:
        ordering = ['name']
        unique_together = [['user', 'name']]

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────────────────────
#  ASSIGNMENT
# ─────────────────────────────────────────────────────────────
STATUS_CHOICES = [
    ('not_started', 'Not Started'),
    ('in_progress', 'In Progress'),
    ('complete',    'Complete'),
]

PRIORITY_CHOICES = [
    ('low',      'Low'),
    ('medium',   'Medium'),
    ('high',     'High'),
    ('critical', 'Critical'),
]

TYPE_CHOICES = [
    ('essay',        'Essay'),
    ('exam',         'Exam'),
    ('lab_report',   'Lab Report'),
    ('problem_set',  'Problem Set'),
    ('discussion',   'Discussion Post'),
    ('project',      'Project'),
    ('presentation', 'Presentation'),
    ('reading',      'Reading'),
    ('quiz',         'Quiz'),
    ('homework',     'Homework'),
    ('other',        'Other'),
]

class Assignment(models.Model):
    assignment_id   = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    course          = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments')
    title           = models.CharField(max_length=255)
    description     = models.TextField(blank=True)
    assignment_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='other')
    due_date        = models.DateTimeField()
    due_time        = models.CharField(max_length=20, blank=True)
    estimated_hours = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    priority_level  = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_major_project = models.BooleanField(default=False)
    completion_percentage = models.IntegerField(default=0)
    canvas_link     = models.URLField(blank=True)
    rubric_link     = models.URLField(blank=True)
    submission_link = models.URLField(blank=True)
    contributes_to_workload = models.BooleanField(default=True)
    tags            = models.ManyToManyField(Tag, blank=True, related_name='assignments')
    started_at      = models.DateTimeField(null=True, blank=True)
    completed_at    = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"{self.title} ({self.course.course_code})"

    def update_completion(self):
        subtasks = self.subtasks.all()
        if subtasks.exists():
            done  = subtasks.filter(status='complete').count()
            total = subtasks.count()
            self.completion_percentage = int((done / total) * 100)
            self.save(update_fields=['completion_percentage'])


# ─────────────────────────────────────────────────────────────
#  ASSIGNMENT SUBTASK
# ─────────────────────────────────────────────────────────────
class AssignmentSubtask(models.Model):
    subtask_id      = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    assignment      = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='subtasks')
    title           = models.CharField(max_length=255)
    description     = models.TextField(blank=True)
    step_order      = models.IntegerField(default=0)
    due_date        = models.DateTimeField(null=True, blank=True)
    due_time        = models.CharField(max_length=20, blank=True)
    estimated_hours = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    completion_percentage = models.IntegerField(default=0)
    started_at      = models.DateTimeField(null=True, blank=True)
    completed_at    = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['step_order']

    def __str__(self):
        return f"Step {self.step_order}: {self.title}"

    def save(self, *args, **kwargs):
        self.completion_percentage = 100 if self.status == 'complete' else 0
        super().save(*args, **kwargs)
        self.assignment.update_completion()


# ─────────────────────────────────────────────────────────────
#  TIME BLOCK
# ─────────────────────────────────────────────────────────────
TIMEBLOCK_STATUS = [
    ('scheduled',   'Scheduled'),
    ('in_progress', 'In Progress'),
    ('completed',   'Completed'),
    ('skipped',     'Skipped'),
]

class TimeBlock(models.Model):
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_blocks')
    assignment   = models.ForeignKey(Assignment, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='time_blocks')
    title        = models.CharField(max_length=255)
    start_time   = models.DateTimeField()
    end_time     = models.DateTimeField()
    location     = models.CharField(max_length=100, blank=True)
    remind_15min = models.BooleanField(default=True)
    reminder_sent= models.BooleanField(default=False)
    status       = models.CharField(max_length=20, choices=TIMEBLOCK_STATUS, default='scheduled')
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end   = models.DateTimeField(null=True, blank=True)
    productivity = models.IntegerField(null=True, blank=True)
    notes        = models.TextField(blank=True)
    is_recurring = models.BooleanField(default=False)
    recurrence   = models.CharField(max_length=50, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.title} — {self.start_time.strftime('%a %b %d %I:%M%p')}"

    @property
    def duration_minutes(self):
        return int((self.end_time - self.start_time).total_seconds() / 60)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=50, blank=True)
    avatar_text = models.CharField(max_length=2, blank=True)
    bio = models.TextField(blank=True)
    major = models.CharField(max_length=100, blank=True)
    year = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f'{self.user.username} Profile'