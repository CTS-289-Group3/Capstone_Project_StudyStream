from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from accounts.models import Assignment, AssignmentSubtask, Course, Semester
from core.models import PersonalEvent, WorkShift


class DashboardCalendarTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="student", password="testpass123")
		self.client.force_login(self.user)
		self.semester = Semester.objects.create(user=self.user, name="Spring 2026", is_active=True)
		self.course = Course.objects.create(
			user=self.user,
			semester=self.semester,
			course_code="CTS289",
			course_name="Capstone",
			color_hex="#1E90FF",
		)

	def test_legacy_dashboard_redirects_to_home(self):
		response = self.client.get("/home/dashboard/")

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response["Location"], "/home/")

	def test_home_view_embeds_assignment_subtasks(self):
		assignment_due = timezone.now() + timedelta(days=3)
		assignment = Assignment.objects.create(
			user=self.user,
			course=self.course,
			title="Project Milestone",
			due_date=assignment_due,
		)
		subtask_start = timezone.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=1)
		AssignmentSubtask.objects.create(
			assignment=assignment,
			title="Draft outline",
			due_date=subtask_start,
			estimated_hours=Decimal("2.5"),
		)

		response = self.client.get("/home/")

		self.assertEqual(response.status_code, 200)
		assignments = response.context["assignments_json"]
		self.assertIn("Draft outline", assignments)
		self.assertIn("subtasks", assignments)

	def test_subtask_list_api_includes_parent_course_color(self):
		assignment = Assignment.objects.create(
			user=self.user,
			course=self.course,
			title="Project Milestone",
			due_date=timezone.now() + timedelta(days=3),
		)
		subtask = AssignmentSubtask.objects.create(
			assignment=assignment,
			title="Draft outline",
			due_date=timezone.now() + timedelta(days=1),
		)

		response = self.client.get(f"/accounts/api/assignments/{assignment.id}/subtasks/")

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(payload["subtasks"][0]["id"], subtask.id)
		self.assertEqual(payload["subtasks"][0]["course_color"], self.course.color_hex)

	def test_workload_summary_api_returns_alerts(self):
		Assignment.objects.create(
			user=self.user,
			course=self.course,
			title="Very Heavy Week",
			due_date=timezone.now() + timedelta(days=1),
			estimated_hours=Decimal("90.0"),
			status="not_started",
		)

		response = self.client.get("/home/api/workload/summary/")

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(payload["summary"]["status"], "RED")
		self.assertTrue(payload["alerts"])
		self.assertEqual(payload["alerts"][0]["type"], "red_week")

	def test_assignment_create_rejects_overlap_with_personal_event(self):
		event_date = timezone.localdate() + timedelta(days=2)
		PersonalEvent.objects.create(
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
		self.assertIn("Only one item can occupy a time block.", response.json()["error"])
		self.assertFalse(Assignment.objects.filter(user=self.user, title="Project Work").exists())

	def test_assignment_edit_rejects_internal_overlap_with_subtask_payload(self):
		assignment = Assignment.objects.create(
			user=self.user,
			course=self.course,
			title="Capstone Build",
			due_date=timezone.now() + timedelta(days=3),
			estimated_hours=Decimal("1.0"),
		)

		target_date = (timezone.localdate() + timedelta(days=4)).isoformat()
		response = self.client.post(
			f"/accounts/api/assignments/{assignment.id}/edit/",
			{
				"course": self.course.id,
				"title": "Capstone Build",
				"due_date": f"{target_date}T10:00",
				"estimated_hours": "1",
				"subtask_title[]": ["Draft README"],
				"subtask_due_date[]": [f"{target_date}T10:30"],
				"subtask_due_time[]": [""],
				"subtask_estimated_hours[]": ["1"],
			},
		)

		self.assertEqual(response.status_code, 409)
		self.assertIn("Only one item can occupy a time block.", response.json()["error"])

	def test_subtask_edit_rejects_overlap_with_work_shift(self):
		assignment = Assignment.objects.create(
			user=self.user,
			course=self.course,
			title="Research Notes",
			due_date=timezone.now() + timedelta(days=5),
		)
		subtask = AssignmentSubtask.objects.create(
			assignment=assignment,
			title="Outline",
			due_date=timezone.now() + timedelta(days=5, hours=1),
			estimated_hours=Decimal("1.0"),
		)
		shift_date = timezone.localdate() + timedelta(days=6)
		shift_start = timezone.make_aware(datetime.combine(shift_date, time(12, 0)), timezone.get_current_timezone())
		shift_end = timezone.make_aware(datetime.combine(shift_date, time(14, 0)), timezone.get_current_timezone())
		WorkShift.objects.create(
			user=self.user,
			employer_name="Campus Library",
			job_title="Campus Library",
			shift_date=shift_date,
			start_time=time(12, 0),
			end_time=time(14, 0),
			shift_start=shift_start,
			shift_end=shift_end,
		)

		response = self.client.post(
			f"/accounts/api/subtasks/{subtask.id}/edit/",
			{
				"title": "Outline",
				"due_date": f"{shift_date.isoformat()}T12:30",
				"estimated_hours": "1",
			},
		)

		self.assertEqual(response.status_code, 409)
		self.assertIn("Only one item can occupy a time block.", response.json()["error"])

	def test_personal_event_edit_rejects_overlap_with_assignment(self):
		assignment_start = timezone.make_aware(
			datetime.combine(timezone.localdate() + timedelta(days=7), time(15, 0)),
			timezone.get_current_timezone(),
		)
		Assignment.objects.create(
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
				"end_time": "17:30",
			},
		)

		self.assertEqual(response.status_code, 409)
		self.assertIn("Only one item can occupy a time block.", response.json()["error"])

	def test_personal_event_add_form_rejects_overlap_with_work_shift(self):
		shift_date = timezone.localdate() + timedelta(days=7)
		WorkShift.objects.create(
			user=self.user,
			employer_name="Campus Cafe",
			job_title="Campus Cafe",
			shift_date=shift_date,
			start_time=time(9, 0),
			end_time=time(11, 0),
			shift_start=timezone.make_aware(datetime.combine(shift_date, time(9, 0)), timezone.get_current_timezone()),
			shift_end=timezone.make_aware(datetime.combine(shift_date, time(11, 0)), timezone.get_current_timezone()),
		)

		response = self.client.post(
			"/home/dashboard/add/personal-event/",
			{
				"title": "Gym",
				"description": "",
				"event_date": shift_date.isoformat(),
				"start_time": "09:30",
				"end_time": "10:30",
				"location": "Rec Center",
				"color_hex": "#FCAF17",
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Only one item can occupy a time block.")
		self.assertFalse(PersonalEvent.objects.filter(user=self.user, title="Gym").exists())

	def test_personal_event_form_normalizes_course_color_to_schedule_palette(self):
		event_date = timezone.localdate() + timedelta(days=7)

		response = self.client.post(
			"/home/dashboard/add/personal-event/",
			{
				"title": "Gym",
				"description": "",
				"event_date": event_date.isoformat(),
				"start_time": "09:30",
				"end_time": "10:30",
				"location": "Rec Center",
				"color_hex": "#1E90FF",
			},
		)

		self.assertEqual(response.status_code, 302)
		personal_event = PersonalEvent.objects.get(user=self.user, title="Gym")
		self.assertEqual(personal_event.color_hex, "#8B5CF6")

	def test_work_shift_edit_rejects_overlap_with_personal_event(self):
		shift_date = timezone.localdate() + timedelta(days=8)
		PersonalEvent.objects.create(
			user=self.user,
			title="Therapy",
			event_date=shift_date,
			start_time=time(9, 0),
			end_time=time(10, 0),
		)
		shift = WorkShift.objects.create(
			user=self.user,
			employer_name="Target",
			job_title="Target",
			shift_date=shift_date,
			start_time=time(11, 0),
			end_time=time(12, 0),
			shift_start=timezone.make_aware(datetime.combine(shift_date, time(11, 0)), timezone.get_current_timezone()),
			shift_end=timezone.make_aware(datetime.combine(shift_date, time(12, 0)), timezone.get_current_timezone()),
		)

		response = self.client.post(
			f"/home/api/work-shifts/{shift.id}/edit/",
			{
				"employer_name": "Target",
				"shift_start": f"{shift_date.isoformat()}T09:30",
				"shift_end": f"{shift_date.isoformat()}T11:00",
			},
		)

		self.assertEqual(response.status_code, 409)
		self.assertIn("Only one item can occupy a time block.", response.json()["error"])

	def test_work_shift_edit_can_replace_conflicting_personal_event(self):
		shift_date = timezone.localdate() + timedelta(days=8)
		conflicting_event = PersonalEvent.objects.create(
			user=self.user,
			title="Therapy",
			event_date=shift_date,
			start_time=time(9, 0),
			end_time=time(10, 0),
		)
		shift = WorkShift.objects.create(
			user=self.user,
			employer_name="Target",
			job_title="Target",
			shift_date=shift_date,
			start_time=time(11, 0),
			end_time=time(12, 0),
			shift_start=timezone.make_aware(datetime.combine(shift_date, time(11, 0)), timezone.get_current_timezone()),
			shift_end=timezone.make_aware(datetime.combine(shift_date, time(12, 0)), timezone.get_current_timezone()),
		)

		conflict_response = self.client.post(
			f"/home/api/work-shifts/{shift.id}/edit/",
			{
				"employer_name": "Target",
				"shift_start": f"{shift_date.isoformat()}T09:00",
				"shift_end": f"{shift_date.isoformat()}T10:00",
			},
		)

		payload = conflict_response.json()
		self.assertEqual(conflict_response.status_code, 409)

		replace_response = self.client.post(
			f"/home/api/work-shifts/{shift.id}/edit/",
			{
				"employer_name": "Target",
				"shift_start": f"{shift_date.isoformat()}T09:00",
				"shift_end": f"{shift_date.isoformat()}T10:00",
				"replace_conflict": "on",
				"conflict_kind": payload["conflict"]["kind_key"],
				"conflict_id": payload["conflict"]["id"],
			},
		)

		self.assertEqual(replace_response.status_code, 200)
		self.assertFalse(PersonalEvent.objects.filter(id=conflicting_event.id).exists())
		shift.refresh_from_db()
		self.assertEqual(shift.start_time, time(9, 0))
		self.assertEqual(shift.end_time, time(10, 0))

	def test_add_work_shift_form_renders_and_saves_date_and_time_fields(self):
		response = self.client.get("/home/dashboard/add/work-shift/")

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'name="shift_date"')
		self.assertContains(response, 'name="start_time"')
		self.assertContains(response, 'name="end_time"')

		shift_date = timezone.localdate() + timedelta(days=9)
		post_response = self.client.post(
			"/home/dashboard/add/work-shift/",
			{
				"job_title": "Campus Desk",
				"shift_date": shift_date.isoformat(),
				"start_time": "08:00",
				"end_time": "12:00",
				"location": "Library",
				"notes": "Morning shift",
				"color_hex": "#10b981",
				"shift_type": "one_time",
			},
		)

		self.assertEqual(post_response.status_code, 302)
		shift = WorkShift.objects.get(user=self.user, job_title="Campus Desk")
		self.assertEqual(shift.shift_date, shift_date)
		self.assertEqual(shift.start_time, time(8, 0))
		self.assertEqual(shift.end_time, time(12, 0))

	def test_add_work_shift_form_rejects_overlap_with_existing_schedule(self):
		shift_date = timezone.localdate() + timedelta(days=10)
		WorkShift.objects.create(
			user=self.user,
			employer_name="Dining Hall",
			job_title="Dining Hall",
			shift_date=shift_date,
			start_time=time(9, 0),
			end_time=time(11, 0),
			shift_start=timezone.make_aware(datetime.combine(shift_date, time(9, 0)), timezone.get_current_timezone()),
			shift_end=timezone.make_aware(datetime.combine(shift_date, time(11, 0)), timezone.get_current_timezone()),
		)

		response = self.client.post(
			"/home/dashboard/add/work-shift/",
			{
				"job_title": "Bookstore",
				"shift_date": shift_date.isoformat(),
				"start_time": "10:00",
				"end_time": "12:00",
				"location": "Student Center",
				"notes": "",
				"color_hex": "#10b981",
				"shift_type": "one_time",
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Only one item can occupy a time block.")
		self.assertFalse(WorkShift.objects.filter(user=self.user, job_title="Bookstore").exists())

	def test_add_work_shift_form_can_replace_conflicting_item(self):
		shift_date = timezone.localdate() + timedelta(days=12)
		conflicting_event = PersonalEvent.objects.create(
			user=self.user,
			title="Dentist",
			event_date=shift_date,
			start_time=time(10, 0),
			end_time=time(12, 0),
		)

		first_response = self.client.post(
			"/home/dashboard/add/work-shift/",
			{
				"job_title": "Campus Desk",
				"shift_date": shift_date.isoformat(),
				"start_time": "10:00",
				"end_time": "12:00",
				"location": "Library",
				"notes": "",
				"color_hex": "#10b981",
				"shift_type": "one_time",
			},
		)

		self.assertEqual(first_response.status_code, 200)
		self.assertContains(first_response, "Schedule Warning")
		self.assertFalse(WorkShift.objects.filter(user=self.user, job_title="Campus Desk").exists())

		replace_response = self.client.post(
			"/home/dashboard/add/work-shift/",
			{
				"job_title": "Campus Desk",
				"shift_date": shift_date.isoformat(),
				"start_time": "10:00",
				"end_time": "12:00",
				"location": "Library",
				"notes": "",
				"color_hex": "#10b981",
				"shift_type": "one_time",
				"replace_conflict": "on",
				"conflict_kind": "personal_event",
				"conflict_id": str(conflicting_event.id),
			},
		)

		self.assertEqual(replace_response.status_code, 302)
		self.assertFalse(PersonalEvent.objects.filter(id=conflicting_event.id).exists())
		self.assertTrue(WorkShift.objects.filter(user=self.user, job_title="Campus Desk").exists())

	def test_work_shift_edit_normalizes_course_color_to_schedule_palette(self):
		shift_date = timezone.localdate() + timedelta(days=10)
		shift = WorkShift.objects.create(
			user=self.user,
			employer_name="Dining Hall",
			job_title="Dining Hall",
			shift_date=shift_date,
			start_time=time(9, 0),
			end_time=time(11, 0),
			shift_start=timezone.make_aware(datetime.combine(shift_date, time(9, 0)), timezone.get_current_timezone()),
			shift_end=timezone.make_aware(datetime.combine(shift_date, time(11, 0)), timezone.get_current_timezone()),
		)

		response = self.client.post(
			f"/home/api/work-shifts/{shift.id}/edit/",
			{
				"employer_name": "Dining Hall",
				"shift_date": shift_date.isoformat(),
				"start_time": "09:00",
				"end_time": "11:00",
				"color_hex": "#1E90FF",
			},
		)

		self.assertEqual(response.status_code, 200)
		shift.refresh_from_db()
		self.assertEqual(shift.color_hex, "#10B981")

	def test_schedule_list_endpoints_return_current_items(self):
		shift_date = timezone.localdate() + timedelta(days=11)
		PersonalEvent.objects.create(
			user=self.user,
			title="Study Group",
			event_date=shift_date,
			start_time=time(13, 0),
			end_time=time(14, 0),
		)
		WorkShift.objects.create(
			user=self.user,
			employer_name="Campus Desk",
			job_title="Campus Desk",
			shift_date=shift_date,
			start_time=time(8, 0),
			end_time=time(12, 0),
			shift_start=timezone.make_aware(datetime.combine(shift_date, time(8, 0)), timezone.get_current_timezone()),
			shift_end=timezone.make_aware(datetime.combine(shift_date, time(12, 0)), timezone.get_current_timezone()),
		)

		personal_response = self.client.get("/home/api/personal-events/")
		work_response = self.client.get("/home/api/work-shifts/")

		self.assertEqual(personal_response.status_code, 200)
		self.assertEqual(work_response.status_code, 200)
		self.assertEqual(personal_response.json()["personal_events"][0]["title"], "Study Group")
		self.assertEqual(work_response.json()["work_shifts"][0]["title"], "Campus Desk")
