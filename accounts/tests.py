from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from accounts.models import Assignment, Course, Profile, Semester
from accounts.models import AssignmentSubtask
from core.models import PersonalEvent, WorkShift
from home.workload_engine import recompute_and_persist_workload


class ScheduleConflictApiTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="planner", password="testpass123")
		self.client.force_login(self.user)
		self.semester = Semester.objects.create(user=self.user, name="Spring 2026", is_active=True)
		self.course = Course.objects.create(
			user=self.user,
			semester=self.semester,
			course_code="CTS289",
			course_name="Capstone",
			color_hex="#1E90FF",
		)

	def test_assignment_create_returns_conflict_payload_and_can_replace_personal_event(self):
		event_date = timezone.localdate() + timedelta(days=2)
		personal_event = PersonalEvent.objects.create(
			user=self.user,
			title="Doctor Appointment",
			event_date=event_date,
			start_time=time(13, 0),
			end_time=time(14, 0),
		)

		response = self.client.post(
			"/accounts/api/assignments/create/",
			{
				"course": self.course.id,
				"title": "Project Work",
				"due_date": f"{event_date.isoformat()}T13:00",
				"estimated_hours": "1",
			},
		)

		self.assertEqual(response.status_code, 409)
		payload = response.json()
		self.assertEqual(payload["conflict"]["kind_key"], "personal_event")
		self.assertTrue(payload["conflict"]["replaceable"])
		self.assertEqual(payload["requested"]["local_ref"], "assignment")
		self.assertIsNotNone(payload["suggestion"])

		replace_response = self.client.post(
			"/accounts/api/assignments/create/",
			{
				"course": self.course.id,
				"title": "Project Work",
				"due_date": f"{event_date.isoformat()}T13:00",
				"estimated_hours": "1",
				"replace_conflict": "on",
				"conflict_kind": payload["conflict"]["kind_key"],
				"conflict_id": payload["conflict"]["id"],
			},
		)

		self.assertEqual(replace_response.status_code, 200)
		self.assertFalse(PersonalEvent.objects.filter(pk=personal_event.id).exists())
		self.assertTrue(Assignment.objects.filter(user=self.user, title="Project Work").exists())

	def test_personal_event_edit_returns_assignment_conflict_payload(self):
		assignment_start = timezone.make_aware(
			datetime.combine(timezone.localdate() + timedelta(days=3), time(15, 0)),
			timezone.get_current_timezone(),
		)
		assignment = Assignment.objects.create(
			user=self.user,
			course=self.course,
			title="Midterm Prep",
			due_date=assignment_start,
			estimated_hours=Decimal("2.0"),
		)
		event = PersonalEvent.objects.create(
			user=self.user,
			title="Coffee",
			event_date=assignment_start.date(),
			start_time=time(18, 0),
			end_time=time(19, 0),
		)

		response = self.client.post(
			f"/home/api/personal-events/{event.id}/edit/",
			{
				"title": "Coffee",
				"event_date": assignment_start.date().isoformat(),
				"start_time": "16:00",
				"end_time": "17:00",
			},
		)

		self.assertEqual(response.status_code, 409)
		payload = response.json()
		self.assertEqual(payload["conflict"]["kind_key"], "assignment")
		self.assertTrue(payload["conflict"]["replaceable"])
		self.assertEqual(payload["requested"]["local_ref"], "personal_event")
		self.assertIsNotNone(payload["suggestion"])
		self.assertEqual(payload["suggestion"]["local_ref"], "personal_event")
		self.assertTrue(Assignment.objects.filter(pk=assignment.id).exists())

	def test_assignment_conflict_suggestion_avoids_sleep_window(self):
		Profile.objects.update_or_create(
			user=self.user,
			defaults={
				"sleep_hours_per_night": Decimal("8.0"),
				"sleep_start_time": time(22, 0),
				"sleep_end_time": time(6, 0),
			},
		)

		event_date = timezone.localdate() + timedelta(days=4)
		PersonalEvent.objects.create(
			user=self.user,
			title="Night Event",
			event_date=event_date,
			start_time=time(21, 0),
			end_time=time(22, 0),
		)

		response = self.client.post(
			"/accounts/api/assignments/create/",
			{
				"course": self.course.id,
				"title": "Late Study",
				"due_date": f"{event_date.isoformat()}T21:00",
				"estimated_hours": "1",
			},
		)

		self.assertEqual(response.status_code, 409)
		payload = response.json()
		suggestion = payload.get("suggestion")
		self.assertIsNotNone(suggestion)

		suggested_dt = timezone.localtime(datetime.fromisoformat(suggestion["start"]))
		self.assertNotEqual(suggested_dt.hour, 22)
		self.assertNotEqual(suggested_dt.hour, 23)

	def test_assignment_create_rejects_overlap_with_work_shift(self):
		shift_date = timezone.localdate() + timedelta(days=5)
		shift_start = timezone.make_aware(
			datetime.combine(shift_date, time(9, 0)),
			timezone.get_current_timezone(),
		)
		shift_end = timezone.make_aware(
			datetime.combine(shift_date, time(11, 0)),
			timezone.get_current_timezone(),
		)
		WorkShift.objects.create(
			user=self.user,
			employer_name="Campus Desk",
			job_title="Campus Desk",
			shift_date=shift_date,
			start_time=time(9, 0),
			end_time=time(11, 0),
			shift_start=shift_start,
			shift_end=shift_end,
		)

		response = self.client.post(
			"/accounts/api/assignments/create/",
			{
				"course": self.course.id,
				"title": "Test4",
				"due_date": f"{shift_date.isoformat()}T09:30",
				"estimated_hours": "1.5",
			},
		)

		self.assertEqual(response.status_code, 409)
		payload = response.json()
		self.assertEqual(payload["conflict"]["kind_key"], "work_shift")
		self.assertFalse(Assignment.objects.filter(user=self.user, title="Test4").exists())

	def test_assignment_edit_rejects_overlap_with_work_shift(self):
		shift_date = timezone.localdate() + timedelta(days=6)
		shift_start = timezone.make_aware(
			datetime.combine(shift_date, time(13, 0)),
			timezone.get_current_timezone(),
		)
		shift_end = timezone.make_aware(
			datetime.combine(shift_date, time(15, 0)),
			timezone.get_current_timezone(),
		)
		WorkShift.objects.create(
			user=self.user,
			employer_name="Library",
			job_title="Library",
			shift_date=shift_date,
			start_time=time(13, 0),
			end_time=time(15, 0),
			shift_start=shift_start,
			shift_end=shift_end,
		)

		assignment = Assignment.objects.create(
			user=self.user,
			course=self.course,
			title="Existing Task",
			due_date=timezone.make_aware(
				datetime.combine(shift_date, time(16, 0)),
				timezone.get_current_timezone(),
			),
			estimated_hours=Decimal("1.0"),
		)

		response = self.client.post(
			f"/accounts/api/assignments/{assignment.id}/edit/",
			{
				"course": self.course.id,
				"title": "Existing Task",
				"due_date": f"{shift_date.isoformat()}T13:30",
				"estimated_hours": "1.0",
			},
		)

		self.assertEqual(response.status_code, 409)
		payload = response.json()
		self.assertEqual(payload["conflict"]["kind_key"], "work_shift")
		assignment.refresh_from_db()
		self.assertEqual(timezone.localtime(assignment.due_date).hour, 16)


class WorkloadPreferencesTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="planner2", password="testpass123", email="planner2@example.com")
		self.client.force_login(self.user)

	def test_settings_view_creates_profile_with_default_sleep_window(self):
		response = self.client.get("/accounts/settings/")
		self.assertEqual(response.status_code, 200)

		profile = Profile.objects.get(user=self.user)
		self.assertEqual(profile.sleep_start_time, time(23, 0))
		self.assertEqual(profile.sleep_end_time, time(7, 0))
		self.assertEqual(profile.sleep_hours_per_night, Decimal("8.0"))

	def test_settings_view_saves_workload_preferences(self):
		response = self.client.post(
			"/accounts/settings/",
			{
				"sleep_start_time": "22:30",
				"sleep_end_time": "06:30",
				"personal_time_hours_per_week": "12.0",
				"family_time_hours_per_week": "18.0",
				"commute_time_hours_per_week": "7.0",
			},
		)

		self.assertEqual(response.status_code, 302)
		profile = Profile.objects.get(user=self.user)
		self.assertEqual(profile.sleep_hours_per_night, Decimal("8.0"))
		self.assertEqual(profile.personal_time_hours_per_week, Decimal("12.0"))
		self.assertEqual(profile.family_time_hours_per_week, Decimal("18.0"))
		self.assertEqual(profile.commute_time_hours_per_week, Decimal("7.0"))

	def test_workload_uses_profile_capacity_preferences(self):
		Profile.objects.update_or_create(
			user=self.user,
			defaults={
				"sleep_hours_per_night": Decimal("8.0"),
				"personal_time_hours_per_week": Decimal("14.0"),
				"family_time_hours_per_week": Decimal("14.0"),
				"commute_time_hours_per_week": Decimal("7.0"),
			},
		)

		payload = recompute_and_persist_workload(self.user, weeks=1)
		summary = payload["summary"]
		self.assertEqual(summary["available_study_hours"], 77.0)

	def test_workload_uses_sleep_window_when_present(self):
		Profile.objects.update_or_create(
			user=self.user,
			defaults={
				"sleep_hours_per_night": Decimal("4.0"),
				"sleep_start_time": time(22, 0),
				"sleep_end_time": time(6, 0),
				"personal_time_hours_per_week": Decimal("0.0"),
				"family_time_hours_per_week": Decimal("0.0"),
				"commute_time_hours_per_week": Decimal("0.0"),
			},
		)

		payload = recompute_and_persist_workload(self.user, weeks=1)
		summary = payload["summary"]
		self.assertEqual(summary["available_study_hours"], 112.0)

	def test_settings_view_rejects_sleep_window_over_16_hours(self):
		response = self.client.post(
			"/accounts/settings/",
			{
				"sleep_start_time": "23:00",
				"sleep_end_time": "19:00",
				"personal_time_hours_per_week": "12.0",
				"family_time_hours_per_week": "18.0",
				"commute_time_hours_per_week": "7.0",
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Sleep window cannot exceed 16 hours per night.")

	def test_workload_clamps_legacy_sleep_values_over_16_hours(self):
		Profile.objects.update_or_create(
			user=self.user,
			defaults={
				"sleep_hours_per_night": Decimal("20.0"),
				"sleep_start_time": time(12, 0),
				"sleep_end_time": time(8, 0),
				"personal_time_hours_per_week": Decimal("0.0"),
				"family_time_hours_per_week": Decimal("0.0"),
				"commute_time_hours_per_week": Decimal("0.0"),
			},
		)

		payload = recompute_and_persist_workload(self.user, weeks=1)
		summary = payload["summary"]
		self.assertEqual(summary["available_study_hours"], 56.0)

	def test_online_course_weekly_hours_count_in_workload(self):
		semester = Semester.objects.create(user=self.user, name="Fall 2026", is_active=True)
		Course.objects.create(
			user=self.user,
			semester=semester,
			course_code="ONLINE101",
			course_name="Online Seminar",
			meeting_times="",
			weekly_study_hours=Decimal("6.0"),
		)

		payload = recompute_and_persist_workload(self.user, weeks=1)
		summary = payload["summary"]
		self.assertEqual(summary["total_class_hours"], 6.0)

	def test_workload_includes_subtask_estimated_hours(self):
		semester = Semester.objects.create(user=self.user, name="Spring 2027", is_active=True)
		course = Course.objects.create(
			user=self.user,
			semester=semester,
			course_code="CTS390",
			course_name="Systems",
			meeting_times="",
			weekly_study_hours=Decimal("0.0"),
		)
		assignment = Assignment.objects.create(
			user=self.user,
			course=course,
			title="Project",
			due_date=timezone.now() + timedelta(days=2),
			estimated_hours=Decimal("2.0"),
			status="in_progress",
			contributes_to_workload=True,
		)
		AssignmentSubtask.objects.create(
			assignment=assignment,
			title="Step 1",
			due_date=timezone.now() + timedelta(days=1),
			estimated_hours=Decimal("1.5"),
			status="in_progress",
		)

		payload = recompute_and_persist_workload(self.user, weeks=1)
		summary = payload["summary"]
		self.assertEqual(summary["total_assignment_hours"], 3.5)


class LoginOnboardingRedirectTests(TestCase):
	def test_first_login_redirects_new_user_to_settings(self):
		User.objects.create_user(username="newplanner", password="testpass123", email="newplanner@example.com")

		response = self.client.post(
			"/accounts/login/",
			{"username": "newplanner", "password": "testpass123"},
		)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, "/accounts/settings/?onboarding=1")

	def test_login_redirects_to_home_when_profile_exists(self):
		user = User.objects.create_user(username="returning", password="testpass123", email="returning@example.com")
		Profile.objects.create(user=user, display_name="Returning", avatar_text="R")

		response = self.client.post(
			"/accounts/login/",
			{"username": "returning", "password": "testpass123"},
		)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, "/home/")
