import uuid
from django.db import models


class LearningPath(models.Model):
    class Status(models.TextChoices):
        PROCESSING = 'PROCESSING', 'Processing'
        READY = 'READY', 'Ready'
        FAILED = 'FAILED', 'Failed'
        COMPLETED = 'COMPLETED', 'Completed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='youtube_learning_paths')
    youtube_url = models.URLField(max_length=500)
    video_id = models.CharField(max_length=20)
    title = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PROCESSING)
    processing_stage = models.CharField(max_length=100, default='Validating video')
    processing_progress = models.PositiveSmallIntegerField(default=0)
    failure_reason = models.TextField(blank=True)
    transcript_language = models.CharField(max_length=30, blank=True)
    transcript_segments = models.JSONField(default=list)
    transcript_duration = models.FloatField(default=0)
    current_level_order = models.PositiveSmallIntegerField(default=1)
    xp = models.PositiveIntegerField(default=0)
    cumulative_notes = models.TextField(blank=True)
    study_notes = models.JSONField(default=list)
    final_challenge = models.JSONField(default=dict)
    mastery_percentage = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-updated_at',)
        constraints = [models.UniqueConstraint(fields=('user', 'video_id'), name='unique_user_youtube_path')]


class LearningLevel(models.Model):
    class Status(models.TextChoices):
        LOCKED = 'LOCKED', 'Locked'
        AVAILABLE = 'AVAILABLE', 'Available'
        STARTED = 'STARTED', 'Started'
        COMPLETED = 'COMPLETED', 'Completed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name='levels')
    order = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=240)
    description = models.TextField(blank=True)
    objectives = models.JSONField(default=list)
    transcript_text = models.TextField()
    start_seconds = models.FloatField()
    end_seconds = models.FloatField()
    key_concepts = models.JSONField(default=list)
    lesson_steps = models.JSONField(default=list)
    notes = models.TextField(blank=True)
    checkpoint = models.JSONField(default=dict)
    estimated_minutes = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.LOCKED)
    best_score = models.PositiveSmallIntegerField(default=0)
    best_stars = models.PositiveSmallIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('order',)
        constraints = [models.UniqueConstraint(fields=('learning_path', 'order'), name='unique_learning_level_order')]


class CheckpointAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='youtube_checkpoint_attempts')
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name='attempts')
    level = models.ForeignKey(LearningLevel, on_delete=models.CASCADE, related_name='attempts')
    answer = models.TextField()
    correct = models.BooleanField(default=False)
    score = models.PositiveSmallIntegerField(default=0)
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
