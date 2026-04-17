from django.conf import settings
from django.db import models

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    job_title = models.CharField(max_length=200, blank=True)
    shift_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    color_hex = models.CharField(max_length=7, default='#10b981')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.job_title} - {self.shift_date}"


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