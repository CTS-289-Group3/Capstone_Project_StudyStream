from django.db import models
from django.contrib.auth.models import User


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
    ('#ef4444', 'Red'),
    ('#3b82f6', 'Blue'),
    ('#8b5cf6', 'Purple'),
    ('#10b981', 'Green'),
    ('#f59e0b', 'Yellow'),
    ('#f97316', 'Orange'),
    ('#06b6d4', 'Teal'),
    ('#ec4899', 'Pink'),
]

class Course(models.Model):
    semester        = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='courses')
    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    course_code     = models.CharField(max_length=20)
    course_name     = models.CharField(max_length=200)
    color_hex       = models.CharField(max_length=7, default='#3b82f6')
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
    course          = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments')
    title           = models.CharField(max_length=255)
    description     = models.TextField(blank=True)
    assignment_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='other')
    due_date        = models.DateTimeField()
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    priority        = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_major        = models.BooleanField(default=False)
    completion_pct  = models.IntegerField(default=0)
    canvas_link     = models.URLField(blank=True)
    rubric_link     = models.URLField(blank=True)
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
            self.completion_pct = int((done / total) * 100)
            self.save(update_fields=['completion_pct'])


# ─────────────────────────────────────────────────────────────
#  ASSIGNMENT SUBTASK
# ─────────────────────────────────────────────────────────────
class AssignmentSubtask(models.Model):
    assignment      = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='subtasks')
    title           = models.CharField(max_length=255)
    description     = models.TextField(blank=True)
    sequence_order  = models.IntegerField(default=0)
    milestone_date  = models.DateTimeField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    started_at      = models.DateTimeField(null=True, blank=True)
    completed_at    = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sequence_order']

    def __str__(self):
        return f"Step {self.sequence_order}: {self.title}"

    def save(self, *args, **kwargs):
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