from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from apps.academics.models import Subject, Topic
from apps.resources.models import Resource
from .models import GeneratedQuestion, GeneratedTest, TestSubmission, TutorConversation
from .serializers import TestGenerateSerializer, TestSubmissionSerializer, TutorConversationSerializer, TutorRequestSerializer
from .services.llm import AIUnavailable, AIProviderError
from .services.tutor import tutor_answer
from .services.assessment_service import generate_assessment
from .services.mastery_engine import apply_assessment_results
from apps.intelligence.services.recommendation_engine import build_context, build_daily_plan, build_next_action

class TutorView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    @extend_schema(request=TutorRequestSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        serializer = TutorRequestSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        data = serializer.validated_data; conversation = None
        if data.get('conversation_id'): conversation = get_object_or_404(TutorConversation, id=data['conversation_id'], student=request.user)
        try: return Response(tutor_answer(request.user, data['message'], data.get('subject_id'), data.get('topic_id'), data.get('resource_ids'), conversation))
        except Exception: return Response({'answer': 'RISE could not complete that tutor request right now.', 'sources': []}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

class ConversationListView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    @extend_schema(responses=TutorConversationSerializer(many=True))
    def get(self, request): return Response(TutorConversationSerializer(TutorConversation.objects.filter(student=request.user).prefetch_related('messages'), many=True).data)

class TestGenerateView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    @extend_schema(request=TestGenerateSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        serializer = TestGenerateSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        data = serializer.validated_data; subject = get_object_or_404(Subject, id=data['subject_id'], semester__student=request.user); topic = None
        if data.get('topic_id'): topic = get_object_or_404(Topic, id=data['topic_id'], subject=subject)
        try:
            assessment, questions, grounded = generate_assessment(request.user, subject.id, topic.id if topic else None, data.get('difficulty'), data['question_count'], data.get('resource_ids'))
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'assessment_id': assessment.id, 'subject': subject.name, 'topic': topic.name if topic else None, 'grounded_in_notes': grounded, 'questions': [{'id': str(item.id), 'question': item.question, 'options': item.options, 'difficulty': assessment.difficulty, 'topic': topic.name if topic else None, 'source_ids': item.source_ids} for item in assessment.questions.all()]}, status=status.HTTP_201_CREATED)

class TestSubmitView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    @extend_schema(request=TestSubmissionSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request, test_id):
        test = get_object_or_404(GeneratedTest, id=test_id, student=request.user); serializer = TestSubmissionSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        if TestSubmission.objects.filter(test=test, student=request.user).exists(): return Response({'detail': 'This assessment has already been completed.'}, status=status.HTTP_409_CONFLICT)
        raw_answers = serializer.validated_data['answers']; answers = {str(item['question_id']): item.get('selected_option') for item in raw_answers} if isinstance(raw_answers, list) else raw_answers
        questions = list(test.questions.all()); performance = {}; score = 0
        for question in questions:
            selected = answers.get(str(question.id)); correct = selected == question.correct_answer; score += int(correct); key = str(test.topic_id or test.subject_id); bucket = performance.setdefault(key, {'correct': 0, 'total': 0, 'percentage': 0}); bucket['correct'] += int(correct); bucket['total'] += 1
        total = len(questions); percentage = round(score / total * 100) if total else 0
        for bucket in performance.values(): bucket['percentage'] = round(bucket['correct'] / bucket['total'] * 100) if bucket['total'] else 0
        submission = TestSubmission.objects.create(test=test, student=request.user, answers=answers, score=score, total=total, percentage=percentage)
        mastery_change = apply_assessment_results(test, performance)
        updated_context = build_context(request.user)
        next_action = build_next_action(updated_context)
        daily_plan = build_daily_plan(updated_context)
        return Response({'score': score, 'total': total, 'percentage': percentage, 'topic_performance': performance, 'mastery_change': mastery_change, 'new_mastery': mastery_change[-1]['after'] if mastery_change else None, 'next_action': next_action, 'daily_plan': daily_plan})

class ResourceStatusView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, resource_id):
        resource = get_object_or_404(Resource, id=resource_id, student=request.user)
        return Response({'resource_id': resource.id, 'processing_status': resource.processing_status, 'processed_at': resource.processed_at, 'processing_error': resource.processing_error})
