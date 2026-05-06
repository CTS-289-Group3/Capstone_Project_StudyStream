from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Assignment, Course, Profile, Semester, Tag, TimeBlock, AssignmentSubtask
from core.scheduling import build_scheduled_item, get_schedule_conflict
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
    DEFAULT_USERNAME = "testb"
    DEFAULT_PASSWORD = "Pass123!"
    DEFAULT_EMAIL = "testb@gmail.com"

    @staticmethod
    def _time_label(value):
        return value.strftime("%I:%M%p").lstrip("0").lower()

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default=self.DEFAULT_USERNAME,
            help="Username for the demo account. Defaults to 'testb'.",
        )
        parser.add_argument(
            "--password",
            default=self.DEFAULT_PASSWORD,
            help="Password for the demo account when it is created or updated.",
        )
        parser.add_argument(
            "--email",
            default=self.DEFAULT_EMAIL,
            help="Email address for the demo account.",
        )
        parser.add_argument(
            "--scenario",
            choices=["default", "testa", "emma"],
            default="default",
            help="Seed scenario. Use 'testa' for a current-week overload dataset or 'emma' for a Spring 2026 student schedule.",
        )
        parser.add_argument(
            "--fresh",
            action="store_true",
            help="Delete the selected user's existing app data before inserting the demo dataset.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        scenario = options["scenario"]
        username = options["username"]
        password = options["password"]
        email = options["email"]

        if scenario == "testa":
            if username == self.DEFAULT_USERNAME:
                username = "testA"
            if password == self.DEFAULT_PASSWORD:
                password = "Pass123!"
            if email == self.DEFAULT_EMAIL:
                email = "testa_seed@example.com"
        elif scenario == "emma":
            if username == self.DEFAULT_USERNAME:
                username = "emma"
            if password == self.DEFAULT_PASSWORD:
                password = "Pass123!"
            if email == self.DEFAULT_EMAIL:
                email = "emma_seed@example.com"

        fresh = options["fresh"]

        user = self._get_or_create_user(username=username, password=password, email=email)

        if fresh:
            self._clear_user_data(user)

        self._seed_profile_for_scenario(user, scenario=scenario)
        seed_context = self._seed_academic_data(user, scenario=scenario)
        self._seed_schedule_data(user, seed_context, scenario=scenario)

        if scenario == "testa":
            self._apply_testa_overload_tuning(user)

        self.stdout.write(self.style.SUCCESS(f"Demo data ready for user '{user.username}'."))
        self.stdout.write(f"Username: {user.username}")
        self.stdout.write(f"Password: {password}")
        self.stdout.write(f"Scenario: {scenario}")
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

    def _find_open_slot(
        self,
        user,
        *,
        kind,
        title,
        start,
        end=None,
        duration_hours=None,
        kind_key=None,
        max_attempts=200,
    ):
        requested = build_scheduled_item(
            kind,
            title,
            start,
            end=end,
            duration_hours=duration_hours,
            kind_key=kind_key,
        )

        if requested is None:
            return None

        for _ in range(max_attempts):
            conflict = get_schedule_conflict(user, [requested])
            if not conflict:
                return requested

            suggestion = conflict.suggestion_item
            if not suggestion:
                break

            requested = build_scheduled_item(
                kind,
                title,
                suggestion.start,
                end=suggestion.end,
                kind_key=kind_key,
            )

        raise RuntimeError(
            f"Unable to place seed item '{title}' without schedule conflicts."
        )

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
        self._seed_profile_for_scenario(user, scenario="default")

    def _seed_profile_for_scenario(self, user, scenario="default"):
        profile_defaults = {
            "display_name": "",
            "avatar_text": "",
            "bio": "",
            "major": "",
            "year": "",
        }

        if scenario == "emma":
            profile_defaults.update(
                {
                    "display_name": "Emma",
                    "avatar_text": "EM",
                    "bio": "Busy spring semester balancing classes, family time, and small appointments.",
                    "major": "Business Administration",
                    "year": "Sophomore",
                    "sleep_hours_per_night": Decimal("7.5"),
                    "sleep_start_time": time(23, 0),
                    "sleep_end_time": time(7, 0),
                    "personal_time_hours_per_week": Decimal("10.0"),
                    "family_time_hours_per_week": Decimal("14.0"),
                    "commute_time_hours_per_week": Decimal("4.0"),
                }
            )

        Profile.objects.update_or_create(user=user, defaults=profile_defaults)

    def _seed_academic_data(self, user, scenario="default"):
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

        if scenario == "emma":
            course_specs = [
                {
                    "code": "ENG-112",
                    "name": "Writing and Research in the Disciplines",
                    "color": "#DC143C",
                    "meeting_times": "MW 10:00am-11:15am",
                    "weekly_study_hours": Decimal("5.0"),
                },
                {
                    "code": "MAT-171",
                    "name": "Precalculus Algebra",
                    "color": "#1E90FF",
                    "meeting_times": "TR 9:30am-10:45am",
                    "weekly_study_hours": Decimal("6.0"),
                },
                {
                    "code": "BIO-168",
                    "name": "Anatomy and Physiology I",
                    "color": "#228B22",
                    "meeting_times": "MW 1:00pm-2:15pm, Lab F 9:00am-10:50am",
                    "weekly_study_hours": Decimal("7.0"),
                },
                {
                    "code": "BUS-110",
                    "name": "Introduction to Business",
                    "color": "#FFD700",
                    "meeting_times": "TR 1:00pm-2:15pm",
                    "weekly_study_hours": Decimal("4.5"),
                },
            ]
        else:
            course_specs = [
                {
                    "code": "CSC-113",
                    "name": "Artificial Intel. Fundamentals",
                    "color": "#DC143C",
                    "meeting_times": "MWF 9:00am-9:50am",
                },
                {
                    "code": "CSC-249",
                    "name": "Data Structures & Algorithms",
                    "color": "#1E90FF",
                    "meeting_times": "TR 11:00am-12:15pm",
                },
                {
                    "code": "CSC-289",
                    "name": "Programming Capstone",
                    "color": "#228B22",
                    "meeting_times": "MW 1:00pm-2:15pm",
                },
                {
                    "code": "NOS-125",
                    "name": "Linux/Unix Scripting",
                    "color": "#FFD700",
                    "meeting_times": "TR 2:30pm-3:45pm",
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
                    "meeting_times": spec["meeting_times"],
                    "weekly_study_hours": spec.get("weekly_study_hours", Decimal("0.0")),
                    "canvas_url": "",
                    "syllabus_url": "",
                    "office_hours": "",
                },
            )
            courses[spec["code"]] = course

        # ------------------------------------------------------------------ #
        #  ASSIGNMENTS                                                        #
        # ------------------------------------------------------------------ #
        if scenario == "emma":
            assignments = [
                {
                    "course": courses["ENG-112"],
                    "title": "Annotated Bibliography",
                    "due_date": timezone.make_aware(datetime(2026, 4, 23, 23, 59)),
                    "priority": "high",
                    "status": "in_progress",
                    "hours": Decimal("4.0"),
                    "major": False,
                    "type": "essay",
                    "description": "Compile six research sources for the final paper and format them in MLA.",
                    "subtasks": [
                        ("Confirm final paper topic", 1, timezone.make_aware(datetime(2026, 4, 20, 18, 0)), Decimal("0.5"), "complete"),
                        ("Find and annotate 3 journal articles", 2, timezone.make_aware(datetime(2026, 4, 21, 20, 0)), Decimal("1.5"), "complete"),
                        ("Annotate remaining sources", 3, timezone.make_aware(datetime(2026, 4, 22, 20, 30)), Decimal("1.5"), "in_progress"),
                        ("Proofread MLA formatting", 4, timezone.make_aware(datetime(2026, 4, 23, 18, 30)), Decimal("0.5"), "not_started"),
                    ],
                },
                {
                    "course": courses["MAT-171"],
                    "title": "Polynomial Functions Problem Set",
                    "due_date": timezone.make_aware(datetime(2026, 4, 24, 17, 0)),
                    "priority": "high",
                    "status": "in_progress",
                    "hours": Decimal("3.5"),
                    "major": False,
                    "type": "homework",
                    "description": "Complete practice problems on graphing, zeros, and end behavior.",
                    "subtasks": [
                        ("Finish textbook odd problems", 1, timezone.make_aware(datetime(2026, 4, 22, 17, 30)), Decimal("1.0"), "complete"),
                        ("Redo missed quiz questions", 2, timezone.make_aware(datetime(2026, 4, 23, 19, 0)), Decimal("1.0"), "in_progress"),
                        ("Check answers in tutoring center", 3, timezone.make_aware(datetime(2026, 4, 24, 11, 0)), Decimal("1.0"), "not_started"),
                        ("Upload final PDF", 4, timezone.make_aware(datetime(2026, 4, 24, 16, 30)), Decimal("0.5"), "not_started"),
                    ],
                },
                {
                    "course": courses["BIO-168"],
                    "title": "Nervous System Lab Report",
                    "due_date": timezone.make_aware(datetime(2026, 4, 28, 13, 0)),
                    "priority": "high",
                    "status": "not_started",
                    "hours": Decimal("5.0"),
                    "major": False,
                    "type": "lab_report",
                    "description": "Write the lab report covering the sheep brain dissection and nervous tissue observations.",
                    "subtasks": [
                        ("Organize lab notes and photos", 1, timezone.make_aware(datetime(2026, 4, 25, 15, 30)), Decimal("1.0"), "not_started"),
                        ("Draft methods and results", 2, timezone.make_aware(datetime(2026, 4, 26, 17, 0)), Decimal("2.0"), "not_started"),
                        ("Write discussion section", 3, timezone.make_aware(datetime(2026, 4, 27, 20, 0)), Decimal("1.5"), "not_started"),
                        ("Review rubric and submit", 4, timezone.make_aware(datetime(2026, 4, 28, 11, 30)), Decimal("0.5"), "not_started"),
                    ],
                },
                {
                    "course": courses["BUS-110"],
                    "title": "Marketing Pitch Deck",
                    "due_date": timezone.make_aware(datetime(2026, 4, 30, 15, 0)),
                    "priority": "medium",
                    "status": "in_progress",
                    "hours": Decimal("4.5"),
                    "major": False,
                    "type": "presentation",
                    "description": "Build a short pitch deck for a small business product launch case study.",
                    "subtasks": [
                        ("Choose product and target audience", 1, timezone.make_aware(datetime(2026, 4, 24, 18, 0)), Decimal("0.5"), "complete"),
                        ("Draft slide outline", 2, timezone.make_aware(datetime(2026, 4, 26, 14, 0)), Decimal("1.0"), "complete"),
                        ("Design slides and visuals", 3, timezone.make_aware(datetime(2026, 4, 28, 18, 30)), Decimal("2.0"), "in_progress"),
                        ("Practice 5-minute pitch", 4, timezone.make_aware(datetime(2026, 4, 29, 19, 30)), Decimal("1.0"), "not_started"),
                    ],
                },
                {
                    "course": courses["ENG-112"],
                    "title": "Peer Review Workshop",
                    "due_date": timezone.make_aware(datetime(2026, 5, 4, 12, 0)),
                    "priority": "medium",
                    "status": "not_started",
                    "hours": Decimal("2.0"),
                    "major": False,
                    "type": "other",
                    "description": "Provide written feedback on two classmates' draft essays before the workshop.",
                    "subtasks": [
                        ("Read first classmate draft", 1, timezone.make_aware(datetime(2026, 5, 2, 15, 0)), Decimal("0.5"), "not_started"),
                        ("Read second classmate draft", 2, timezone.make_aware(datetime(2026, 5, 2, 16, 0)), Decimal("0.5"), "not_started"),
                        ("Complete peer review forms", 3, timezone.make_aware(datetime(2026, 5, 3, 19, 30)), Decimal("1.0"), "not_started"),
                    ],
                },
                {
                    "course": courses["MAT-171"],
                    "title": "Rational Functions Quiz Review",
                    "due_date": timezone.make_aware(datetime(2026, 5, 1, 9, 30)),
                    "priority": "medium",
                    "status": "not_started",
                    "hours": Decimal("2.5"),
                    "major": False,
                    "type": "quiz",
                    "description": "Prepare for the chapter quiz covering asymptotes and graph transformations.",
                    "subtasks": [
                        ("Review class notes", 1, timezone.make_aware(datetime(2026, 4, 29, 17, 30)), Decimal("0.5"), "not_started"),
                        ("Complete practice quiz", 2, timezone.make_aware(datetime(2026, 4, 30, 18, 0)), Decimal("1.0"), "not_started"),
                        ("Meet with math tutor", 3, timezone.make_aware(datetime(2026, 4, 30, 19, 30)), Decimal("1.0"), "not_started"),
                    ],
                },
                {
                    "course": courses["BIO-168"],
                    "title": "Homeostasis Group Presentation",
                    "due_date": timezone.make_aware(datetime(2026, 5, 7, 13, 0)),
                    "priority": "high",
                    "status": "not_started",
                    "hours": Decimal("4.0"),
                    "major": False,
                    "type": "presentation",
                    "description": "Present how the endocrine and nervous systems work together to maintain homeostasis.",
                    "subtasks": [
                        ("Split talking points with group", 1, timezone.make_aware(datetime(2026, 5, 3, 18, 0)), Decimal("0.5"), "not_started"),
                        ("Design Emma's slides", 2, timezone.make_aware(datetime(2026, 5, 4, 20, 0)), Decimal("1.5"), "not_started"),
                        ("Rehearse with group", 3, timezone.make_aware(datetime(2026, 5, 6, 15, 0)), Decimal("1.0"), "not_started"),
                        ("Print speaker notes", 4, timezone.make_aware(datetime(2026, 5, 7, 10, 0)), Decimal("1.0"), "not_started"),
                    ],
                },
                {
                    "course": courses["BUS-110"],
                    "title": "Weekly Budget Reflection",
                    "due_date": timezone.make_aware(datetime(2026, 5, 8, 23, 0)),
                    "priority": "low",
                    "status": "not_started",
                    "hours": Decimal("1.5"),
                    "major": False,
                    "type": "essay",
                    "description": "Reflect on a one-week personal budget tracker and spending habits.",
                    "subtasks": [
                        ("Update expense tracker", 1, timezone.make_aware(datetime(2026, 5, 6, 20, 30)), Decimal("0.5"), "not_started"),
                        ("Write reflection paragraph", 2, timezone.make_aware(datetime(2026, 5, 7, 20, 0)), Decimal("0.5"), "not_started"),
                        ("Submit to LMS", 3, timezone.make_aware(datetime(2026, 5, 8, 21, 30)), Decimal("0.5"), "not_started"),
                    ],
                },
                {
                    "course": courses["ENG-112"],
                    "title": "Research Essay Final Draft",
                    "due_date": timezone.make_aware(datetime(2026, 5, 12, 23, 59)),
                    "priority": "critical",
                    "status": "not_started",
                    "hours": Decimal("7.0"),
                    "major": True,
                    "type": "essay",
                    "description": "Submit the final 6-8 page research essay with revised thesis, sources, and Works Cited.",
                    "subtasks": [
                        ("Revise thesis and outline", 1, timezone.make_aware(datetime(2026, 5, 7, 18, 30)), Decimal("1.0"), "not_started"),
                        ("Draft body sections", 2, timezone.make_aware(datetime(2026, 5, 9, 16, 0)), Decimal("2.5"), "not_started"),
                        ("Integrate quotes and citations", 3, timezone.make_aware(datetime(2026, 5, 10, 16, 30)), Decimal("1.5"), "not_started"),
                        ("Visit writing center", 4, timezone.make_aware(datetime(2026, 5, 11, 14, 0)), Decimal("1.0"), "not_started"),
                        ("Final proofread and submit", 5, timezone.make_aware(datetime(2026, 5, 12, 21, 30)), Decimal("1.0"), "not_started"),
                    ],
                },
                {
                    "course": courses["BUS-110"],
                    "title": "Business Ethics Case Study",
                    "due_date": timezone.make_aware(datetime(2026, 5, 11, 17, 0)),
                    "priority": "medium",
                    "status": "not_started",
                    "hours": Decimal("3.0"),
                    "major": False,
                    "type": "essay",
                    "description": "Analyze an ethics case and recommend how the company should respond.",
                    "subtasks": [
                        ("Read case packet", 1, timezone.make_aware(datetime(2026, 5, 8, 18, 30)), Decimal("0.5"), "not_started"),
                        ("Draft response outline", 2, timezone.make_aware(datetime(2026, 5, 9, 14, 0)), Decimal("0.5"), "not_started"),
                        ("Write case analysis", 3, timezone.make_aware(datetime(2026, 5, 10, 13, 30)), Decimal("1.5"), "not_started"),
                        ("Revise and submit", 4, timezone.make_aware(datetime(2026, 5, 11, 15, 30)), Decimal("0.5"), "not_started"),
                    ],
                },
                {
                    "course": courses["MAT-171"],
                    "title": "Precalculus Final Exam",
                    "due_date": timezone.make_aware(datetime(2026, 5, 14, 8, 0)),
                    "priority": "critical",
                    "status": "not_started",
                    "hours": Decimal("6.0"),
                    "major": True,
                    "type": "exam",
                    "description": "Comprehensive final exam on polynomial, exponential, logarithmic, and rational functions.",
                    "subtasks": [
                        ("Make formula review sheet", 1, timezone.make_aware(datetime(2026, 5, 10, 12, 0)), Decimal("1.0"), "not_started"),
                        ("Complete practice test 1", 2, timezone.make_aware(datetime(2026, 5, 11, 19, 0)), Decimal("1.5"), "not_started"),
                        ("Attend tutoring session", 3, timezone.make_aware(datetime(2026, 5, 12, 16, 0)), Decimal("1.0"), "not_started"),
                        ("Complete practice test 2", 4, timezone.make_aware(datetime(2026, 5, 13, 14, 0)), Decimal("1.5"), "not_started"),
                        ("Light morning review", 5, timezone.make_aware(datetime(2026, 5, 14, 6, 30)), Decimal("1.0"), "not_started"),
                    ],
                },
                {
                    "course": courses["BIO-168"],
                    "title": "Anatomy Practical Final",
                    "due_date": timezone.make_aware(datetime(2026, 5, 15, 9, 0)),
                    "priority": "critical",
                    "status": "not_started",
                    "hours": Decimal("6.5"),
                    "major": True,
                    "type": "exam",
                    "description": "Practical final covering skeletal, muscular, nervous, and organ identification.",
                    "subtasks": [
                        ("Review labeled diagrams", 1, timezone.make_aware(datetime(2026, 5, 11, 17, 30)), Decimal("1.5"), "not_started"),
                        ("Flashcard lab structures", 2, timezone.make_aware(datetime(2026, 5, 12, 19, 0)), Decimal("1.5"), "not_started"),
                        ("Meet study group in lab", 3, timezone.make_aware(datetime(2026, 5, 13, 16, 30)), Decimal("1.5"), "not_started"),
                        ("Timed specimen review", 4, timezone.make_aware(datetime(2026, 5, 14, 18, 30)), Decimal("1.0"), "not_started"),
                        ("Pack supplies and review checklist", 5, timezone.make_aware(datetime(2026, 5, 14, 21, 0)), Decimal("1.0"), "not_started"),
                    ],
                },
            ]
        else:
            assignments = [
            # ── WEEK 1 (Apr 19–25) ─────────────────────────────────────────
            {
                "course": courses["CSC-113"],
                "title": "Workout Planner Program",
                "due_date": timezone.make_aware(datetime(2026, 4, 21, 17, 0)),
                "priority": "high",
                "status": "in_progress",
                "hours": Decimal("6.5"),
                "major": True,
                "type": "project",
                "description": "Build the planner logic, polish the interface, and prepare a short demo.",
                "subtasks": [
                    ("Draft database structure",            1, timezone.make_aware(datetime(2026, 4, 18, 18, 0)), Decimal("1.5"), "complete"),
                    ("Implement workout generation logic",  2, timezone.make_aware(datetime(2026, 4, 19, 20, 0)), Decimal("2.5"), "in_progress"),
                    ("Test and record demo",                3, timezone.make_aware(datetime(2026, 4, 21, 12, 0)), Decimal("2.5"), "not_started"),
                ],
            },
            {
                "course": courses["CSC-249"],
                "title": "Hash Table Implementation",
                "due_date": timezone.make_aware(datetime(2026, 4, 22, 14, 0)),
                "priority": "high",
                "status": "not_started",
                "hours": Decimal("4.0"),
                "major": False,
                "type": "problem_set",
                "description": "Implement open addressing and compare collision behavior.",
                "subtasks": [
                    ("Write hash table insert/search", 1, timezone.make_aware(datetime(2026, 4, 20, 18, 0)), Decimal("2.0"), "not_started"),
                    ("Capture runtime analysis",        2, timezone.make_aware(datetime(2026, 4, 21, 21, 0)), Decimal("2.0"), "not_started"),
                ],
            },
            {
                "course": courses["NOS-125"],
                "title": "Linux Final Project",
                "due_date": timezone.make_aware(datetime(2026, 4, 24, 16, 23)),
                "priority": "high",
                "status": "in_progress",
                "hours": Decimal("8.5"),
                "major": True,
                "type": "project",
                "description": "Package the final shell automation project and deployment notes.",
                "subtasks": [
                    ("Finish shell scripts",          1, timezone.make_aware(datetime(2026, 4, 21, 14, 30)), Decimal("3.0"), "in_progress"),
                    ("Write usage documentation",     2, timezone.make_aware(datetime(2026, 4, 22, 21, 0)),  Decimal("2.0"), "not_started"),
                    ("Prepare submission archive",    3, timezone.make_aware(datetime(2026, 4, 24, 10, 0)),  Decimal("1.5"), "not_started"),
                    ("Peer review partner's script",  4, timezone.make_aware(datetime(2026, 4, 23, 14, 0)),  Decimal("1.0"), "not_started"),
                    ("Record walkthrough screencast", 5, timezone.make_aware(datetime(2026, 4, 24, 13, 0)),  Decimal("1.0"), "not_started"),
                ],
            },
            {
                "course": courses["CSC-289"],
                "title": "Capstone: StudyStream",
                "due_date": timezone.make_aware(datetime(2026, 4, 25, 16, 23)),
                "priority": "critical",
                "status": "in_progress",
                "hours": Decimal("10.0"),
                "major": True,
                "type": "project",
                "description": "Integrate dashboard updates, seed data, and workload analysis improvements.",
                "subtasks": [
                    ("Update dashboard widgets",  1, timezone.make_aware(datetime(2026, 4, 22, 8, 0)), Decimal("3.0"), "in_progress"),
                    ("Seed new testing fields",   2, timezone.make_aware(datetime(2026, 4, 23, 15, 0)), Decimal("2.5"), "not_started"),
                    ("Review final demo flow",    3, timezone.make_aware(datetime(2026, 4, 25, 11, 0)), Decimal("2.0"), "not_started"),
                    ("Write project README",      4, timezone.make_aware(datetime(2026, 4, 24, 15, 0)), Decimal("1.0"), "not_started"),
                    ("Submit to Canvas",          5, timezone.make_aware(datetime(2026, 4, 25, 16, 0)), Decimal("0.5"), "not_started"),
                ],
            },

            # ── WEEK 2 (Apr 26 – May 2) ────────────────────────────────────
            {
                "course": courses["CSC-113"],
                "title": "AI Ethics Reflection Paper",
                "due_date": timezone.make_aware(datetime(2026, 4, 29, 23, 59)),
                "priority": "medium",
                "status": "not_started",
                "hours": Decimal("3.5"),
                "major": False,
                "type": "essay",
                "description": "Reflect on bias, fairness, and transparency in modern AI systems. Minimum 800 words.",
                "subtasks": [
                    ("Outline key argument",         1, timezone.make_aware(datetime(2026, 4, 26, 19, 0)), Decimal("0.5"), "not_started"),
                    ("Draft body paragraphs",        2, timezone.make_aware(datetime(2026, 4, 27, 18, 0)), Decimal("1.5"), "not_started"),
                    ("Add citations and revise",     3, timezone.make_aware(datetime(2026, 4, 28, 21, 0)), Decimal("1.0"), "not_started"),
                    ("Proofread and submit",         4, timezone.make_aware(datetime(2026, 4, 29, 21, 0)), Decimal("0.5"), "not_started"),
                ],
            },
            {
                "course": courses["CSC-249"],
                "title": "Sorting Algorithm Comparison",
                "due_date": timezone.make_aware(datetime(2026, 4, 30, 14, 0)),
                "priority": "medium",
                "status": "not_started",
                "hours": Decimal("5.0"),
                "major": False,
                "type": "problem_set",
                "description": "Implement merge sort, quicksort, and heapsort. Benchmark on 3 dataset sizes.",
                "subtasks": [
                    ("Implement merge sort",           1, timezone.make_aware(datetime(2026, 4, 26, 15, 0)), Decimal("1.0"), "not_started"),
                    ("Implement quicksort",            2, timezone.make_aware(datetime(2026, 4, 27, 15, 0)), Decimal("1.0"), "not_started"),
                    ("Implement heapsort",             3, timezone.make_aware(datetime(2026, 4, 28, 19, 0)), Decimal("1.0"), "not_started"),
                    ("Run benchmarks + record data",   4, timezone.make_aware(datetime(2026, 4, 29, 17, 0)), Decimal("1.0"), "not_started"),
                    ("Write analysis summary",         5, timezone.make_aware(datetime(2026, 4, 30, 11, 0)), Decimal("1.0"), "not_started"),
                ],
            },
            {
                "course": courses["NOS-125"],
                "title": "Cron Jobs & Scheduling Lab",
                "due_date": timezone.make_aware(datetime(2026, 5, 1, 17, 0)),
                "priority": "medium",
                "status": "not_started",
                "hours": Decimal("3.0"),
                "major": False,
                "type": "lab",
                "description": "Set up cron jobs to automate backup and log rotation tasks on a Linux VM.",
                "subtasks": [
                    ("Configure VM environment",      1, timezone.make_aware(datetime(2026, 4, 28, 20, 30)), Decimal("0.5"), "not_started"),
                    ("Write backup cron job",         2, timezone.make_aware(datetime(2026, 4, 29, 16, 0)), Decimal("1.0"), "not_started"),
                    ("Write log rotation cron job",   3, timezone.make_aware(datetime(2026, 4, 30, 20, 30)), Decimal("1.0"), "not_started"),
                    ("Screenshot results and submit", 4, timezone.make_aware(datetime(2026, 5,  1, 14, 0)), Decimal("0.5"), "not_started"),
                ],
            },

            # ── WEEK 3 (May 3–9) ───────────────────────────────────────────
            {
                "course": courses["CSC-289"],
                "title": "Capstone: Peer Code Review",
                "due_date": timezone.make_aware(datetime(2026, 5, 6, 17, 0)),
                "priority": "high",
                "status": "not_started",
                "hours": Decimal("4.0"),
                "major": False,
                "type": "lab",
                "description": "Review a classmate's capstone repo and submit structured written feedback.",
                "subtasks": [
                    ("Clone and run partner's project",   1, timezone.make_aware(datetime(2026, 5, 4, 18, 30)), Decimal("0.5"), "not_started"),
                    ("Evaluate code quality & structure", 2, timezone.make_aware(datetime(2026, 5, 5, 10, 0)), Decimal("1.5"), "not_started"),
                    ("Write review document",             3, timezone.make_aware(datetime(2026, 5, 5, 21, 30)), Decimal("1.5"), "not_started"),
                    ("Submit on Canvas",                  4, timezone.make_aware(datetime(2026, 5, 6, 15, 0)), Decimal("0.5"), "not_started"),
                ],
            },
            {
                "course": courses["CSC-113"],
                "title": "ML Model Demo Presentation",
                "due_date": timezone.make_aware(datetime(2026, 5, 7, 14, 0)),
                "priority": "high",
                "status": "not_started",
                "hours": Decimal("5.0"),
                "major": True,
                "type": "presentation",
                "description": "Present a trained classifier to the class. Must include dataset description, model choice rationale, and accuracy results.",
                "subtasks": [
                    ("Select dataset and train model",       1, timezone.make_aware(datetime(2026, 5, 3, 18, 0)), Decimal("2.0"), "not_started"),
                    ("Build slide deck",                     2, timezone.make_aware(datetime(2026, 5, 5, 11, 30)), Decimal("1.5"), "not_started"),
                    ("Rehearse presentation",                3, timezone.make_aware(datetime(2026, 5, 6, 20, 30)), Decimal("1.0"), "not_started"),
                    ("Upload slides to Canvas",              4, timezone.make_aware(datetime(2026, 5, 7, 10, 0)), Decimal("0.5"), "not_started"),
                ],
            },
            {
                "course": courses["CSC-249"],
                "title": "Graph Traversal Problem Set",
                "due_date": timezone.make_aware(datetime(2026, 5, 8, 14, 0)),
                "priority": "medium",
                "status": "not_started",
                "hours": Decimal("4.5"),
                "major": False,
                "type": "problem_set",
                "description": "Implement BFS and DFS. Solve 3 shortest-path problems and explain time complexity.",
                "subtasks": [
                    ("Implement BFS",                     1, timezone.make_aware(datetime(2026, 5, 4, 15, 0)), Decimal("1.0"), "not_started"),
                    ("Implement DFS",                     2, timezone.make_aware(datetime(2026, 5, 5, 15, 0)), Decimal("1.0"), "not_started"),
                    ("Solve shortest-path problems",      3, timezone.make_aware(datetime(2026, 5, 6, 12, 30)), Decimal("1.5"), "not_started"),
                    ("Write complexity analysis",         4, timezone.make_aware(datetime(2026, 5, 7, 17, 0)), Decimal("1.0"), "not_started"),
                ],
            },

            # ── FINALS WEEK (May 10–15) ────────────────────────────────────
            {
                "course": courses["CSC-289"],
                "title": "Capstone Final Submission",
                "due_date": timezone.make_aware(datetime(2026, 5, 13, 17, 0)),
                "priority": "critical",
                "status": "not_started",
                "hours": Decimal("8.0"),
                "major": True,
                "type": "project",
                "description": "Final polished submission: clean repo, full README, demo video, and in-class presentation.",
                "subtasks": [
                    ("Final bug sweep and cleanup",          1, timezone.make_aware(datetime(2026, 5, 10, 20, 0)), Decimal("2.0"), "not_started"),
                    ("Record 5-min demo video",              2, timezone.make_aware(datetime(2026, 5, 11, 14, 0)), Decimal("1.5"), "not_started"),
                    ("Write final README",                   3, timezone.make_aware(datetime(2026, 5, 11, 15, 30)), Decimal("1.5"), "not_started"),
                    ("Push clean repo to GitHub",            4, timezone.make_aware(datetime(2026, 5, 12, 12, 0)), Decimal("0.5"), "not_started"),
                    ("In-class final presentation",          5, timezone.make_aware(datetime(2026, 5, 13, 12, 0)), Decimal("1.5"), "not_started"),
                    ("Submit all materials on Canvas",       6, timezone.make_aware(datetime(2026, 5, 13, 17, 30)), Decimal("1.0"), "not_started"),
                ],
            },
            {
                "course": courses["NOS-125"],
                "title": "Linux Final Exam",
                "due_date": timezone.make_aware(datetime(2026, 5, 14, 12, 0)),
                "priority": "critical",
                "status": "not_started",
                "hours": Decimal("6.0"),
                "major": True,
                "type": "exam",
                "description": "Cumulative practical exam. Topics: scripting, file permissions, cron, SSH, sed/awk, and process management.",
                "subtasks": [
                    ("Review shell scripting notes",          1, timezone.make_aware(datetime(2026, 5, 10, 22, 0)), Decimal("1.5"), "not_started"),
                    ("Review file permissions & ACLs",        2, timezone.make_aware(datetime(2026, 5, 11, 21, 15)), Decimal("1.0"), "not_started"),
                    ("Practice sed/awk exercises",            3, timezone.make_aware(datetime(2026, 5, 12, 14, 30)), Decimal("1.5"), "not_started"),
                    ("Do timed practice exam",                4, timezone.make_aware(datetime(2026, 5, 13, 20, 30)), Decimal("1.5"), "not_started"),
                    ("Final review pass",                     5, timezone.make_aware(datetime(2026, 5, 14, 8,  0)), Decimal("0.5"), "not_started"),
                ],
            },
            {
                "course": courses["CSC-113"],
                "title": "AI Fundamentals Final Exam",
                "due_date": timezone.make_aware(datetime(2026, 5, 15, 10, 0)),
                "priority": "critical",
                "status": "not_started",
                "hours": Decimal("5.0"),
                "major": True,
                "type": "exam",
                "description": "Cumulative exam covering search, ML basics, neural networks, ethics, and NLP.",
                "subtasks": [
                    ("Review search algorithms unit",         1, timezone.make_aware(datetime(2026, 5, 10, 18, 30)), Decimal("1.0"), "not_started"),
                    ("Review ML & neural network notes",      2, timezone.make_aware(datetime(2026, 5, 11, 12, 0)), Decimal("1.5"), "not_started"),
                    ("Review NLP and ethics modules",         3, timezone.make_aware(datetime(2026, 5, 12, 16, 30)), Decimal("1.0"), "not_started"),
                    ("Complete practice quiz set",            4, timezone.make_aware(datetime(2026, 5, 13, 19, 0)), Decimal("1.0"), "not_started"),
                    ("Final review pass",                     5, timezone.make_aware(datetime(2026, 5, 14, 20, 0)), Decimal("0.5"), "not_started"),
                ],
            },
            ]

        if scenario == "testa":
            week_start = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
            testa_assignments = [
                {
                    "course": courses["CSC-289"],
                    "title": "Capstone Sprint: Scheduler Refactor",
                    "due_date": timezone.make_aware(datetime.combine(week_start + timedelta(days=4), time(23, 0))),
                    "priority": "critical",
                    "status": "in_progress",
                    "hours": Decimal("11.5"),
                    "major": True,
                    "type": "project",
                    "description": "Refactor scheduling conflict checks and complete integration tests for the sprint demo.",
                    "subtasks": [
                        ("Audit conflict edge-cases", 1, timezone.make_aware(datetime.combine(week_start + timedelta(days=1), time(20, 30))), Decimal("2.0"), "in_progress"),
                        ("Implement refactor branch", 2, timezone.make_aware(datetime.combine(week_start + timedelta(days=2), time(21, 30))), Decimal("4.0"), "not_started"),
                        ("Write regression tests", 3, timezone.make_aware(datetime.combine(week_start + timedelta(days=3), time(21, 0))), Decimal("3.0"), "not_started"),
                        ("Polish demo narrative", 4, timezone.make_aware(datetime.combine(week_start + timedelta(days=4), time(18, 0))), Decimal("2.5"), "not_started"),
                    ],
                },
                {
                    "course": courses["CSC-249"],
                    "title": "Dynamic Programming Study Packet",
                    "due_date": timezone.make_aware(datetime.combine(week_start + timedelta(days=3), time(16, 0))),
                    "priority": "high",
                    "status": "not_started",
                    "hours": Decimal("7.0"),
                    "major": False,
                    "type": "problem_set",
                    "description": "Complete the optional but graded DP packet and submit worked solutions.",
                    "subtasks": [
                        ("Solve memoization section", 1, timezone.make_aware(datetime.combine(week_start + timedelta(days=1), time(17, 0))), Decimal("2.0"), "not_started"),
                        ("Solve tabulation section", 2, timezone.make_aware(datetime.combine(week_start + timedelta(days=2), time(17, 0))), Decimal("2.0"), "not_started"),
                        ("Review and annotate solutions", 3, timezone.make_aware(datetime.combine(week_start + timedelta(days=3), time(12, 0))), Decimal("1.5"), "not_started"),
                        ("Submit packet", 4, timezone.make_aware(datetime.combine(week_start + timedelta(days=3), time(15, 30))), Decimal("1.5"), "not_started"),
                    ],
                },
                {
                    "course": courses["NOS-125"],
                    "title": "Bash Automation Incident Write-up",
                    "due_date": timezone.make_aware(datetime.combine(week_start + timedelta(days=5), time(14, 0))),
                    "priority": "high",
                    "status": "not_started",
                    "hours": Decimal("5.5"),
                    "major": False,
                    "type": "essay",
                    "description": "Produce a postmortem-style write-up for a broken automation pipeline and remediation plan.",
                    "subtasks": [
                        ("Reproduce failure and capture logs", 1, timezone.make_aware(datetime.combine(week_start + timedelta(days=3), time(19, 0))), Decimal("1.5"), "not_started"),
                        ("Draft incident timeline", 2, timezone.make_aware(datetime.combine(week_start + timedelta(days=4), time(19, 30))), Decimal("1.5"), "not_started"),
                        ("Write remediation section", 3, timezone.make_aware(datetime.combine(week_start + timedelta(days=5), time(10, 30))), Decimal("1.5"), "not_started"),
                        ("Proofread and submit", 4, timezone.make_aware(datetime.combine(week_start + timedelta(days=5), time(13, 30))), Decimal("1.0"), "not_started"),
                    ],
                },
            ]
            assignments.extend(testa_assignments)

        for item in assignments:
            assignment_slot = self._find_open_slot(
                user,
                kind="assignment",
                kind_key="assignment",
                title=item["title"],
                start=item["due_date"],
                duration_hours=item["hours"],
            )

            assignment, _ = Assignment.objects.update_or_create(
                user=user,
                course=item["course"],
                title=item["title"],
                defaults={
                    "description": item["description"],
                    "assignment_type": item["type"],
                    "due_date": assignment_slot.start,
                    "due_time": self._time_label(assignment_slot.start) if hasattr(assignment_slot.start, "strftime") else "",
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
                subtask_slot = self._find_open_slot(
                    user,
                    kind="subtask",
                    kind_key="subtask",
                    title=title,
                    start=due_dt,
                    duration_hours=hours,
                )

                AssignmentSubtask.objects.update_or_create(
                    assignment=assignment,
                    title=title,
                    defaults={
                        "description": "",
                        "step_order": order,
                        "due_date": subtask_slot.start,
                        "due_time": self._time_label(subtask_slot.start),
                        "estimated_hours": hours,
                        "status": status,
                    },
                )

        return {"courses": courses, "assignments": Assignment.objects.filter(user=user)}

    def _seed_schedule_data(self, user, seed_context, scenario="default"):
        if scenario == "emma":
            work_shifts = [
                ("Student Assistant", "Campus Welcome Desk", date(2026, 4, 21), time(8, 0), time(11, 0), "Student Union", "Morning front desk coverage before class.", "#10b981", True, True, "weekly_tuesday"),
                ("Student Assistant", "Campus Welcome Desk", date(2026, 4, 23), time(8, 0), time(11, 0), "Student Union", "Thursday help desk shift.", "#10b981", True, True, "weekly_thursday"),
                ("Student Assistant", "Campus Welcome Desk", date(2026, 4, 28), time(8, 0), time(11, 0), "Student Union", "Usual Tuesday desk shift.", "#10b981", True, True, "weekly_tuesday"),
                ("Student Assistant", "Campus Welcome Desk", date(2026, 4, 30), time(8, 0), time(11, 0), "Student Union", "Usual Thursday desk shift.", "#10b981", True, True, "weekly_thursday"),
                ("Student Assistant", "Campus Welcome Desk", date(2026, 5, 5), time(8, 0), time(11, 0), "Student Union", "Tuesday desk shift between assignments.", "#10b981", True, True, "weekly_tuesday"),
                ("Student Assistant", "Campus Welcome Desk", date(2026, 5, 7), time(8, 0), time(11, 0), "Student Union", "Thursday desk shift before presentation prep.", "#10b981", True, True, "weekly_thursday"),
                ("Student Assistant", "Campus Welcome Desk", date(2026, 5, 12), time(8, 0), time(10, 30), "Student Union", "Shorter finals-week shift.", "#10b981", True, False, ""),
            ]

            recurring_shifts = [
                ("Student Assistant", time(8, 0), time(11, 0), "Student Union Welcome Desk", RecurringWorkShift.RECUR_WEEKLY),
            ]

            personal_events = [
                ("Hair Appointment", date(2026, 4, 24), time(13, 0), time(14, 30), "Downtown Salon", "Trim, blowout, and quick style refresh before finals stretch.", "#EC4899"),
                ("Nail Appointment", date(2026, 5, 2), time(11, 0), time(12, 30), "Polish Bar", "Short gel manicure appointment.", "#EC4899"),
                ("Dentist Cleaning", date(2026, 4, 29), time(9, 0), time(10, 0), "Oak Ridge Dental", "Routine six-month cleaning.", "#F43F5E"),
                ("Grocery Run", date(2026, 4, 26), time(13, 30), time(14, 30), "Trader Joe's", "Pick up quick dinners, fruit, and snacks for the week.", "#06B6D4"),
                ("Coffee with Academic Advisor", date(2026, 5, 5), time(14, 30), time(15, 15), "Campus Coffee House", "Check in about fall registration and transfer credits.", "#F97316"),
                ("BIO-168 Study Group", date(2026, 5, 6), time(15, 0), time(16, 30), "Science Building 214", "Run through organ systems review questions.", "#10B981"),
                ("Church with Family", date(2026, 5, 3), time(10, 30), time(12, 0), "New Hope Church", "Sunday service with family.", "#06B6D4"),
                ("Mother's Day Brunch", date(2026, 5, 10), time(11, 0), time(13, 0), "Mom's House", "Celebrate before finals week gets hectic.", "#F97316"),
                ("Campus Writing Center", date(2026, 5, 11), time(14, 0), time(15, 0), "Learning Commons", "Essay feedback appointment for the final draft.", "#0EA5E9"),
                ("Quick Target Run", date(2026, 5, 12), time(13, 45), time(14, 30), "Target", "Pick up note cards and highlighters for finals.", "#06B6D4"),
                ("Celebrate End of Semester", date(2026, 5, 15), time(21, 0), time(22, 30), "Local Bistro", "Late dinner out after the last final.", "#F97316"),
            ]
        else:
            # ------------------------------------------------------------------ #
            #  WORK SHIFTS                                                         #
            #  Realistic mix: Walmart (Customer Service / Cashier) and             #
            #  Target (seasonal cashier, third employer for variety).              #
            #  Roughly 3–4 shifts per week, varied times.                          #
            # ------------------------------------------------------------------ #
            work_shifts = [
                # ── WEEK 1: Apr 19–25 ──────────────────────────────────────────
                ("Cashier",          "Neighborhood Market", date(2026, 4, 20), time(7,  0), time(13, 0), "Neighborhood Market",         "Morning shift before class.",              "#f59e0b", True,  False, ""),
                ("Customer Service", "Walmart",             date(2026, 4, 23), time(10, 0), time(14, 0), "Walmart",                     "Midday shift – customer desk coverage.",   "#10b981", True,  True,  "weekly_thursday"),
                ("Cashier",          "Walmart",             date(2026, 4, 19), time(14, 0), time(19, 0), "Walmart",                     "Sunday afternoon shift.",                  "#10b981", True,  False, ""),
                ("Cashier",          "Target",              date(2026, 4, 22), time(16, 0), time(21, 0), "Target",                      "Evening shift, check lane 4.",             "#e11d48", True,  False, ""),

                # ── WEEK 2: Apr 26 – May 2 ─────────────────────────────────────
                ("Cashier",          "Neighborhood Market", date(2026, 4, 27), time(7,  0), time(12, 0), "Neighborhood Market",         "Early morning, restock before open.",      "#f59e0b", True,  False, ""),
                ("Customer Service", "Walmart",             date(2026, 4, 28), time(10, 0), time(15, 0), "Walmart",                     "Cover returns desk 10–3.",                 "#10b981", True,  False, ""),
                ("Cashier",          "Target",              date(2026, 4, 30), time(15, 0), time(20, 0), "Target",                      "Midweek evening shift.",                   "#e11d48", True,  False, ""),
                ("Cashier",          "Walmart",             date(2026, 5,  2), time(8,  0), time(13, 0), "Walmart",                     "Saturday morning rush.",                   "#10b981", True,  False, ""),

                # ── WEEK 3: May 3–9 ────────────────────────────────────────────
                ("Cashier",          "Neighborhood Market", date(2026, 5,  3), time(7,  0), time(11, 0), "Neighborhood Market",         "Short Sunday shift.",                      "#f59e0b", True,  False, ""),
                ("Cashier",          "Target",              date(2026, 5,  5), time(16, 0), time(21, 0), "Target",                      "Tuesday evening – semester crunch week.",  "#e11d48", True,  False, ""),
                ("Customer Service", "Walmart",             date(2026, 5,  7), time(11, 0), time(15, 0), "Walmart",                     "Thursday midday, customer service desk.",  "#10b981", True,  True,  "weekly_thursday"),
                ("Cashier",          "Walmart",             date(2026, 5,  9), time(8,  0), time(14, 0), "Walmart",                     "Saturday – last big shift before finals.", "#10b981", True,  False, ""),

                # ── FINALS WEEK: May 10–15 ─────────────────────────────────────
                ("Cashier",          "Target",              date(2026, 5, 10), time(8,  0), time(13, 0), "Target",                      "Sunday morning – lighter finals week.",    "#e11d48", True,  False, ""),
                ("Cashier",          "Neighborhood Market", date(2026, 5, 12), time(6,  0), time(10, 0), "Neighborhood Market",         "Early Tuesday before study block.",        "#f59e0b", True,  False, ""),
            ]

            recurring_shifts = [
                ("Cashier",          time(10, 0), time(14, 0), "Walmart",                     RecurringWorkShift.RECUR_WEEKLY),
                ("Customer Service", time(6,  0), time(10, 0), "Customer Service Desk – Walmart", RecurringWorkShift.RECUR_WEEKLY),
                ("Cashier",          time(16, 0), time(21, 0), "Target",                      RecurringWorkShift.RECUR_WEEKLY),
            ]

            # ------------------------------------------------------------------ #
            #  PERSONAL EVENTS                                                     #
            #  Mix: social, gym, appointments, self-care, academic milestones      #
            # ------------------------------------------------------------------ #
            personal_events = [
                # ── WEEK 1: Apr 19–25 ──────────────────────────────────────────
                ("Doxie's Pre-Birthday Party",        date(2026, 4, 23), time(18, 0), time(20, 0), "209",                      "party party",                                       "#06b6d4"),
                ("Gym – Leg Day",                     date(2026, 4, 19), time(9,  0), time(10,30), "Planet Fitness",           "Squats, lunges, leg press.",                        "#8b5cf6"),
                ("Gym – Push Day",                    date(2026, 4, 21), time(8,  0), time(9,  30), "Planet Fitness",          "Chest/shoulders/triceps.",                          "#8b5cf6"),
                ("Study Group – CSC-249",             date(2026, 4, 20), time(15, 0), time(17, 0), "Campus Library Room 2B",   "Hash table prep with Haylee and Aryan.",            "#1E90FF"),
                ("Grocery Run",                       date(2026, 4, 22), time(11, 0), time(12, 0), "Walmart Neighborhood Mkt", "Weekly grocery haul.",                              "#64748b"),
                ("Hair Appointment",                  date(2026, 4, 25), time(13, 0), time(15, 0), "Salon",                    "Trim and deep condition.",                          "#f472b6"),

                # ── WEEK 2: Apr 26 – May 2 ─────────────────────────────────────
                ("Gym – Pull Day",                    date(2026, 4, 26), time(9,  0), time(10,30), "Planet Fitness",           "Back, biceps, rear delts.",                        "#8b5cf6"),
                ("Gym – Push Day",                    date(2026, 4, 28), time(8,  0), time(9,  30), "Planet Fitness",          "Bench press focus.",                               "#8b5cf6"),
                ("Gym – Leg Day",                     date(2026, 4, 30), time(9,  0), time(10,30), "Planet Fitness",           "Romanian deadlift variation.",                     "#8b5cf6"),
                ("Coffee with James",                 date(2026, 4, 27), time(13, 0), time(14, 0), "Starbucks on Main",        "Catch-up + capstone commiseration.",               "#f59e0b"),
                ("Doctor Appointment",                date(2026, 4, 29), time(10, 0), time(11, 0), "Family Health Clinic",     "Annual checkup.",                                  "#ef4444"),
                ("Study Group – CSC-289",             date(2026, 4, 28), time(17, 30),time(19, 0), "Campus Library",           "Capstone alignment session with group.",           "#228B22"),
                ("Laundry + Meal Prep",               date(2026, 5,  2), time(14, 0), time(16, 0), "Home",                    "Batch cooking for the week.",                      "#64748b"),

                # ── WEEK 3: May 3–9 ────────────────────────────────────────────
                ("Gym – Full Body",                   date(2026, 5,  3), time(11, 30), time(13, 0), "Planet Fitness",          "Deload week – lighter weight.",                    "#8b5cf6"),
                ("Gym – Upper Body",                  date(2026, 5,  5), time(8,  0), time(9,  30), "Planet Fitness",          "Pull-ups, rows, curls.",                           "#8b5cf6"),
                ("Study Group – CSC-113",             date(2026, 5,  4), time(16, 0), time(18, 0), "Campus Library Room 1A",   "ML model review before presentation.",             "#DC143C"),
                ("Dinner with Family",                date(2026, 5,  6), time(18, 30),time(20, 30), "Mom's house",             "Weekly family dinner.",                            "#f59e0b"),
                ("Capstone Dry Run",                  date(2026, 5,  8), time(17, 0), time(18, 30), "Campus Lab 204",          "Practice final presentation with classmates.",     "#228B22"),
                ("Pharmacy + Errands",                date(2026, 5,  7), time(15, 30), time(16, 30), "CVS + Target",            "Prescriptions and supplies.",                      "#64748b"),

                # ── FINALS WEEK: May 10–15 ─────────────────────────────────────
                ("Light Gym – Stress Relief",         date(2026, 5, 10), time(14, 0), time(15, 0), "Planet Fitness",           "30 min cardio only – don't overdo it.",            "#8b5cf6"),
                ("Study Session – NOS-125 Exam Prep", date(2026, 5, 11), time(18, 0), time(21, 0), "Home desk",                "Timed practice run of shell scripting problems.",  "#FFD700"),
                ("Capstone Final Presentation Day",   date(2026, 5, 13), time(9,  0), time(12, 0), "Campus Auditorium",        "The big one. Breathe.",                            "#228B22"),
                ("Celebrate – End of Semester!",      date(2026, 5, 15), time(19, 0), time(22, 0), "TBD",                      "Dinner out with Haylee, James, Aryan.",            "#06b6d4"),
            ]

        for (job_title, employer_name, shift_date, start_time_value, end_time_value,
             location, notes, color, is_confirmed, is_recurring, recurrence_pattern) in work_shifts:
            shift_slot = self._find_open_slot(
                user,
                kind="work shift",
                kind_key="work_shift",
                title=employer_name or job_title or "Work Shift",
                start=timezone.make_aware(datetime.combine(shift_date, start_time_value)),
                end=timezone.make_aware(datetime.combine(shift_date, end_time_value)),
            )
            WorkShift.objects.update_or_create(
                user=user,
                employer_name=employer_name,
                shift_date=timezone.localtime(shift_slot.start).date(),
                defaults={
                    "job_title": job_title,
                    "start_time": timezone.localtime(shift_slot.start).time().replace(microsecond=0),
                    "end_time": timezone.localtime(shift_slot.end).time().replace(microsecond=0),
                    "shift_start": shift_slot.start,
                    "shift_end": shift_slot.end,
                    "location": location,
                    "notes": notes,
                    "color_hex": color,
                    "is_confirmed": is_confirmed,
                    "is_recurring": is_recurring,
                    "recurrence_pattern": recurrence_pattern,
                },
            )

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

        for (title, event_date, start_t, end_t, location, description, color) in personal_events:
            event_slot = self._find_open_slot(
                user,
                kind="personal event",
                kind_key="personal_event",
                title=title,
                start=timezone.make_aware(datetime.combine(event_date, start_t)),
                end=timezone.make_aware(datetime.combine(event_date, end_t)),
            )
            PersonalEvent.objects.update_or_create(
                user=user,
                title=title,
                event_date=timezone.localtime(event_slot.start).date(),
                defaults={
                    "description": description,
                    "start_time": timezone.localtime(event_slot.start).time().replace(microsecond=0),
                    "end_time": timezone.localtime(event_slot.end).time().replace(microsecond=0),
                    "location": location,
                    "color_hex": color,
                },
            )

        if scenario == "emma":
            RecurringPersonalEvent.objects.update_or_create(
                user=user,
                title="Dinner with Family",
                start_date=date(2026, 1, 13),
                defaults={
                    "description": "Daily family dinner block Emma keeps protected throughout the semester.",
                    "start_time": time(17, 0),
                    "end_time": time(19, 0),
                    "location": "Mom's House",
                    "recurrence_pattern": RecurringPersonalEvent.RECUR_WEEKLY,
                    "weekdays": "0,1,2,3,4,5,6",
                    "monthly_day": None,
                    "is_active": True,
                },
            )

        # ------------------------------------------------------------------ #
        #  TIME BLOCKS  (linked to assignments)                                #
        # ------------------------------------------------------------------ #
        assignments_qs = seed_context["assignments"]
        if scenario == "emma":
            block_map = {
                "Annotated Bibliography": ("Annotated bibliography research block", datetime(2026, 4, 22, 15, 30), datetime(2026, 4, 22, 17, 0), "Campus library", "Finish the remaining source annotations before dinner."),
                "Polynomial Functions Problem Set": ("Math homework problem block", datetime(2026, 4, 23, 15, 30), datetime(2026, 4, 23, 17, 0), "Math lab", "Work through the tougher graphing problems with tutor notes."),
                "Nervous System Lab Report": ("BIO lab report drafting", datetime(2026, 4, 27, 15, 0), datetime(2026, 4, 27, 17, 0), "Science building study lounge", "Draft methods and results while the lab details are still fresh."),
                "Marketing Pitch Deck": ("Pitch deck design session", datetime(2026, 4, 28, 19, 15), datetime(2026, 4, 28, 20, 45), "Home desk", "Polish slides after dinner and tighten speaker notes."),
                "Homeostasis Group Presentation": ("BIO presentation rehearsal", datetime(2026, 5, 6, 13, 0), datetime(2026, 5, 6, 14, 30), "Science building classroom", "Meet the group before the afternoon study session."),
                "Research Essay Final Draft": ("Essay revision deep work", datetime(2026, 5, 10, 14, 30), datetime(2026, 5, 10, 16, 30), "Home desk", "Two uninterrupted hours for thesis revision and paragraph cleanup."),
                "Business Ethics Case Study": ("Case study writing block", datetime(2026, 5, 9, 10, 30), datetime(2026, 5, 9, 12, 0), "Campus library", "Draft the analysis before Sunday family plans."),
                "Precalculus Final Exam": ("Final exam practice set", datetime(2026, 5, 12, 15, 0), datetime(2026, 5, 12, 16, 30), "Home desk", "Work through a timed practice set before dinner."),
                "Anatomy Practical Final": ("Anatomy flashcard lab", datetime(2026, 5, 13, 13, 30), datetime(2026, 5, 13, 15, 0), "Science Building 214", "Review diagrams and structures with classmates."),
            }
        else:
            block_map = {
            "Capstone: StudyStream":        ("Capstone dashboard polish",        datetime(2026, 4, 22, 13, 0), datetime(2026, 4, 22, 15, 0), "Home office",       "Focus on workload widgets and demo flow."),
            "Hash Table Implementation":    ("Hash table implementation block",  datetime(2026, 4, 21, 19,30), datetime(2026, 4, 21, 21, 0), "Campus library",    "Finish collision handling and tests."),
            "AI Ethics Reflection Paper":   ("AI Ethics paper draft session",    datetime(2026, 4, 27, 20, 0), datetime(2026, 4, 27, 22, 0), "Home desk",         "Draft body paragraphs in one sitting."),
            "Sorting Algorithm Comparison": ("Sorting algo coding block",        datetime(2026, 4, 28, 15, 0), datetime(2026, 4, 28, 17, 0), "Campus lab",        "Implement merge sort and quicksort."),
            "Linux Final Project":          ("Linux project shell scripting",    datetime(2026, 4, 21, 17,30), datetime(2026, 4, 21, 19, 0), "Home desk",         "Finish automation scripts."),
            "ML Model Demo Presentation":   ("ML presentation prep block",       datetime(2026, 5,  5, 13, 0), datetime(2026, 5,  5, 15, 0), "Home desk",         "Build slide deck and rehearse."),
            "Capstone Final Submission":    ("Final capstone cleanup block",     datetime(2026, 5, 10, 15, 0), datetime(2026, 5, 10, 18, 0), "Home office",       "Bug sweep, README, and demo video."),
            "AI Fundamentals Final Exam":   ("AI exam review session",           datetime(2026, 5, 12, 18, 0), datetime(2026, 5, 12, 20,30), "Campus library",    "Timed practice questions."),
            "Linux Final Exam":             ("Linux exam timed practice",        datetime(2026, 5, 13, 14, 0), datetime(2026, 5, 13, 16,30), "Home desk",         "Full timed mock exam."),
            "Graph Traversal Problem Set":  ("BFS/DFS coding session",           datetime(2026, 5,  6, 16, 0), datetime(2026, 5,  6, 18, 0), "Campus lab",        "Implement BFS and DFS, verify edge cases."),
            }

        if scenario == "testa":
            week_start = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
            block_map.update(
                {
                    "Capstone Sprint: Scheduler Refactor": (
                        "Capstone refactor focus block",
                        datetime.combine(week_start + timedelta(days=1), time(19, 0)),
                        datetime.combine(week_start + timedelta(days=1), time(20, 30)),
                        "Home office",
                        "Only one planned block to leave room for auto task breakdown suggestions.",
                    ),
                    "Dynamic Programming Study Packet": (
                        "DP packet starter block",
                        datetime.combine(week_start + timedelta(days=2), time(18, 30)),
                        datetime.combine(week_start + timedelta(days=2), time(20, 0)),
                        "Campus library",
                        "Intentionally limited scheduling so remaining subtasks stay unscheduled.",
                    ),
                }
            )

        for assignment_title, (block_title, start_dt, end_dt, location, notes) in block_map.items():
            a = assignments_qs.filter(title=assignment_title).first()
            if a:
                block_slot = self._find_open_slot(
                    user,
                    kind="time block",
                    kind_key="time_block",
                    title=block_title,
                    start=timezone.make_aware(start_dt),
                    end=timezone.make_aware(end_dt),
                )
                TimeBlock.objects.update_or_create(
                    user=user,
                    title=block_title,
                    start_time=block_slot.start,
                    defaults={
                        "assignment": a,
                        "end_time": block_slot.end,
                        "location": location,
                        "status": "scheduled",
                        "notes": notes,
                        "is_recurring": False,
                        "recurrence": "",
                    },
                )

        # ------------------------------------------------------------------ #
        #  WORKLOAD ANALYSIS  (one entry per week)                             #
        # ------------------------------------------------------------------ #
        if scenario == "emma":
            workload_weeks = [
                (
                    date(2026, 4, 20), 17, Decimal("13.00"), Decimal("6.00"), Decimal("17.00"), Decimal("96.00"),
                    Decimal("0.188"), WorkloadAnalysis.STATUS_GREEN, 4, 0, False, False,
                    [
                        {"action": "stay_consistent", "message": "Short daily blocks will keep the research and math work manageable."},
                    ],
                    False, None,
                ),
                (
                    date(2026, 4, 27), 18, Decimal("13.00"), Decimal("6.00"), Decimal("13.50"), Decimal("96.00"),
                    Decimal("0.141"), WorkloadAnalysis.STATUS_GREEN, 4, 0, False, False,
                    [
                        {"action": "protect_dinner", "message": "Daily family dinners are already blocked, so use mid-afternoon openings for schoolwork."},
                    ],
                    False, None,
                ),
                (
                    date(2026, 5, 4), 19, Decimal("13.00"), Decimal("6.00"), Decimal("17.50"), Decimal("95.00"),
                    Decimal("0.184"), WorkloadAnalysis.STATUS_YELLOW, 4, 1, True, False,
                    [
                        {"action": "frontload_essay", "message": "Start the research essay revisions before finals week so it does not collide with exam prep."},
                        {"action": "keep_short_blocks", "message": "Use quick review sessions between appointments instead of waiting for one big evening slot."},
                    ],
                    False, None,
                ),
                (
                    date(2026, 5, 11), 20, Decimal("8.00"), Decimal("2.50"), Decimal("19.50"), Decimal("104.00"),
                    Decimal("0.188"), WorkloadAnalysis.STATUS_YELLOW, 4, 3, True, False,
                    [
                        {"action": "finals_focus", "message": "Two finals land back-to-back. Keep errands light and preserve the afternoon study blocks."},
                    ],
                    False, None,
                ),
            ]
        else:
            workload_weeks = [
            # (week_start, week_num, class_h, work_h, assign_h, avail_h, ratio, status, assign_ct, major_ct, cluster, overloaded, actions, alert, alert_dt)
            (
                date(2026, 4, 20), 17, Decimal("15.00"), Decimal("11.00"), Decimal("29.00"), Decimal("87.00"),
                Decimal("0.333"), WorkloadAnalysis.STATUS_GREEN, 4, 3, True, False,
                [
                    {"action": "start_early",      "message": "Major deadlines cluster late in the week. Start now."},
                    {"action": "protect_study_time","message": "Keep evening time blocks open for assignment work."},
                ],
                False, None,
            ),
            (
                date(2026, 4, 27), 18, Decimal("15.00"), Decimal("20.00"), Decimal("46.00"), Decimal("77.00"),
                Decimal("0.597"), WorkloadAnalysis.STATUS_YELLOW, 6, 3, False, False,
                [
                    {"action": "plan_ahead", "message": "Heavy week ahead. Break larger assignments into smaller sessions."},
                ],
                True, timezone.make_aware(datetime(2026, 4, 17, 8, 0)),
            ),
            (
                date(2026, 5, 4), 19, Decimal("15.00"), Decimal("16.00"), Decimal("38.00"), Decimal("83.00"),
                Decimal("0.524"), WorkloadAnalysis.STATUS_YELLOW, 5, 2, True, False,
                [
                    {"action": "presentation_prep", "message": "Presentation due Thursday – block rehearsal time Wednesday evening."},
                    {"action": "start_exam_review",  "message": "Finals start next week. Begin review passes now."},
                ],
                False, None,
            ),
            (
                date(2026, 5, 11), 20, Decimal("0.00"), Decimal("6.00"), Decimal("19.00"), Decimal("106.00"),
                Decimal("0.179"), WorkloadAnalysis.STATUS_GREEN, 3, 3, True, False,
                [
                    {"action": "finals_focus",    "message": "Finals week. Minimize work hours and protect study blocks."},
                    {"action": "rest_scheduled",  "message": "You have capacity – use it for recovery between exams."},
                ],
                False, None,
            ),
            ]

        for (week_start, week_num, class_h, work_h, assign_h, avail_h, ratio,
             status, assign_ct, major_ct, cluster, overloaded, actions, alert, alert_dt) in workload_weeks:
            WorkloadAnalysis.objects.update_or_create(
                user=user,
                week_start_date=week_start,
                defaults={
                    "week_number": week_num,
                    "year": 2026,
                    "total_class_hours": class_h,
                    "total_work_hours": work_h,
                    "total_assignment_hours": assign_h,
                    "available_study_hours": avail_h,
                    "utilization_ratio": ratio,
                    "week_status": status,
                    "assignment_count": assign_ct,
                    "major_assignment_count": major_ct,
                    "deadline_cluster_detected": cluster,
                    "is_overloaded": overloaded,
                    "recommended_actions": actions,
                    "alert_sent": alert,
                    "alert_sent_at": alert_dt,
                },
            )

    def _apply_testa_overload_tuning(self, user):
        current_week_start = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
        iso_year, iso_week, _ = current_week_start.isocalendar()

        WorkloadAnalysis.objects.update_or_create(
            user=user,
            week_start_date=current_week_start,
            defaults={
                "week_number": iso_week,
                "year": iso_year,
                "total_class_hours": Decimal("15.00"),
                "total_work_hours": Decimal("19.00"),
                "total_assignment_hours": Decimal("52.00"),
                "available_study_hours": Decimal("78.00"),
                "utilization_ratio": Decimal("0.667"),
                "week_status": WorkloadAnalysis.STATUS_RED,
                "assignment_count": 8,
                "major_assignment_count": 3,
                "deadline_cluster_detected": True,
                "is_overloaded": True,
                "recommended_actions": [
                    {
                        "action": "task_breakdown",
                        "message": "Break major assignments into 60-90 minute chunks and place them into open weeknight slots.",
                    },
                    {
                        "action": "protect_open_windows",
                        "message": "Keep at least two unscheduled windows this week so the planner can auto-place urgent subtasks.",
                    },
                ],
                "alert_sent": True,
                "alert_sent_at": timezone.now(),
            },
        )