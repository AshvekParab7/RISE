from rest_framework import serializers

from apps.academics.models import Subject, Topic
from apps.resources.models import Resource


class FocusStartSerializer(serializers.Serializer):
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    topic = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all(), required=False, allow_null=True)
    selected_resource_ids = serializers.PrimaryKeyRelatedField(
        source='selected_resources',
        many=True,
        queryset=Resource.objects.all(),
        allow_empty=False,
    )

    def validate(self, attrs):
        user = self.context['request'].user
        subject = attrs['subject']
        topic = attrs.get('topic')
        resources = attrs['selected_resources']
        if subject.semester.student_id != user.id:
            raise serializers.ValidationError({'subject': 'Subject does not belong to the authenticated user.'})
        if topic and topic.subject_id != subject.id:
            raise serializers.ValidationError({'topic': 'Topic must belong to the selected subject.'})
        invalid_resources = [
            resource for resource in resources
            if resource.student_id != user.id
            or resource.subject_id != subject.id
            or resource.processing_status != Resource.ProcessingStatus.READY
        ]
        if invalid_resources:
            raise serializers.ValidationError({
                'selected_resource_ids': 'Resources must belong to the authenticated student and selected subject, and be READY.',
            })
        return attrs


class FocusStateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=('sync', 'pause', 'resume', 'quit'))
    end_reason = serializers.CharField(required=False, allow_blank=False, max_length=120)

    def validate(self, attrs):
        if attrs['action'] == 'quit' and not attrs.get('end_reason'):
            raise serializers.ValidationError({'end_reason': 'A reason is required when quitting a Focus session.'})
        return attrs


class FocusBreakAnswerSerializer(serializers.Serializer):
    answer = serializers.CharField(max_length=500, allow_blank=False)