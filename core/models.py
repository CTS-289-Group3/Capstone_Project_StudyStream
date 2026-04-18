from django.conf import settings
from django.db import models
from datetime import datetime
import uuid

from django.utils import timezone

class Workspace(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)


class PersonalEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    color_hex = models.CharField(max_length=7, default='#FCAF17')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class WorkShift(models.Model):
    shift_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    job_title = models.CharField(max_length=200, blank=True)
    employer_name = models.CharField(max_length=100, blank=True)
    shift_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    shift_start = models.DateTimeField()
    shift_end = models.DateTimeField()
    location = models.CharField(max_length=100, blank=True)
    is_confirmed = models.BooleanField(default=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    color_hex = models.CharField(max_length=7, default='#10b981')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employer_name or self.job_title or 'Work Shift'} - {self.shift_date}"

    @property
    def duration_hours(self):
        if not self.shift_start or not self.shift_end:
            return None
        return round((self.shift_end - self.shift_start).total_seconds() / 3600, 2)

    def save(self, *args, **kwargs):
        if self.employer_name and not self.job_title:
            self.job_title = self.employer_name
        if self.job_title and not self.employer_name:
            self.employer_name = self.job_title

        if self.shift_start and self.shift_end:
            start_local = timezone.localtime(self.shift_start)
            end_local = timezone.localtime(self.shift_end)
            self.shift_date = start_local.date()
            self.start_time = start_local.time().replace(microsecond=0)
            self.end_time = end_local.time().replace(microsecond=0)
        elif self.shift_date and self.start_time and self.end_time:
            tz = timezone.get_current_timezone()
            self.shift_start = timezone.make_aware(datetime.combine(self.shift_date, self.start_time), tz)
            self.shift_end = timezone.make_aware(datetime.combine(self.shift_date, self.end_time), tz)

        super().save(*args, **kwargs)


class RecurringWorkShift(models.Model):
    RECUR_WEEKLY = "weekly"
    RECUR_BIWEEKLY = "biweekly"
    RECUR_MONTHLY = "monthly"

    RECUR_CHOICES = [
        (RECUR_WEEKLY, "Weekly"),
        (RECUR_BIWEEKLY, "Every 2 Weeks"),
        (RECUR_MONTHLY, "Monthly"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=200, blank=True)
    recurrence_pattern = models.CharField(max_length=20, choices=RECUR_CHOICES, default=RECUR_WEEKLY)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "start_time"]

    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')})"


class RecurringWorkLocation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class RecurringJobTitle(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class RecurringPersonalEvent(models.Model):
    RECUR_WEEKLY = "weekly"
    RECUR_BIWEEKLY = "biweekly"
    RECUR_MONTHLY = "monthly"

    RECUR_CHOICES = [
        (RECUR_WEEKLY, "Weekly"),
        (RECUR_BIWEEKLY, "Every 2 Weeks"),
        (RECUR_MONTHLY, "Monthly"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    recurrence_pattern = models.CharField(max_length=20, choices=RECUR_CHOICES)
    weekdays = models.CharField(max_length=20, blank=True)
    monthly_day = models.PositiveSmallIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title", "start_date"]

    def __str__(self):
        return f"{self.title} ({self.get_recurrence_pattern_display()})"


class WorkloadAnalysis(models.Model):
    STATUS_GREEN = "GREEN"
    STATUS_YELLOW = "YELLOW"
    STATUS_RED = "RED"

    WEEK_STATUS_CHOICES = [
        (STATUS_GREEN, "Green"),
        (STATUS_YELLOW, "Yellow"),
        (STATUS_RED, "Red"),
    ]

    analysis_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workload_analyses")

    week_start_date = models.DateField()
    week_number = models.PositiveSmallIntegerField(null=True, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)

    total_class_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_work_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_assignment_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    available_study_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    utilization_ratio = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    week_status = models.CharField(max_length=10, choices=WEEK_STATUS_CHOICES, blank=True)

    assignment_count = models.IntegerField(null=True, blank=True)
    major_assignment_count = models.IntegerField(null=True, blank=True)
    deadline_cluster_detected = models.BooleanField(default=False)

    is_overloaded = models.BooleanField(default=False)
    recommended_actions = models.JSONField(default=list, blank=True)

    alert_sent = models.BooleanField(default=False)
    alert_sent_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-week_start_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "week_start_date"], name="unique_user_week_start_workload_analysis"),
        ]

    def save(self, *args, **kwargs):
        if self.week_start_date:
            iso_year, iso_week, _ = self.week_start_date.isocalendar()
            if self.week_number is None:
                self.week_number = iso_week
            if self.year is None:
                self.year = iso_year
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Workload {self.user_id} - {self.week_start_date}"