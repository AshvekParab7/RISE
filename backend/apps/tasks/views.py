from rest_framework import permissions, viewsets
from .models import StudySession, Task
from .serializers import StudySessionSerializer, TaskSerializer

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_value_regex = '[0-9a-f-]{36}'
    def get_queryset(self): return Task.objects.filter(student=self.request.user).select_related('subject', 'subject__semester')

class StudySessionViewSet(viewsets.ModelViewSet):
    serializer_class = StudySessionSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_value_regex = '[0-9a-f-]{36}'
    def get_queryset(self): return StudySession.objects.filter(student=self.request.user).select_related('subject', 'topic')
