from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TutorSession
from .serializers import AnswerSerializer, EvaluateSerializer, PracticeSerializer, SessionCreateSerializer, TeachSerializer, TutorSessionSerializer
from .services.coach import complete_session, create_session, generate_practice, quick_revision, start_teach, submit_answer, submit_practice


class SessionListCreateView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        sessions = TutorSession.objects.filter(user=request.user).select_related('subject', 'topic')
        return Response(TutorSessionSerializer(sessions, many=True).data)

    def post(self, request):
        serializer = SessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            session = create_session(request.user, serializer.validated_data)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TutorSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class SessionDetailView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, session_id):
        session = get_object_or_404(TutorSession, id=session_id, user=request.user)
        return Response({**TutorSessionSerializer(session).data, 'messages': session.messages, 'current_question': session.current_question})


class TeachView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = TeachSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = get_object_or_404(TutorSession, id=serializer.validated_data['session_id'], user=request.user)
        result = start_teach(session, serializer.validated_data.get('prompt', ''))
        return Response({'session': TutorSessionSerializer(result['session']).data, 'lesson': result['lesson'], 'sources': result['sources']})


class AnswerView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = AnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = get_object_or_404(TutorSession, id=serializer.validated_data['session_id'], user=request.user)
        result = submit_answer(session, serializer.validated_data.get('answer', ''), serializer.validated_data.get('help_requested', False))
        result['session'] = TutorSessionSerializer(result['session']).data
        return Response(result)


class EvaluateView(AnswerView):
    serializer_class = EvaluateSerializer


class PracticeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = PracticeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        session = get_object_or_404(TutorSession, id=data['session_id'], user=request.user)
        try:
            result = submit_practice(session, data['answers']) if 'answers' in data else generate_practice(session, data['question_count'], data['difficulty'])
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'session': TutorSessionSerializer(result.pop('session')).data, **result})


class RevisionView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        session = get_object_or_404(TutorSession, id=request.data.get('session_id'), user=request.user)
        result = quick_revision(session)
        result['session'] = TutorSessionSerializer(result['session']).data
        return Response(result)


class CompleteSessionView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, session_id):
        session = get_object_or_404(TutorSession, id=session_id, user=request.user)
        return Response(TutorSessionSerializer(complete_session(session)).data)


class ReportView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, session_id):
        session = get_object_or_404(TutorSession, id=session_id, user=request.user)
        return Response(session.report)


class WeaknessView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, session_id):
        session = get_object_or_404(TutorSession, id=session_id, user=request.user)
        return Response({'weaknesses': session.weaknesses, 'concepts': session.concepts})
