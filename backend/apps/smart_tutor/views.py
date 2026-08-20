from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TutorConversation
from .serializers import TutorConversationSerializer, TutorRequestSerializer
from .flashcard_serializers import FlashcardRequestSerializer
from .mcq_serializers import MCQRequestSerializer
from .services.flashcards import generate_flashcards
from .services.mcqs import generate_mcqs
from .services.tutor import AIProviderError, AIUnavailable, pdf_tutor_answer, public_tutor_answer, tutor_answer


class TutorView(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(request=TutorRequestSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        serializer = TutorRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if data.get('file'):
            try:
                return Response(pdf_tutor_answer(data['message'], data['file']))
            except ValueError as exc:
                return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            except (AIUnavailable, AIProviderError):
                return Response({'answer': 'RISE Tutor is temporarily unavailable.', 'sources': []}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        if not request.user.is_authenticated:
            try:
                return Response(public_tutor_answer(data['message']))
            except (AIUnavailable, AIProviderError):
                return Response({'answer': 'RISE Tutor is temporarily unavailable.', 'sources': []}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        conversation = None
        if data.get('conversation_id'):
            conversation = get_object_or_404(TutorConversation, id=data['conversation_id'], student=request.user)
        try:
            return Response(tutor_answer(request.user, data['message'], data.get('subject_id'), data.get('topic_id'), data.get('resource_ids'), conversation))
        except Exception:
            return Response({'answer': 'RISE could not complete that tutor request right now.', 'sources': []}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class ConversationListView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses=TutorConversationSerializer(many=True))
    def get(self, request):
        conversations = TutorConversation.objects.filter(student=request.user).prefetch_related('messages')
        return Response(TutorConversationSerializer(conversations, many=True).data)


class FlashcardView(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(request=FlashcardRequestSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        serializer = FlashcardRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            cards = generate_flashcards(data['topic'], data['count'], data['file'])
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'topic': data['topic'], 'flashcards': cards})


class MCQView(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(request=MCQRequestSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        serializer = MCQRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            mcqs = generate_mcqs(data['topic'], data['count'], data['file'])
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'topic': data['topic'], 'mcqs': mcqs})
