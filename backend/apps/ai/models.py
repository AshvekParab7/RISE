import uuid
from django.db import models

class ResourceChunk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resource = models.ForeignKey('resources.Resource', on_delete=models.CASCADE, related_name='chunks')
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='resource_chunks')
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE, related_name='resource_chunks')
    text = models.TextField()
    chunk_index = models.PositiveIntegerField()
    page = models.PositiveIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    embedding = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=('resource', 'chunk_index'), name='unique_resource_chunk')]
        ordering = ('resource', 'chunk_index')

class GeneratedTest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='generated_tests')
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE, related_name='generated_tests')
    topic = models.ForeignKey('academics.Topic', on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_tests')
    difficulty = models.CharField(max_length=20, default='MEDIUM')
    question_count = models.PositiveSmallIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

class GeneratedQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey(GeneratedTest, on_delete=models.CASCADE, related_name='questions')
    order = models.PositiveSmallIntegerField()
    question = models.TextField()
    options = models.JSONField(default=list)
    correct_answer = models.CharField(max_length=500)
    explanation = models.TextField(blank=True)
    source_ids = models.JSONField(default=list)

class TestSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey(GeneratedTest, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='test_submissions')
    answers = models.JSONField(default=dict)
    score = models.PositiveSmallIntegerField(default=0)
    total = models.PositiveSmallIntegerField(default=0)
    percentage = models.PositiveSmallIntegerField(default=0)
    feedback = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
