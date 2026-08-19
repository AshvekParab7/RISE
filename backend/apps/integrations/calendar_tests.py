from datetime import datetime, timezone
from unittest.mock import Mock
from django.test import TestCase
from apps.accounts.models import User
from apps.academics.models import Semester, Subject
from apps.tasks.models import Task
from .models import GoogleConnection
from .models_calendar import GoogleCalendar, GoogleCalendarEvent
from .services.calendar_sync import CalendarSyncEngine
from .services.google_calendar import CalendarSyncTokenExpired

class FakeCalendarService:
    def __init__(self, connection): self.connection = connection; self.calls = 0
    def get_events(self, calendar_id, time_min, time_max, sync_token=None):
        self.calls += 1
        return ([{'id': 'event-exam', 'summary': 'Computer Networks Final Exam', 'status': 'confirmed', 'start': {'dateTime': '2026-09-20T10:00:00+05:30', 'timeZone': 'Asia/Kolkata'}, 'end': {'dateTime': '2026-09-20T12:00:00+05:30', 'timeZone': 'Asia/Kolkata'}, 'created': '2026-08-01T00:00:00Z', 'updated': '2026-08-02T00:00:00Z'}, {'id': 'event-task', 'summary': 'CN assignment deadline', 'status': 'confirmed', 'start': {'date': '2026-09-21'}, 'end': {'date': '2026-09-22'}, 'created': '2026-08-01T00:00:00Z', 'updated': '2026-08-02T00:00:00Z'}], 'calendar-sync-token')

class CalendarSyncTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('calendar@example.com', 'Password123!')
        semester = Semester.objects.create(student=self.user, name='Semester 5', year=2026, semester_number=5, is_current=True)
        self.subject = Subject.objects.create(semester=semester, name='Computer Networks', code='CN')
        self.connection = GoogleConnection.objects.create(user=self.user, google_user_id='calendar-google', email='calendar@gmail.com')
        self.calendar = GoogleCalendar.objects.create(google_connection=self.connection, google_calendar_id='academic', summary='Academic', time_zone='Asia/Kolkata', selected=True)

    def test_sync_is_idempotent_and_preserves_timezone(self):
        first = CalendarSyncEngine(self.connection, FakeCalendarService).sync()
        second = CalendarSyncEngine(self.connection, FakeCalendarService).sync()
        self.assertEqual(first['events_created'], 2)
        self.assertEqual(second['events_created'], 0)
        self.assertEqual(GoogleCalendarEvent.objects.count(), 2)
        event = GoogleCalendarEvent.objects.get(google_event_id='event-exam')
        self.assertEqual(event.timezone, 'Asia/Kolkata')
        self.assertTrue(event.rise_exam_id)
        self.assertEqual(Task.objects.filter(source=Task.Source.GOOGLE_CALENDAR).count(), 1)

    def test_invalid_sync_token_triggers_full_sync(self):
        class TokenService(FakeCalendarService):
            def get_events(self, calendar_id, time_min, time_max, sync_token=None):
                if sync_token: raise CalendarSyncTokenExpired(410, 'expired')
                return super().get_events(calendar_id, time_min, time_max, sync_token)
        self.calendar.next_sync_token = 'expired'; self.calendar.save()
        result = CalendarSyncEngine(self.connection, TokenService).sync()
        self.assertEqual(result['events_created'], 2)
        self.assertEqual(GoogleCalendar.objects.get(pk=self.calendar.pk).next_sync_token, 'calendar-sync-token')
