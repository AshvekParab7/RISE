from rest_framework import serializers

from .models import TutorConversation, TutorMessage


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
    file = serializers.FileField(required=False)
    subject_id = serializers.UUIDField(required=False, allow_null=True)
    topic_id = serializers.UUIDField(required=False, allow_null=True)
    resource_ids = serializers.ListField(child=serializers.UUIDField(), required=False)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)

    def validate_file(self, file):
        if not file.name.lower().endswith('.pdf') or file.content_type not in ('application/pdf', 'application/x-pdf'):
            raise serializers.ValidationError('Only PDF files are supported.')
        if file.size > 20 * 1024 * 1024:
            raise serializers.ValidationError('PDF must be 20 MB or smaller.')
        return file
