from rest_framework import serializers


class FlashcardRequestSerializer(serializers.Serializer):
    topic = serializers.CharField(max_length=500)
    count = serializers.IntegerField(min_value=1, max_value=20, default=3)
    file = serializers.FileField()

    def validate_file(self, file):
        if not file.name.lower().endswith('.pdf') or file.content_type not in ('application/pdf', 'application/x-pdf'):
            raise serializers.ValidationError('Only PDF files are supported.')
        if file.size > 20 * 1024 * 1024:
            raise serializers.ValidationError('PDF must be 20 MB or smaller.')
        return file
