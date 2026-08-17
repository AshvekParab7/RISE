from rest_framework import serializers
from .models import Resource

class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = '__all__'
        read_only_fields = ('student', 'file_size', 'uploaded_at', 'updated_at', 'is_ai_ready')
    def validate_subject(self, subject):
        if subject.semester.student_id != self.context['request'].user.id:
            raise serializers.ValidationError('Subject does not belong to the authenticated user.')
        return subject
    def create(self, validated_data):
        return Resource.objects.create(student=self.context['request'].user, **validated_data)
