import uuid
from django.db import models


class TutorSession(models.Model):
    class Mode(models.TextChoices):
        TEACH = 'TEACH', 'Teach me'
        PRACTICE = 'PRACTICE', 'Practice'
        REVISION = 'REVISION', 'Quick revision'

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        COMPLETED = 'COMPLETED', 'Completed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='ashvek_tutor_sessions')
    subject = models.ForeignKey('academics.Subject', on_delete=models.SET_NULL, null=True, blank=True, related_name='ashvek_tutor_sessions')
    topic = models.ForeignKey('academics.Topic', on_delete=models.SET_NULL, null=True, blank=True, related_name='ashvek_tutor_sessions')
    topic_label = models.CharField(max_length=200)
    mode = models.CharField(max_length=12, choices=Mode.choices, default=Mode.TEACH)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    resource_ids = models.JSONField(default=list)
    messages = models.JSONField(default=list)
    concepts = models.JSONField(default=dict)
    questions = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    current_question = models.JSONField(default=dict)
    report = models.JSONField(default=dict)
    practice_test_id = models.UUIDField(null=True, blank=True)
    points = models.PositiveIntegerField(default=0)
    current_step = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-updated_at',)
        indexes = [models.Index(fields=('user', 'status'))]
