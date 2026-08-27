from rest_framework import serializers
from .models import CheckpointAttempt, LearningLevel, LearningPath


class YouTubeCreateSerializer(serializers.Serializer):
    url = serializers.URLField(max_length=500)
    retry = serializers.BooleanField(required=False, default=False)


class LearningLevelSerializer(serializers.ModelSerializer):
    checkpoint = serializers.SerializerMethodField()

    class Meta:
        model = LearningLevel
        fields = ('id', 'order', 'title', 'description', 'objectives', 'start_seconds', 'end_seconds', 'key_concepts', 'lesson_steps', 'notes', 'checkpoint', 'estimated_minutes', 'status', 'best_score', 'best_stars', 'started_at', 'completed_at')

    def get_checkpoint(self, obj):
        checkpoint = dict(obj.checkpoint or {})
        checkpoint.pop('correct_answer', None)
        checkpoint.pop('explanation', None)
        if isinstance(checkpoint.get('options'), dict):
            checkpoint['options'] = [f'{key}. {value}' for key, value in checkpoint['options'].items()]
        return checkpoint


class LearningPathSerializer(serializers.ModelSerializer):
    levels = LearningLevelSerializer(many=True, read_only=True)
    completed_levels = serializers.SerializerMethodField()
    total_levels = serializers.IntegerField(source='levels.count', read_only=True)
    final_challenge = serializers.SerializerMethodField()

    class Meta:
        model = LearningPath
        fields = ('id', 'youtube_url', 'video_id', 'title', 'status', 'processing_stage', 'processing_progress', 'failure_reason', 'transcript_language', 'transcript_duration', 'current_level_order', 'xp', 'cumulative_notes', 'study_notes', 'mastery_percentage', 'final_challenge', 'completed_levels', 'total_levels', 'levels', 'created_at', 'updated_at', 'completed_at')

    def get_completed_levels(self, obj):
        return obj.levels.filter(status=LearningLevel.Status.COMPLETED).count()

    def get_final_challenge(self, obj):
        challenge = dict(obj.final_challenge or {})
        challenge['questions'] = [{key: value for key, value in question.items() if key not in ('correct_answer', 'explanation')} for question in challenge.get('questions', [])]
        return challenge


class CheckpointSerializer(serializers.Serializer):
    level_id = serializers.UUIDField()
    answer = serializers.CharField(max_length=5000)


class FinalChallengeSerializer(serializers.Serializer):
    answers = serializers.DictField(child=serializers.CharField(max_length=5000))


class CheckpointAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckpointAttempt
        fields = ('id', 'level', 'correct', 'score', 'feedback', 'created_at')
