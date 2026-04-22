from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from accounts.models import Assignment, Course, Profile, Semester
from core.models import PersonalEvent
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


class WorkloadPreferencesTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="planner2", password="testpass123", email="planner2@example.com")
		self.client.force_login(self.user)

	def test_settings_view_saves_workload_preferences(self):
		response = self.client.post(
			"/accounts/settings/",
			{
				"sleep_hours_per_night": "8.0",
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
