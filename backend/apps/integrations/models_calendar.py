import uuid
from django.db import models

class GoogleCalendar(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    google_connection = models.ForeignKey('GoogleConnection', on_delete=models.CASCADE, related_name='calendars')
    google_calendar_id = models.CharField(max_length=255)
    summary = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    time_zone = models.CharField(max_length=80, blank=True)
    access_role = models.CharField(max_length=40, blank=True)
    selected = models.BooleanField(default=False)
    next_sync_token = models.TextField(blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=('google_connection', 'google_calendar_id'), name='unique_google_calendar')]
        ordering = ('summary', 'google_calendar_id')

class GoogleCalendarEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    google_calendar = models.ForeignKey(GoogleCalendar, on_delete=models.CASCADE, related_name='events')
    google_event_id = models.CharField(max_length=255)
    summary = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=500, blank=True)
    start_datetime = models.DateTimeField(null=True, blank=True)
    end_datetime = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=80, blank=True)
    all_day = models.BooleanField(default=False)
    status = models.CharField(max_length=40, blank=True)
    event_type = models.CharField(max_length=40, default='UNKNOWN')
    html_link = models.URLField(blank=True)
    recurrence = models.JSONField(default=list)
    google_created_at = models.DateTimeField(null=True, blank=True)
    google_updated_at = models.DateTimeField(null=True, blank=True)
    rise_exam = models.ForeignKey('academics.Exam', on_delete=models.SET_NULL, null=True, blank=True, related_name='google_calendar_events')
    rise_task = models.ForeignKey('tasks.Task', on_delete=models.SET_NULL, null=True, blank=True, related_name='google_calendar_events')
    last_synced_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=('google_calendar', 'google_event_id'), name='unique_google_calendar_event')]
        ordering = ('start_datetime', 'summary')
