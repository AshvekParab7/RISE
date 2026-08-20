from rest_framework import serializers
from .models import GeneratedTest, TestSubmission

class PlannerRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=10000)
    history = serializers.ListField(child=serializers.JSONField(), required=False, default=list)
    calendar = serializers.ListField(child=serializers.JSONField(), required=False, default=list)
    progress = serializers.JSONField(required=False, default=dict)

class TestGenerateSerializer(serializers.Serializer):
    subject_id = serializers.UUIDField()
    topic_id = serializers.UUIDField(required=False, allow_null=True)
    difficulty = serializers.ChoiceField(choices=('EASY', 'MEDIUM', 'HARD'), required=False, allow_null=True)
    question_count = serializers.IntegerField(min_value=1, max_value=20, default=5)

class TestSubmissionSerializer(serializers.Serializer):
    answers = serializers.JSONField()
