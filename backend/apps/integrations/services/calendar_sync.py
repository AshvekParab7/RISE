from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from django.db import transaction
from django.utils import timezone
from apps.academics.models import Exam, Semester, Subject
from apps.tasks.models import Task
from .google_calendar import CalendarSyncTokenExpired, GoogleCalendarService
from ..models_calendar import GoogleCalendar, GoogleCalendarEvent

KEYWORDS = {'exam': 'ACADEMIC', 'test': 'ACADEMIC', 'quiz': 'ACADEMIC', 'lecture': 'ACADEMIC', 'class': 'ACADEMIC', 'lab': 'ACADEMIC', 'assignment': 'ACADEMIC', 'deadline': 'ACADEMIC', 'submission': 'ACADEMIC', 'project': 'ACADEMIC'}

def classify(summary):
    value = (summary or '').lower()
    return 'ACADEMIC' if any(keyword in value for keyword in KEYWORDS) else 'UNKNOWN'

def parse_event_time(value, calendar_timezone, all_day=False):
    if all_day:
        zone = ZoneInfo(calendar_timezone or 'UTC')
        return datetime.combine(datetime.fromisoformat(value).date(), time.min, tzinfo=zone)
    return datetime.fromisoformat(value.replace('Z', '+00:00'))

class CalendarSyncEngine:
    def __init__(self, connection, service_class=GoogleCalendarService): self.connection = connection; self.service = service_class(connection)

    @transaction.atomic
    def sync(self, calendar_ids=None, now=None):
        now = now or timezone.now(); result = {'calendars': 0, 'events_found': 0, 'events_created': 0, 'events_updated': 0, 'events_removed': 0, 'tasks_created': 0, 'exams_created': 0, 'skipped': 0, 'errors': []}
        selected = GoogleCalendar.objects.filter(google_connection=self.connection, selected=True, is_active=True)
        if calendar_ids is not None: selected = selected.filter(google_calendar_id__in=calendar_ids)
        for calendar in selected:
            try:
                time_min = now - timedelta(days=30); time_max = now + timedelta(days=180)
                try: events, sync_token = self.service.get_events(calendar.google_calendar_id, time_min, time_max, calendar.next_sync_token or None)
                except CalendarSyncTokenExpired:
                    calendar.next_sync_token = ''; calendar.events.all().delete(); calendar.save(update_fields=['next_sync_token', 'updated_at'])
                    events, sync_token = self.service.get_events(calendar.google_calendar_id, time_min, time_max, None)
                for event in events:
                    result['events_found'] += 1
                    created, removed, mapped = self._upsert_event(calendar, event)
                    result['events_created' if created else 'events_updated'] += 1
                    if removed: result['events_removed'] += 1
                    if not mapped: result['skipped'] += 1
                calendar.next_sync_token = sync_token or calendar.next_sync_token; calendar.last_synced_at = timezone.now(); calendar.save(update_fields=['next_sync_token', 'last_synced_at', 'updated_at'])
            except Exception:
                result['errors'].append({'calendar_id': calendar.google_calendar_id, 'message': 'Calendar sync failed.'})
        return result

    def _upsert_event(self, calendar, event):
        deleted = event.get('status') == 'cancelled'; start = event.get('start', {}); end = event.get('end', {}); all_day = 'date' in start
        start_value = start.get('date') if all_day else start.get('dateTime'); end_value = end.get('date') if all_day else end.get('dateTime')
        start_dt = parse_event_time(start_value, start.get('timeZone') or calendar.time_zone, all_day) if start_value else None
        end_dt = parse_event_time(end_value, end.get('timeZone') or calendar.time_zone, all_day) if end_value else None
        record, created = GoogleCalendarEvent.objects.update_or_create(google_calendar=calendar, google_event_id=event['id'], defaults={'summary': event.get('summary', ''), 'description': event.get('description', ''), 'location': event.get('location', ''), 'start_datetime': start_dt, 'end_datetime': end_dt, 'timezone': start.get('timeZone') or calendar.time_zone, 'all_day': all_day, 'status': event.get('status', ''), 'event_type': classify(event.get('summary', '')), 'html_link': event.get('htmlLink', ''), 'recurrence': event.get('recurrence', []), 'google_created_at': self._parse(event.get('created')), 'google_updated_at': self._parse(event.get('updated')), 'last_synced_at': timezone.now(), 'is_active': not deleted})
        if deleted: return created, True, False
        mapped = self._map_to_rise(record)
        return created, False, mapped

    def _parse(self, value): return datetime.fromisoformat(value.replace('Z', '+00:00')) if value else None

    def _map_to_rise(self, event):
        semester = Semester.objects.filter(student=self.connection.user, is_current=True).first() or Semester.objects.filter(student=self.connection.user).first()
        subject = next((item for item in Subject.objects.filter(semester__student=self.connection.user) if item.name.lower() in event.summary.lower() or (item.code and item.code.lower() in event.summary.lower())), None)
        summary = event.summary.lower(); due = event.end_datetime or event.start_datetime or timezone.now()
        if subject and any(word in summary for word in ('exam', 'test', 'quiz')) and not event.rise_exam:
            event.rise_exam = Exam.objects.create(semester=semester, subject=subject, title=event.summary, exam_date=due.date(), start_time=(event.start_datetime or due).time(), end_time=due.time(), source=Exam.Source.IMPORTED); event.save(update_fields=['rise_exam', 'updated_at']); return True
        if subject and any(word in summary for word in ('assignment', 'deadline', 'submission')):
            if not event.rise_task: event.rise_task = Task.objects.create(student=self.connection.user, subject=subject, title=event.summary, description=event.description, deadline=due, estimated_minutes=30, priority=Task.Priority.MEDIUM, source=Task.Source.GOOGLE_CALENDAR); event.save(update_fields=['rise_task', 'updated_at']); return True
        return event.event_type == 'ACADEMIC'
