from datetime import datetime, time, timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.accounts.models import User
from apps.academics.models import Semester, Subject
from apps.tasks.models import Task
from .models import WhatsAppAssignmentReminder
from .services.assignment_reminders import send_due_assignment_reminders


class AssignmentReminderTests(TestCase):
    @override_settings(TWILIO_ASSIGNMENT_CONTENT_SID='HX-test')
    @patch('apps.integrations.services.assignment_reminders.send_assignment_reminder', return_value={'sid': 'SM-test', 'status': 'queued', 'to': 'whatsapp:+919518786952'})
    def test_sends_once_for_incomplete_assignment_due_in_two_days(self, send):
        user = User.objects.create_user('reminder@example.com', 'Password123!', phone_number='+919518786952')
        semester = Semester.objects.create(student=user, name='Semester 5', year=2026, semester_number=5, is_current=True)
        subject = Subject.objects.create(semester=semester, name='Computer Networks', code='CN')
        target = timezone.localdate() + timedelta(days=2)
        task = Task.objects.create(
            student=user,
            subject=subject,
            title='TCP worksheet',
            description='Submit the worksheet.',
            deadline=timezone.make_aware(datetime.combine(target, time(14, 0))),
            estimated_minutes=60,
            source=Task.Source.GOOGLE_CLASSROOM,
            status=Task.Status.TODO,
        )
        first = send_due_assignment_reminders()
        second = send_due_assignment_reminders()
        self.assertEqual(first['sent'], 1)
        self.assertEqual(second['sent'], 0)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(WhatsAppAssignmentReminder.objects.get(task=task).message_sid, 'SM-test')
