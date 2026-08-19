from rest_framework import permissions, viewsets
from .models import Resource
from .serializers import ResourceSerializer
from apps.ai.services.resource_processing import process_resource

class ResourceViewSet(viewsets.ModelViewSet):
    serializer_class = ResourceSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_value_regex = '[0-9a-f-]{36}'
    def get_queryset(self): return Resource.objects.filter(student=self.request.user).select_related('subject', 'subject__semester')
    def perform_create(self, serializer):
        resource = serializer.save()
        process_resource(resource)
