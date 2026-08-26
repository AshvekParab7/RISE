from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from apps.academics.models import Subject, Topic
from apps.resources.models import Resource
from .models import GeneratedQuestion, GeneratedTest, PlannerConversation, PlannerMessage, TestSubmission, TutorConversation
from .serializers import TestGenerateSerializer, TestSubmissionSerializer, TutorConversationSerializer, TutorRequestSerializer
from .services.gemini import GeminiUnavailable
from .services.llm import AIUnavailable, AIProviderError
from .services.tutor import pdf_tutor_answer, public_tutor_answer, tutor_answer
from .services.assessment_service import generate_assessment
from .services.mastery_engine import apply_assessment_results
from apps.intelligence.services.recommendation_engine import build_context, build_daily_plan, build_next_action
from .serializers import PlannerRequestSerializer
from .services.planner import build_planner_context, fallback_planner_turn, planner_turn


def _planner_history(conversation):
    return [
        {
            'role': 'user' if message.role == PlannerMessage.Role.USER else 'assistant',
            'content': message.content,
        }
        for message in conversation.messages.order_by('created_at', 'id')
    ]


def _planner_conversation_data(conversation, include_messages=False):
    data = {
        'id': str(conversation.id),
        'title': conversation.title or 'New planner chat',
        'created_at': conversation.created_at,
        'updated_at': conversation.updated_at,
    }
    if hasattr(conversation, 'message_count'):
        data['message_count'] = conversation.message_count
    if include_messages:
        data['messages'] = [
            {
                'id': str(message.id),
                'role': 'user' if message.role == PlannerMessage.Role.USER else 'assistant',
                'content': message.content,
                'created_at': message.created_at,
            }
            for message in conversation.messages.order_by('created_at', 'id')
        ]
    return data


class PlannerView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(request=PlannerRequestSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        serializer = PlannerRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        conversation_id = data.get('conversation_id')
        conversation = get_object_or_404(
            PlannerConversation.objects.prefetch_related('messages'),
            id=conversation_id,
            student=request.user,
        ) if conversation_id else PlannerConversation.objects.create(
            student=request.user,
            title=' '.join(data['message'].split())[:200],
        )
        history = _planner_history(conversation) if conversation_id else data.get('history', [])
        if not history or history[-1].get('role') != 'user' or history[-1].get('content') != data['message']:
            history = [*history, {'role': 'user', 'content': data['message']}]
        PlannerMessage.objects.create(
            conversation=conversation,
            role=PlannerMessage.Role.USER,
            content=data['message'],
        )
        planner_context = build_planner_context(request.user, data.get('selected_day'))
        context = build_context(request.user)
        progress = {'next_action': build_next_action(context), 'daily_plan': build_daily_plan(context)}
        try:
            result = planner_turn(data['message'], history, planner_context['calendar'], progress, planner_context)
        except (AIUnavailable, AIProviderError, GeminiUnavailable):
            result = fallback_planner_turn(data['message'], history, planner_context)
        reply = str(result.get('reply') or 'Tell me what you want to study and when you are free.')
        PlannerMessage.objects.create(
            conversation=conversation,
            role=PlannerMessage.Role.ASSISTANT,
            content=reply,
        )
        conversation.save(update_fields=('updated_at',))
        return Response({
            **result,
            'reply': reply,
            'conversation_id': str(conversation.id),
            'conversation_title': conversation.title or 'New planner chat',
        })


class PlannerConversationListView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        conversations = PlannerConversation.objects.filter(
            student=request.user,
        ).annotate(message_count=Count('messages')).order_by('-updated_at')[:30]
        return Response([_planner_conversation_data(conversation) for conversation in conversations])


class PlannerConversationDetailView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, conversation_id):
        conversation = get_object_or_404(
            PlannerConversation.objects.prefetch_related('messages'),
            id=conversation_id,
            student=request.user,
        )
        return Response(_planner_conversation_data(conversation, include_messages=True))


class PlannerConversationMessageView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, conversation_id):
        conversation = get_object_or_404(PlannerConversation, id=conversation_id, student=request.user)
        content = str(request.data.get('content') or '').strip()
        role = str(request.data.get('role') or '').upper()
        if not content or role not in (PlannerMessage.Role.USER, PlannerMessage.Role.ASSISTANT):
            return Response({'detail': 'A message role and content are required.'}, status=status.HTTP_400_BAD_REQUEST)
        message = PlannerMessage.objects.create(conversation=conversation, role=role, content=content)
        conversation.save(update_fields=('updated_at',))
        return Response({
            'id': str(message.id),
            'role': role.lower(),
            'content': message.content,
            'created_at': message.created_at,
        }, status=status.HTTP_201_CREATED)

class TutorView(APIView):
    permission_classes = (permissions.AllowAny,)
    @extend_schema(request=TutorRequestSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        serializer = TutorRequestSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        data = serializer.validated_data; conversation = None
        if data.get('file'):
            try: return Response(pdf_tutor_answer(data['message'], data['file']))
            except ValueError as exc: return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            except (AIUnavailable, AIProviderError): return Response({'answer': 'RISE Tutor is temporarily unavailable.', 'sources': []}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        if not request.user.is_authenticated:
            try: return Response(public_tutor_answer(data['message']))
            except (AIUnavailable, AIProviderError): return Response({'answer': 'RISE Tutor is temporarily unavailable.', 'sources': []}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
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
