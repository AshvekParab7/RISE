import uuid
from django.db import models

class GoogleCourse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    google_connection = models.ForeignKey('GoogleConnection', on_delete=models.CASCADE, related_name='courses')
    google_course_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    section = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    room = models.CharField(max_length=255, blank=True)
    teacher_name = models.CharField(max_length=255, blank=True)
    course_state = models.CharField(max_length=40, blank=True)
    course_created_at = models.DateTimeField(null=True, blank=True)
    course_updated_at = models.DateTimeField(null=True, blank=True)
    rise_subject = models.ForeignKey('academics.Subject', on_delete=models.SET_NULL, null=True, blank=True, related_name='google_courses')
    last_synced_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=('google_connection', 'google_course_id'), name='unique_google_course_connection')]
        ordering = ('name',)

class GoogleCoursework(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    google_course = models.ForeignKey(GoogleCourse, on_delete=models.CASCADE, related_name='coursework')
    google_coursework_id = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    state = models.CharField(max_length=40, blank=True)
    work_type = models.CharField(max_length=40, blank=True)
    due_date = models.DateField(null=True, blank=True)
    due_time = models.TimeField(null=True, blank=True)
    alternate_link = models.URLField(blank=True)
    creation_time = models.DateTimeField(null=True, blank=True)
    update_time = models.DateTimeField(null=True, blank=True)
    max_points = models.FloatField(null=True, blank=True)
    source_snapshot = models.JSONField(default=dict)
    rise_task = models.OneToOneField('tasks.Task', on_delete=models.SET_NULL, null=True, blank=True, related_name='google_coursework')
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=('google_course', 'google_coursework_id'), name='unique_google_coursework')]
        ordering = ('due_date', 'title')

class GoogleMaterial(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    google_course = models.ForeignKey(GoogleCourse, on_delete=models.CASCADE, related_name='materials')
    google_material_id = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    material_type = models.CharField(max_length=40, blank=True)
    drive_file_id = models.CharField(max_length=255, blank=True)
    alternate_link = models.URLField(blank=True)
    mime_type = models.CharField(max_length=160, blank=True)
    source_url = models.URLField(blank=True)
    rise_resource = models.ForeignKey('resources.Resource', on_delete=models.SET_NULL, null=True, blank=True, related_name='google_materials')
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=('google_course', 'google_material_id'), name='unique_google_material')]
        ordering = ('title',)

class GoogleSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    google_coursework = models.ForeignKey(GoogleCoursework, on_delete=models.CASCADE, related_name='submissions')
    google_submission_id = models.CharField(max_length=255)
    state = models.CharField(max_length=40, blank=True)
    assigned_grade = models.FloatField(null=True, blank=True)
    draft_grade = models.FloatField(null=True, blank=True)
    late = models.BooleanField(default=False)
    submission_time = models.DateTimeField(null=True, blank=True)
    update_time = models.DateTimeField(null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=('google_coursework', 'google_submission_id'), name='unique_google_submission')]
