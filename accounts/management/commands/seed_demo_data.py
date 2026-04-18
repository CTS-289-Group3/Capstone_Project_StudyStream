from datetime import date, datetime, time
from decimal import Decimal

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
    WorkloadAnalysis,
    WorkShift,
)


class Command(BaseCommand):
    help = "Populate StudyStream with demo data for testing."

    @staticmethod
    def _time_label(value):
        return value.strftime("%I:%M%p").lstrip("0").lower()

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
        WorkloadAnalysis.objects.filter(user=user).delete()

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
                "color": "#DC143C",
            },
            {
                "code": "CSC-249",
                "name": "Data Structure & Algorithms",
                "color": "#1E90FF",
            },
            {
                "code": "CSC-289",
                "name": "Programming Capstone",
                "color": "#228B22",
            },
            {
                "code": "NOS-125",
                "name": "Linux/Unix Scripting",
                "color": "#FFD700",
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
                "hours": Decimal("6.5"),
                "major": True,
                "type": "project",
                "description": "Build the planner logic, polish the interface, and prepare a short demo.",
                "subtasks": [
                    ("Draft database structure", 1, timezone.make_aware(datetime(2026, 4, 18, 18, 0)), Decimal("1.5"), "complete"),
                    ("Implement workout generation logic", 2, timezone.make_aware(datetime(2026, 4, 19, 20, 0)), Decimal("2.5"), "in_progress"),
                    ("Test and record demo", 3, timezone.make_aware(datetime(2026, 4, 21, 12, 0)), Decimal("2.5"), "not_started"),
                ],
            },
            {
                "course": courses["CSC-249"],
                "title": "Hash program",
                "due_date": timezone.make_aware(datetime(2026, 4, 22, 14, 0)),
                "priority": "high",
                "status": "not_started",
                "hours": Decimal("4.0"),
                "major": False,
                "type": "problem_set",
                "description": "Implement open addressing and compare collision behavior.",
                "subtasks": [
                    ("Write hash table insert/search", 1, timezone.make_aware(datetime(2026, 4, 20, 15, 0)), Decimal("2.0"), "not_started"),
                    ("Capture runtime analysis", 2, timezone.make_aware(datetime(2026, 4, 21, 19, 0)), Decimal("2.0"), "not_started"),
                ],
            },
            {
                "course": courses["NOS-125"],
                "title": "Linux Final Project",
                "due_date": timezone.make_aware(datetime(2026, 4, 24, 16, 23)),
                "priority": "high",
                "status": "not_started",
                "hours": Decimal("8.5"),
                "major": True,
                "type": "project",
                "description": "Package the final shell automation project and deployment notes.",
                "subtasks": [
                    ("Finish shell scripts", 1, timezone.make_aware(datetime(2026, 4, 21, 17, 30)), Decimal("3.0"), "in_progress"),
                    ("Write usage documentation", 2, timezone.make_aware(datetime(2026, 4, 22, 18, 0)), Decimal("2.0"), "not_started"),
                    ("Prepare submission archive", 3, timezone.make_aware(datetime(2026, 4, 24, 10, 0)), Decimal("1.5"), "not_started"),
                ],
            },
            {
                "course": courses["CSC-289"],
                "title": "Capstone study stream",
                "due_date": timezone.make_aware(datetime(2026, 4, 25, 16, 23)),
                "priority": "critical",
                "status": "not_started",
                "hours": Decimal("10.0"),
                "major": True,
                "type": "project",
                "description": "Integrate dashboard updates, seed data, and workload analysis improvements.",
                "subtasks": [
                    ("Update dashboard widgets", 1, timezone.make_aware(datetime(2026, 4, 22, 16, 0)), Decimal("3.0"), "in_progress"),
                    ("Seed new testing fields", 2, timezone.make_aware(datetime(2026, 4, 23, 12, 0)), Decimal("2.5"), "not_started"),
                    ("Review final demo flow", 3, timezone.make_aware(datetime(2026, 4, 25, 11, 0)), Decimal("2.0"), "not_started"),
                ],
            },
        ]

        for item in assignments:
            assignment, _ = Assignment.objects.update_or_create(
                user=user,
                course=item["course"],
                title=item["title"],
                defaults={
                    "description": item["description"],
                    "assignment_type": item["type"],
                    "due_date": item["due_date"],
                    "due_time": self._time_label(item["due_date"]) if hasattr(item["due_date"], "strftime") else "",
                    "estimated_hours": item["hours"],
                    "status": item["status"],
                    "priority_level": item["priority"],
                    "is_major_project": item["major"],
                    "canvas_link": "https://example.com/canvas/task",
                    "rubric_link": "https://example.com/rubric/task",
                    "submission_link": "https://example.com/submission/task",
                    "contributes_to_workload": True,
                    "completion_percentage": 0,
                },
            )

            for title, order, due_dt, hours, status in item["subtasks"]:
                AssignmentSubtask.objects.update_or_create(
                    assignment=assignment,
                    title=title,
                    defaults={
                        "description": "",
                        "step_order": order,
                        "due_date": due_dt,
                        "due_time": self._time_label(due_dt),
                        "estimated_hours": hours,
                        "status": status,
                    },
                )

        return {"courses": courses, "assignments": Assignment.objects.filter(user=user)}

    def _seed_schedule_data(self, user, seed_context):
        work_shifts = [
            ("Cashier", "Neighborhood Market", date(2026, 4, 20), time(7, 0), time(13, 0), "Neighborhood market", "Morning shift before class.", "#f59e0b", True, False, ""),
            ("Customer Service", "Walmart", date(2026, 4, 23), time(10, 0), time(14, 0), "Walmart", "Midday shift with customer desk coverage.", "#10b981", True, True, "weekly_thursday"),
        ]
        for job_title, employer_name, shift_date, start_time_value, end_time_value, location, notes, color, is_confirmed, is_recurring, recurrence_pattern in work_shifts:
            WorkShift.objects.update_or_create(
                user=user,
                employer_name=employer_name,
                shift_date=shift_date,
                defaults={
                    "job_title": job_title,
                    "start_time": start_time_value,
                    "end_time": end_time_value,
                    "shift_start": timezone.make_aware(datetime.combine(shift_date, start_time_value)),
                    "shift_end": timezone.make_aware(datetime.combine(shift_date, end_time_value)),
                    "location": location,
                    "notes": notes,
                    "color_hex": color,
                    "is_confirmed": is_confirmed,
                    "is_recurring": is_recurring,
                    "recurrence_pattern": recurrence_pattern,
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

        study_stream_assignment = seed_context["assignments"].filter(title="Capstone study stream").first()
        hash_assignment = seed_context["assignments"].filter(title="Hash program").first()

        if study_stream_assignment:
            TimeBlock.objects.update_or_create(
                user=user,
                title="Capstone dashboard polish",
                start_time=timezone.make_aware(datetime(2026, 4, 22, 18, 0)),
                defaults={
                    "assignment": study_stream_assignment,
                    "end_time": timezone.make_aware(datetime(2026, 4, 22, 20, 0)),
                    "location": "Home office",
                    "status": "scheduled",
                    "notes": "Focus on workload widgets and demo flow.",
                    "is_recurring": False,
                    "recurrence": "",
                },
            )

        if hash_assignment:
            TimeBlock.objects.update_or_create(
                user=user,
                title="Hash table implementation block",
                start_time=timezone.make_aware(datetime(2026, 4, 21, 19, 30)),
                defaults={
                    "assignment": hash_assignment,
                    "end_time": timezone.make_aware(datetime(2026, 4, 21, 21, 0)),
                    "location": "Campus library",
                    "status": "scheduled",
                    "notes": "Finish collision handling and tests.",
                    "is_recurring": False,
                    "recurrence": "",
                },
            )

        WorkloadAnalysis.objects.update_or_create(
            user=user,
            week_start_date=date(2026, 4, 20),
            defaults={
                "week_number": 17,
                "year": 2026,
                "total_class_hours": Decimal("15.00"),
                "total_work_hours": Decimal("10.00"),
                "total_assignment_hours": Decimal("29.00"),
                "available_study_hours": Decimal("87.00"),
                "utilization_ratio": Decimal("0.333"),
                "week_status": WorkloadAnalysis.STATUS_GREEN,
                "assignment_count": 4,
                "major_assignment_count": 3,
                "deadline_cluster_detected": True,
                "is_overloaded": False,
                "recommended_actions": [
                    {"action": "start_early", "message": "Major deadlines cluster late in the week. Start now."},
                    {"action": "protect_study_time", "message": "Keep your evening time blocks open for assignment work."},
                ],
                "alert_sent": False,
                "alert_sent_at": None,
            },
        )

        WorkloadAnalysis.objects.update_or_create(
            user=user,
            week_start_date=date(2026, 4, 27),
            defaults={
                "week_number": 18,
                "year": 2026,
                "total_class_hours": Decimal("15.00"),
                "total_work_hours": Decimal("20.00"),
                "total_assignment_hours": Decimal("46.00"),
                "available_study_hours": Decimal("77.00"),
                "utilization_ratio": Decimal("0.597"),
                "week_status": WorkloadAnalysis.STATUS_YELLOW,
                "assignment_count": 6,
                "major_assignment_count": 3,
                "deadline_cluster_detected": False,
                "is_overloaded": False,
                "recommended_actions": [
                    {"action": "plan_ahead", "message": "Heavy week ahead. Break larger assignments into smaller sessions."},
                ],
                "alert_sent": True,
                "alert_sent_at": timezone.make_aware(datetime(2026, 4, 17, 8, 0)),
            },
        )
