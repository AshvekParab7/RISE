from rest_framework import serializers
from .models import GeneratedTest, TestSubmission, TutorConversation, TutorMessage

class TutorMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TutorMessage
        fields = ('id', 'role', 'content', 'created_at')

class TutorConversationSerializer(serializers.ModelSerializer):
    messages = TutorMessageSerializer(many=True, read_only=True)
    class Meta:
        model = TutorConversation
        fields = ('id', 'title', 'messages', 'created_at', 'updated_at')

class TutorRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=10000)
    subject_id = serializers.UUIDField(required=False, allow_null=True)
    topic_id = serializers.UUIDField(required=False, allow_null=True)
    resource_ids = serializers.ListField(child=serializers.UUIDField(), required=False)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)

class TestGenerateSerializer(serializers.Serializer):
    subject_id = serializers.UUIDField()
    topic_id = serializers.UUIDField(required=False, allow_null=True)
    difficulty = serializers.ChoiceField(choices=('EASY', 'MEDIUM', 'HARD'), required=False, allow_null=True)
    question_count = serializers.IntegerField(min_value=1, max_value=20, default=5)

class TestSubmissionSerializer(serializers.Serializer):
    answers = serializers.JSONField()
