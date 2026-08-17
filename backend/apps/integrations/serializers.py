from rest_framework import serializers
from .models import GoogleConnection

class GoogleConnectionSerializer(serializers.ModelSerializer):
    connected_at = serializers.DateTimeField(source='created_at', read_only=True)
    class Meta:
        model = GoogleConnection
        fields = ('id', 'connected', 'email', 'display_name', 'picture', 'scopes', 'connected_at', 'last_synced_at', 'is_active')
        read_only_fields = fields
    connected = serializers.SerializerMethodField()
    def get_connected(self, obj) -> bool:
        return bool(obj.is_active)
