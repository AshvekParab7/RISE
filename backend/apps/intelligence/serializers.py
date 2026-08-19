from rest_framework import serializers

class ReasonSerializer(serializers.Serializer):
    code = serializers.CharField()
    label = serializers.CharField()
    impact = serializers.IntegerField()

class PrioritySerializer(serializers.Serializer):
    type = serializers.CharField(required=False)
    subject_id = serializers.CharField(required=False)
    topic_id = serializers.CharField(required=False)
    subject = serializers.CharField()
    topic = serializers.CharField(required=False, allow_null=True)
    priority_score = serializers.IntegerField()
    estimated_minutes = serializers.IntegerField(required=False)
    reasons = ReasonSerializer(many=True)

class PriorityResponseSerializer(serializers.Serializer):
    generated_at = serializers.DateTimeField()
    overall_status = serializers.CharField()
    priorities = PrioritySerializer(many=True)

class NextActionSerializer(serializers.Serializer):
    action = serializers.DictField(allow_null=True)
    reason = serializers.CharField()
