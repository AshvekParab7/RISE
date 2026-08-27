from rest_framework import serializers
from .models import TutorSession


class TutorSessionSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True, allow_null=True)
    topic_name = serializers.CharField(source='topic.name', read_only=True, allow_null=True)

    class Meta:
        model = TutorSession
        fields = ('id', 'subject', 'subject_name', 'topic', 'topic_name', 'topic_label', 'mode', 'status', 'resource_ids', 'concepts', 'weaknesses', 'report', 'points', 'current_step', 'created_at', 'updated_at', 'completed_at')
        read_only_fields = fields


class SessionCreateSerializer(serializers.Serializer):
    topic = serializers.CharField(max_length=200)
    subject_id = serializers.UUIDField(required=False, allow_null=True)
    topic_id = serializers.UUIDField(required=False, allow_null=True)
    resource_ids = serializers.ListField(child=serializers.UUIDField(), required=False, allow_empty=True)
    mode = serializers.ChoiceField(choices=TutorSession.Mode.choices, default=TutorSession.Mode.TEACH)


class SessionActionSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()


class TeachSerializer(SessionActionSerializer):
    prompt = serializers.CharField(required=False, allow_blank=True, max_length=500)


class AnswerSerializer(SessionActionSerializer):
    answer = serializers.CharField(max_length=4000, required=False, allow_blank=True)
    question_id = serializers.CharField(required=False, allow_blank=True)
    help_requested = serializers.BooleanField(required=False, default=False)


class PracticeSerializer(SessionActionSerializer):
    question_count = serializers.IntegerField(required=False, min_value=1, max_value=10, default=5)
    difficulty = serializers.ChoiceField(choices=('EASY', 'MEDIUM', 'HARD', 'ADAPTIVE'), default='ADAPTIVE')
    answers = serializers.DictField(required=False)


class EvaluateSerializer(AnswerSerializer):
    pass
