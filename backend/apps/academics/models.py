import uuid
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.core.exceptions import ValidationError

class Semester(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='semesters')
    name = models.CharField(max_length=160)
    year = models.PositiveIntegerField()
    semester_number = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(20)])
    is_current = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-is_current', '-year', 'semester_number')
        constraints = [models.UniqueConstraint(fields=('student', 'year', 'semester_number'), name='unique_student_semester')]

    def save(self, *args, **kwargs):
        if self.is_current:
            Semester.objects.filter(student=self.student, is_current=True).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.student.email} · {self.name}'

class Subject(models.Model):
    class Difficulty(models.TextChoices):
        EASY = 'EASY', 'Easy'
        MEDIUM = 'MEDIUM', 'Medium'
        HARD = 'HARD', 'Hard'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=160)
    code = models.CharField(max_length=30, blank=True)
    description = models.TextField(blank=True)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM)
    target_grade = models.CharField(max_length=10, blank=True)
    color = models.CharField(max_length=20, default='#9733EE')
    icon = models.CharField(max_length=40, default='book-open')
    mastery_percentage = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    priority_score = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    exam_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ('exam_date', 'name')
        constraints = [models.UniqueConstraint(fields=('semester', 'name'), name='unique_subject_per_semester')]
    def __str__(self):
        return self.name

class Topic(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = 'NOT_STARTED', 'Not started'
        IN_PROGRESS = 'IN_PROGRESS', 'In progress'
        MASTERED = 'MASTERED', 'Mastered'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    unit_name = models.CharField(max_length=160)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    mastery_percentage = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ('subject', 'unit_name', 'order', 'name')
        constraints = [models.UniqueConstraint(fields=('subject', 'unit_name', 'name'), name='unique_topic_per_unit')]
    def __str__(self):
        return self.name

class Syllabus(models.Model):
    class ProcessingStatus(models.TextChoices):
        UPLOADED = 'UPLOADED', 'Uploaded'
        PROCESSING = 'PROCESSING', 'Processing'
        PROCESSED = 'PROCESSED', 'Processed'
        FAILED = 'FAILED', 'Failed'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='syllabi')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='syllabi/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processing_status = models.CharField(max_length=20, choices=ProcessingStatus.choices, default=ProcessingStatus.UPLOADED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Exam(models.Model):
    class Source(models.TextChoices):
        MANUAL = 'MANUAL', 'Manual'
        IMPORTED = 'IMPORTED', 'Imported'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='exams')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='exams')
    title = models.CharField(max_length=200)
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue = models.CharField(max_length=160, blank=True)
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.MANUAL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError({'end_time': 'End time must be after start time.'})
        if self.subject_id and self.semester_id and self.subject.semester_id != self.semester_id:
            raise ValidationError({'subject': 'Subject must belong to the selected semester.'})

class CollegeClass(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='college_classes')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='college_classes')
    day_of_week = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(6)])
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=80, blank=True)
    instructor = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError({'end_time': 'End time must be after start time.'})
        if self.subject_id and self.semester_id and self.subject.semester_id != self.semester_id:
            raise ValidationError({'subject': 'Subject must belong to the selected semester.'})
