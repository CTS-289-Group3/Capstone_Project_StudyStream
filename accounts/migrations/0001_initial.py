# accounts/migrations/0001_initial.py
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── Semester ──────────────────────────────────────────────
        migrations.CreateModel(
            name='Semester',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='semesters',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),

        # ── Course ────────────────────────────────────────────────
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_code', models.CharField(max_length=20)),
                ('course_name', models.CharField(max_length=200)),
                ('color_hex', models.CharField(default='#3b82f6', max_length=7)),
                ('professor_name', models.CharField(blank=True, max_length=100)),
                ('professor_email', models.EmailField(blank=True)),
                ('office_hours', models.TextField(blank=True)),
                ('canvas_url', models.URLField(blank=True)),
                ('syllabus_url', models.URLField(blank=True)),
                ('meeting_times', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('semester', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='courses',
                    to='accounts.semester',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='courses',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['course_code'],
            },
        ),

        # ── Assignment ────────────────────────────────────────────
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('assignment_type', models.CharField(
                    choices=[
                        ('essay', 'Essay'), ('exam', 'Exam'), ('lab_report', 'Lab Report'),
                        ('problem_set', 'Problem Set'), ('discussion', 'Discussion Post'),
                        ('project', 'Project'), ('presentation', 'Presentation'),
                        ('reading', 'Reading'), ('other', 'Other'),
                    ],
                    default='other', max_length=20,
                )),
                ('due_date', models.DateTimeField()),
                ('estimated_hours', models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True)),
                ('status', models.CharField(
                    choices=[
                        ('not_started', 'Not Started'),
                        ('in_progress', 'In Progress'),
                        ('complete', 'Complete'),
                    ],
                    default='not_started', max_length=20,
                )),
                ('priority', models.CharField(
                    choices=[
                        ('low', 'Low'), ('medium', 'Medium'),
                        ('high', 'High'), ('critical', 'Critical'),
                    ],
                    default='medium', max_length=10,
                )),
                ('is_major', models.BooleanField(default=False)),
                ('completion_pct', models.IntegerField(default=0)),
                ('canvas_link', models.URLField(blank=True)),
                ('rubric_link', models.URLField(blank=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='assignments',
                    to='accounts.course',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='assignments',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['due_date'],
            },
        ),

        # ── AssignmentSubtask ─────────────────────────────────────
        migrations.CreateModel(
            name='AssignmentSubtask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('sequence_order', models.IntegerField(default=0)),
                ('milestone_date', models.DateTimeField(blank=True, null=True)),
                ('estimated_hours', models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True)),
                ('status', models.CharField(
                    choices=[
                        ('not_started', 'Not Started'),
                        ('in_progress', 'In Progress'),
                        ('complete', 'Complete'),
                    ],
                    default='not_started', max_length=20,
                )),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assignment', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='subtasks',
                    to='accounts.assignment',
                )),
            ],
            options={
                'ordering': ['sequence_order'],
            },
        ),

        # ── TimeBlock ─────────────────────────────────────────────
        migrations.CreateModel(
            name='TimeBlock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('location', models.CharField(blank=True, max_length=100)),
                ('remind_15min', models.BooleanField(default=True)),
                ('reminder_sent', models.BooleanField(default=False)),
                ('status', models.CharField(
                    choices=[
                        ('scheduled', 'Scheduled'), ('in_progress', 'In Progress'),
                        ('completed', 'Completed'), ('skipped', 'Skipped'),
                    ],
                    default='scheduled', max_length=20,
                )),
                ('actual_start', models.DateTimeField(blank=True, null=True)),
                ('actual_end', models.DateTimeField(blank=True, null=True)),
                ('productivity', models.IntegerField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('is_recurring', models.BooleanField(default=False)),
                ('recurrence', models.CharField(blank=True, max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assignment', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='time_blocks',
                    to='accounts.assignment',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='time_blocks',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['start_time'],
            },
        ),
    ]
