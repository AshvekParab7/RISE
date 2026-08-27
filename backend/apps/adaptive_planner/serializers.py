from datetime import time

from rest_framework import serializers

from apps.academics.models import Subject

from .models import ExamScheduleRow, ExamScheduleUpload


class ExamScheduleRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamScheduleRow
        fields = '__all__'
        read_only_fields = ('upload', 'subject_label', 'confidence', 'raw_text', 'review_status', 'confirmed_exam', 'created_at', 'updated_at')


class ExamScheduleUploadSerializer(serializers.ModelSerializer):
    rows = ExamScheduleRowSerializer(many=True, read_only=True)

    class Meta:
        model = ExamScheduleUpload
        fields = '__all__'
        read_only_fields = ('student', 'original_filename', 'status', 'processing_error', 'uploaded_at', 'processed_at', 'updated_at')


class ConfirmExamScheduleRowSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    title = serializers.CharField(max_length=200)
    exam_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    venue = serializers.CharField(max_length=160, allow_blank=True, required=False, default='')

    def validate(self, attrs):
        if attrs['end_time'] <= attrs['start_time']:
            raise serializers.ValidationError({'end_time': 'End time must be after start time.'})
        if attrs['subject'].semester.student_id != self.context['request'].user.id:
            raise serializers.ValidationError({'subject': 'Subject does not belong to the authenticated user.'})
        return attrs


class ConfirmExamScheduleSerializer(serializers.Serializer):
    rows = ConfirmExamScheduleRowSerializer(many=True, allow_empty=False)


class PlanPreviewSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    days = serializers.IntegerField(required=False, min_value=1, max_value=14, default=7)
    daily_minutes = serializers.IntegerField(required=False, min_value=30, max_value=720, default=180)
    day_start = serializers.TimeField(required=False, default=time(8, 0))
    day_end = serializers.TimeField(required=False, default=time(22, 0))

    def validate(self, attrs):
        if attrs['day_end'] <= attrs['day_start']:
            raise serializers.ValidationError({'day_end': 'Day end must be after day start.'})
        return attrs


class PlanCommitSerializer(serializers.Serializer):
    blocks = serializers.ListField(child=serializers.JSONField(), allow_empty=False, max_length=100)
