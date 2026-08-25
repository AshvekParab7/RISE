from datetime import datetime, timedelta

from rest_framework import serializers
from .models import PlannerEvent, StudySession, Task

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ('student', 'completed_at', 'created_at', 'updated_at')
    def validate(self, attrs):
        subject = attrs.get('subject')
        if subject and subject.semester.student_id != self.context['request'].user.id:
            raise serializers.ValidationError({'subject': 'Subject does not belong to the authenticated user.'})
        estimated_minutes = attrs.get('estimated_minutes', getattr(self.instance, 'estimated_minutes', 0))
        if estimated_minutes <= 0:
            raise serializers.ValidationError({'estimated_minutes': 'Estimated minutes must be positive.'})
        return attrs
    def create(self, validated_data):
        return Task.objects.create(student=self.context['request'].user, **validated_data)

class StudySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudySession
        fields = '__all__'
        read_only_fields = (
            'student', 'created_at', 'selected_resources', 'smart_break_test',
            'remaining_seconds', 'last_state_change_at', 'focus_state',
            'break_unlock_expires_at', 'penalty_seconds', 'end_reason',
            'score', 'awarded_points', 'completion_metadata',
        )
    def validate(self, attrs):
        subject = attrs.get('subject')
        topic = attrs.get('topic')
        if subject and subject.semester.student_id != self.context['request'].user.id:
            raise serializers.ValidationError({'subject': 'Subject does not belong to the authenticated user.'})
        if topic and topic.subject_id != subject.id:
            raise serializers.ValidationError({'topic': 'Topic must belong to the selected subject.'})
        planned_minutes = attrs.get('planned_minutes', getattr(self.instance, 'planned_minutes', 0))
        if planned_minutes <= 0:
            raise serializers.ValidationError({'planned_minutes': 'Planned minutes must be positive.'})
        return attrs
    def create(self, validated_data):
        return StudySession.objects.create(student=self.context['request'].user, **validated_data)

class PlannerEventSerializer(serializers.ModelSerializer):
    end_at = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PlannerEvent
        fields = '__all__'
        read_only_fields = ('student', 'end_at', 'created_at', 'updated_at')

    def get_end_at(self, instance) -> datetime:
        return instance.start_at + timedelta(minutes=instance.duration_minutes)

    def validate(self, attrs):
        subject = attrs.get('subject')
        if subject and subject.semester.student_id != self.context['request'].user.id:
            raise serializers.ValidationError({'subject': 'Subject does not belong to the authenticated user.'})
        if attrs.get('duration_minutes', getattr(self.instance, 'duration_minutes', 0)) <= 0:
            raise serializers.ValidationError({'duration_minutes': 'Duration must be positive.'})
        return attrs

    def create(self, validated_data):
        return PlannerEvent.objects.create(student=self.context['request'].user, **validated_data)
