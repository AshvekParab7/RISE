import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

MAX_FILE_SIZE = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'webp'}


def validate_exam_schedule_file(value):
    name = value.name.lower()
    extension = name.rsplit('.', 1)[-1] if '.' in name else ''
    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationError('Exam schedules must be PDF or image files.')
    if value.size > MAX_FILE_SIZE:
        raise ValidationError('Exam schedule files must be 20 MB or smaller.')


class ExamScheduleUpload(models.Model):
    class Status(models.TextChoices):
        PROCESSING = 'PROCESSING', 'Processing'
        NEEDS_REVIEW = 'NEEDS_REVIEW', 'Needs review'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        FAILED = 'FAILED', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exam_schedule_uploads')
    file = models.FileField(upload_to='exam-schedules/', validators=[validate_exam_schedule_file])
    original_filename = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROCESSING)
    processing_error = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-uploaded_at',)


class ExamScheduleRow(models.Model):
    class ReviewStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending review'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        REJECTED = 'REJECTED', 'Rejected'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    upload = models.ForeignKey(ExamScheduleUpload, on_delete=models.CASCADE, related_name='rows')
    subject = models.ForeignKey('academics.Subject', on_delete=models.SET_NULL, null=True, blank=True, related_name='exam_schedule_rows')
    subject_label = models.CharField(max_length=200, blank=True)
    title = models.CharField(max_length=200, default='Imported exam')
    exam_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    venue = models.CharField(max_length=160, blank=True)
    confidence = models.PositiveSmallIntegerField(default=0)
    raw_text = models.TextField(blank=True)
    review_status = models.CharField(max_length=12, choices=ReviewStatus.choices, default=ReviewStatus.PENDING)
    confirmed_exam = models.ForeignKey('academics.Exam', on_delete=models.SET_NULL, null=True, blank=True, related_name='schedule_rows')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('exam_date', 'start_time', 'subject_label', 'created_at')
