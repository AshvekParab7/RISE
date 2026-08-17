import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

class Task(models.Model):
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'
    class Source(models.TextChoices):
        MANUAL = 'MANUAL', 'Manual'
        GOOGLE_CLASSROOM = 'GOOGLE_CLASSROOM', 'Google Classroom'
        GOOGLE_CALENDAR = 'GOOGLE_CALENDAR', 'Google Calendar'
        RISE_TUTOR = 'RISE_TUTOR', 'RISE Tutor'
    class Status(models.TextChoices):
        TODO = 'TODO', 'To do'
        IN_PROGRESS = 'IN_PROGRESS', 'In progress'
        COMPLETED = 'COMPLETED', 'Completed'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='tasks')
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    title = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    deadline = models.DateTimeField()
    estimated_minutes = models.PositiveIntegerField()
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def clean(self):
        if self.estimated_minutes <= 0:
            raise ValidationError({'estimated_minutes': 'Estimated minutes must be positive.'})
        if self.subject_id and self.subject.semester.student_id != self.student_id:
            raise ValidationError({'subject': 'Subject must belong to the authenticated student.'})
    def save(self, *args, **kwargs):
        if self.status == self.Status.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        if self.status != self.Status.COMPLETED:
            self.completed_at = None
        super().save(*args, **kwargs)

class StudySession(models.Model):
    class Status(models.TextChoices):
        PLANNED = 'PLANNED', 'Planned'
        ACTIVE = 'ACTIVE', 'Active'
        COMPLETED = 'COMPLETED', 'Completed'
        ABANDONED = 'ABANDONED', 'Abandoned'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='study_sessions')
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE, related_name='study_sessions')
    topic = models.ForeignKey('academics.Topic', on_delete=models.CASCADE, related_name='study_sessions', null=True, blank=True)
    planned_minutes = models.PositiveIntegerField()
    actual_minutes = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    created_at = models.DateTimeField(auto_now_add=True)
    def clean(self):
        if self.planned_minutes <= 0:
            raise ValidationError({'planned_minutes': 'Planned minutes must be positive.'})
        if self.topic_id and self.topic.subject_id != self.subject_id:
            raise ValidationError({'topic': 'Topic must belong to the selected subject.'})
        if self.subject_id and self.subject.semester.student_id != self.student_id:
            raise ValidationError({'subject': 'Subject must belong to the authenticated student.'})
