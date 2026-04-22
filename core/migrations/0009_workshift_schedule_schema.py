from datetime import datetime
import uuid

from django.db import migrations, models
from django.utils import timezone


def backfill_workshift_schedule_fields(apps, schema_editor):
    WorkShift = apps.get_model("core", "WorkShift")
    tz = timezone.get_current_timezone()

    for shift in WorkShift.objects.all():
        update_fields = []

        if not shift.employer_name and shift.job_title:
            shift.employer_name = shift.job_title
            update_fields.append("employer_name")

        if shift.shift_date and shift.start_time and shift.end_time:
            start_dt = timezone.make_aware(datetime.combine(shift.shift_date, shift.start_time), tz)
            end_dt = timezone.make_aware(datetime.combine(shift.shift_date, shift.end_time), tz)
            shift.shift_start = start_dt
            shift.shift_end = end_dt
            update_fields.extend(["shift_start", "shift_end"])

        if update_fields:
            shift.save(update_fields=update_fields)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_recurringworkshift_recurrence_pattern"),
    ]

    operations = [
        migrations.AddField(
            model_name="workshift",
            name="shift_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name="workshift",
            name="employer_name",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="workshift",
            name="shift_start",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="workshift",
            name="shift_end",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="workshift",
            name="is_confirmed",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="workshift",
            name="is_recurring",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="workshift",
            name="recurrence_pattern",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="workshift",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="workshift",
            name="location",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.RunPython(backfill_workshift_schedule_fields, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="workshift",
            name="shift_start",
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name="workshift",
            name="shift_end",
            field=models.DateTimeField(),
        ),
    ]
