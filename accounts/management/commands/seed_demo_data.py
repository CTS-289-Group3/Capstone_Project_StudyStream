from datetime import date, datetime, time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Assignment, Course, Profile, Semester, Tag, TimeBlock, AssignmentSubtask
from core.models import (
    PersonalEvent,
    RecurringJobTitle,
    RecurringPersonalEvent,
    RecurringWorkLocation,
    RecurringWorkShift,
    WorkShift,
)


class Command(BaseCommand):
    help = "Populate StudyStream with demo data for testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default="tessab",
            help="Username for the demo account. Defaults to 'tessab'.",
        )
        parser.add_argument(
            "--password",
            default="StudyStream123!",
            help="Password for the demo account when it is created or updated.",
        )
        parser.add_argument(
            "--email",
            default="tessab_seed@gmail.com",
            help="Email address for the demo account.",
        )
        parser.add_argument(
            "--fresh",
            action="store_true",
            help="Delete the selected user's existing app data before inserting the demo dataset.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        email = options["email"]
        fresh = options["fresh"]

        user = self._get_or_create_user(username=username, password=password, email=email)

        if fresh:
            self._clear_user_data(user)

        self._seed_profile(user)
        seed_context = self._seed_academic_data(user)
        self._seed_schedule_data(user, seed_context)

        self.stdout.write(self.style.SUCCESS(f"Demo data ready for user '{user.username}'."))
        self.stdout.write(f"Username: {user.username}")
        self.stdout.write(f"Password: {password}")
        if fresh:
            self.stdout.write("Mode: refreshed existing data before seeding")
        else:
            self.stdout.write("Mode: merged demo data into existing account")

    def _get_or_create_user(self, username, password, email):
        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )
        if created:
            user.set_password(password)
            user.email = email
            user.save(update_fields=["password", "email"])
            return user

        updates = []
        if email and user.email != email:
            user.email = email
            updates.append("email")
        if password:
            user.set_password(password)
            updates.append("password")
        if updates:
            user.save(update_fields=updates)
        return user

    def _clear_user_data(self, user):
        AssignmentSubtask.objects.filter(assignment__user=user).delete()
        Assignment.objects.filter(user=user).delete()
        TimeBlock.objects.filter(user=user).delete()
        Tag.objects.filter(user=user).delete()
        Course.objects.filter(user=user).delete()
        Semester.objects.filter(user=user).delete()

        WorkShift.objects.filter(user=user).delete()
        PersonalEvent.objects.filter(user=user).delete()
        RecurringPersonalEvent.objects.filter(user=user).delete()
        RecurringWorkShift.objects.filter(user=user).delete()
        RecurringWorkLocation.objects.filter(user=user).delete()
        RecurringJobTitle.objects.filter(user=user).delete()

    def _seed_profile(self, user):
        Profile.objects.update_or_create(
            user=user,
            defaults={
                "display_name": "",
                "avatar_text": "",
                "bio": "",
                "major": "",
                "year": "",
            },
        )

    def _seed_academic_data(self, user):
        active_semester, _ = Semester.objects.update_or_create(
            user=user,
            name="Spring 2026",
            defaults={
                "start_date": date(2026, 1, 13),
                "end_date": date(2026, 5, 15),
                "is_active": True,
            },
        )
        Semester.objects.filter(user=user).exclude(id=active_semester.id).update(is_active=False)

        course_specs = [
            {
                "code": "CSC-113",
                "name": "Artificial Intel. fundamental",
                "color": "#ec4899",
            },
            {
                "code": "CSC-249",
                "name": "Data Structure & Algorithms",
                "color": "#ef4444",
            },
            {
                "code": "CSC-289",
                "name": "Programming Capstone",
                "color": "#10b981",
            },
            {
                "code": "NOS-125",
                "name": "Linux/Unix Scripting",
                "color": "#8b5cf6",
            },
        ]

        courses = {}
        for spec in course_specs:
            course, _ = Course.objects.update_or_create(
                user=user,
                semester=active_semester,
                course_code=spec["code"],
                defaults={
                    "course_name": spec["name"],
                    "color_hex": spec["color"],
                    "professor_name": "",
                    "professor_email": "",
                    "meeting_times": "",
                    "canvas_url": "",
                    "syllabus_url": "",
                    "office_hours": "",
                },
            )
            courses[spec["code"]] = course

        assignments = [
            {
                "course": courses["CSC-113"],
                "title": "Program for workout planner",
                "due_date": timezone.make_aware(datetime(2026, 4, 21, 17, 0)),
                "priority": "high",
                "status": "not_started",
            },
            {
                "course": courses["CSC-249"],
                "title": "Hash program",
                "due_date": timezone.make_aware(datetime(2026, 4, 22, 14, 0)),
                "priority": "high",
                "status": "not_started",
            },
            {
                "course": courses["NOS-125"],
                "title": "Linux Final Project",
                "due_date": timezone.make_aware(datetime(2026, 4, 24, 16, 23)),
                "priority": "high",
                "status": "not_started",
            },
            {
                "course": courses["CSC-289"],
                "title": "Capstone study stream",
                "due_date": timezone.make_aware(datetime(2026, 4, 25, 16, 23)),
                "priority": "critical",
                "status": "not_started",
            },
        ]

        for item in assignments:
            Assignment.objects.update_or_create(
                user=user,
                course=item["course"],
                title=item["title"],
                defaults={
                    "description": "",
                    "assignment_type": "project",
                    "due_date": item["due_date"],
                    "estimated_hours": None,
                    "status": item["status"],
                    "priority": item["priority"],
                    "is_major": False,
                    "canvas_link": "",
                    "rubric_link": "",
                    "completion_pct": 0,
                },
            )

        return {"courses": courses}

    def _seed_schedule_data(self, user, seed_context):
        work_shifts = [
            ("Cashier", date(2026, 4, 20), time(7, 0), time(13, 0), "Neighborhood market", "", "#f59e0b"),
            ("", date(2026, 4, 23), time(10, 0), time(14, 0), "Walmart", "", "#10b981"),
        ]
        for job_title, shift_date, start_time_value, end_time_value, location, notes, color in work_shifts:
            WorkShift.objects.update_or_create(
                user=user,
                job_title=job_title,
                shift_date=shift_date,
                defaults={
                    "start_time": start_time_value,
                    "end_time": end_time_value,
                    "location": location,
                    "notes": notes,
                    "color_hex": color,
                },
            )

        recurring_shifts = [
            ("Cashier", time(10, 0), time(14, 0), "Walmart", RecurringWorkShift.RECUR_WEEKLY),
            ("Customer Service", time(6, 0), time(10, 0), "Customer Service Desk - Walmart", RecurringWorkShift.RECUR_WEEKLY),
        ]
        for name, start_time_value, end_time_value, location, recurrence in recurring_shifts:
            RecurringWorkShift.objects.update_or_create(
                user=user,
                name=name,
                defaults={
                    "start_time": start_time_value,
                    "end_time": end_time_value,
                    "location": location,
                    "recurrence_pattern": recurrence,
                    "is_active": True,
                },
            )

        PersonalEvent.objects.update_or_create(
            user=user,
            title="Doxie's pre birthday event",
            event_date=date(2026, 4, 23),
            defaults={
                "description": "party party",
                "start_time": time(18, 0),
                "end_time": time(20, 0),
                "location": "209",
                "color_hex": "#06b6d4",
            },
        )
