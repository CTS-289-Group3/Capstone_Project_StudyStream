from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from accounts.models import Assignment, AssignmentSubtask, Course, Semester


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
