from django.db.models import Count
from rest_framework import permissions, viewsets
from .models import CollegeClass, Exam, Semester, Subject, Syllabus, Topic
from .serializers import CollegeClassSerializer, ExamSerializer, SemesterSerializer, SubjectSerializer, SyllabusSerializer, TopicSerializer

class OwnedModelViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    lookup_value_regex = '[0-9a-f-]{36}'

class SemesterViewSet(OwnedModelViewSet):
    serializer_class = SemesterSerializer
    def get_queryset(self): return Semester.objects.filter(student=self.request.user)

class SubjectViewSet(OwnedModelViewSet):
    serializer_class = SubjectSerializer
    def get_queryset(self): return Subject.objects.filter(semester__student=self.request.user).select_related('semester').annotate(topic_count=Count('topics'))

class TopicViewSet(OwnedModelViewSet):
    serializer_class = TopicSerializer
    def get_queryset(self): return Topic.objects.filter(subject__semester__student=self.request.user).select_related('subject', 'subject__semester')

class SyllabusViewSet(OwnedModelViewSet):
    serializer_class = SyllabusSerializer
    def get_queryset(self): return Syllabus.objects.filter(semester__student=self.request.user).select_related('semester')

class ExamViewSet(OwnedModelViewSet):
    serializer_class = ExamSerializer
    def get_queryset(self): return Exam.objects.filter(semester__student=self.request.user).select_related('semester', 'subject')

class CollegeClassViewSet(OwnedModelViewSet):
    serializer_class = CollegeClassSerializer
    def get_queryset(self): return CollegeClass.objects.filter(semester__student=self.request.user).select_related('semester', 'subject')
