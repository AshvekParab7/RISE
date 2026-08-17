import uuid
from django.core.exceptions import ValidationError
from django.db import models

MAX_FILE_SIZE = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'png', 'jpg', 'jpeg', 'webp'}

def validate_resource_file(value):
    name = value.name.lower()
    extension = name.rsplit('.', 1)[-1] if '.' in name else ''
    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationError('Unsupported file type.')
    if value.size > MAX_FILE_SIZE:
        raise ValidationError('File must be 20 MB or smaller.')

def validate_syllabus_file(value):
    validate_resource_file(value)

class Resource(models.Model):
    class ProcessingStatus(models.TextChoices):
        PROCESSING = 'PROCESSING', 'Processing'
        READY = 'READY', 'Ready'
        FAILED = 'FAILED', 'Failed'
    class ResourceType(models.TextChoices):
        NOTE = 'NOTE', 'Note'
        SLIDES = 'SLIDES', 'Slides'
        DOCUMENT = 'DOCUMENT', 'Document'
        QUESTION_PAPER = 'QUESTION_PAPER', 'Question paper'
        IMAGE = 'IMAGE', 'Image'
        OTHER = 'OTHER', 'Other'
    class Source(models.TextChoices):
        USER_UPLOAD = 'USER_UPLOAD', 'User upload'
        GOOGLE_CLASSROOM = 'GOOGLE_CLASSROOM', 'Google Classroom'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='resources')
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='resources/', validators=[validate_resource_file], blank=True)
    resource_type = models.CharField(max_length=20, choices=ResourceType.choices, default=ResourceType.NOTE)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.USER_UPLOAD)
    file_size = models.PositiveBigIntegerField(default=0)
    page_count = models.PositiveIntegerField(null=True, blank=True)
    is_ai_ready = models.BooleanField(default=False)
    processing_status = models.CharField(max_length=12, choices=ProcessingStatus.choices, default=ProcessingStatus.PROCESSING)
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def clean(self):
        if self.subject_id and self.student_id and self.subject.semester.student_id != self.student_id:
            raise ValidationError({'subject': 'Subject must belong to the authenticated student.'})
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
