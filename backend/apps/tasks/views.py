from rest_framework import permissions, viewsets
from .models import PlannerEvent, StudySession, Task
from .serializers import PlannerEventSerializer, StudySessionSerializer, TaskSerializer

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

class PlannerEventViewSet(viewsets.ModelViewSet):
    serializer_class = PlannerEventSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_value_regex = '[0-9a-f-]{36}'

    def get_queryset(self):
        queryset = PlannerEvent.objects.filter(student=self.request.user).select_related('subject')
        day = self.request.query_params.get('day')
        return queryset.filter(start_at__date=day) if day else queryset
