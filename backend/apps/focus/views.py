from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.tasks.models import StudySession
from apps.tasks.serializers import StudySessionSerializer
from .serializers import FocusBreakAnswerSerializer, FocusStartSerializer, FocusStateSerializer
from .services import (
    ACTIVE_FOCUS_STATES,
    FOCUS_DURATION_SECONDS,
    create_smart_break_question,
    create_study_guide,
    grade_smart_break_answer,
    smart_break_question_payload,
    sync_focus_session,
)


class FocusSessionActionsMixin:
    @action(detail=False, methods=['get'], url_path='focus/current')
    def focus_current(self, request):
        session = self.get_queryset().filter(focus_state__in=ACTIVE_FOCUS_STATES).order_by('-created_at').first()
        if not session:
            return Response(None)
        sync_focus_session(session)
        return Response(StudySessionSerializer(session, context={'request': request}).data)

    @action(detail=False, methods=['post'], url_path='focus/start')
    def focus_start(self, request):
        serializer = FocusStartSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            current = self.get_queryset().select_for_update().filter(focus_state__in=ACTIVE_FOCUS_STATES).first()
            if current:
                sync_focus_session(current)
                return Response(
                    StudySessionSerializer(current, context={'request': request}).data,
                    status=status.HTTP_409_CONFLICT,
                )
            now = timezone.now()
            session = StudySession.objects.create(
                student=request.user,
                subject=serializer.validated_data['subject'],
                topic=serializer.validated_data.get('topic'),
                planned_minutes=45,
                remaining_seconds=FOCUS_DURATION_SECONDS,
                started_at=now,
                last_state_change_at=now,
                status=StudySession.Status.ACTIVE,
                focus_state=StudySession.FocusState.ACTIVE,
            )
            session.selected_resources.set(serializer.validated_data['selected_resources'])
        return Response(StudySessionSerializer(session, context={'request': request}).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='focus/state')
    def focus_state(self, request, pk=None):
        serializer = FocusStateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = self.get_object()
        sync_focus_session(session)
        action_name = serializer.validated_data['action']
        now = timezone.now()
        if action_name == 'pause':
            if session.focus_state != StudySession.FocusState.ACTIVE:
                return Response({'detail': 'Only an active Focus session can be paused.'}, status=status.HTTP_409_CONFLICT)
            session.focus_state = StudySession.FocusState.PAUSED_BREAK
            session.last_state_change_at = now
        elif action_name == 'resume':
            if session.focus_state != StudySession.FocusState.PAUSED_BREAK:
                return Response({'detail': 'Only a paused Focus session can be resumed.'}, status=status.HTTP_409_CONFLICT)
            if session.break_unlock_expires_at and session.break_unlock_expires_at > now:
                return Response({'detail': 'The Smart Break is still authorized.'}, status=status.HTTP_409_CONFLICT)
            session.focus_state = StudySession.FocusState.ACTIVE
            session.break_unlock_expires_at = None
            session.last_state_change_at = now
        elif action_name == 'quit':
            if session.focus_state in (StudySession.FocusState.COMPLETED, StudySession.FocusState.ABANDONED):
                return Response({'detail': 'This Focus session has already ended.'}, status=status.HTTP_409_CONFLICT)
            session.focus_state = StudySession.FocusState.ABANDONED
            session.status = StudySession.Status.ABANDONED
            session.end_reason = serializer.validated_data['end_reason']
            session.ended_at = now
        session.save(update_fields=(
            'focus_state', 'break_unlock_expires_at', 'last_state_change_at',
            'status', 'end_reason', 'ended_at',
        ))
        return Response(StudySessionSerializer(session, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='focus/study-guide')
    def focus_study_guide(self, request, pk=None):
        session = self.get_object()
        try:
            return Response(create_study_guide(session))
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='focus/smart-break/question')
    def focus_smart_break_question(self, request, pk=None):
        session = self.get_object()
        sync_focus_session(session)
        if session.focus_state != StudySession.FocusState.ACTIVE:
            return Response({'detail': 'Smart Break questions are available during active Focus time.'}, status=status.HTTP_409_CONFLICT)
        try:
            question, grounded = create_smart_break_question(session)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'question': smart_break_question_payload(question),
            'grounded_in_notes': grounded,
            'focus_state': session.focus_state,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='focus/smart-break/answer')
    def focus_smart_break_answer(self, request, pk=None):
        serializer = FocusBreakAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = self.get_object()
        sync_focus_session(session)
        if session.focus_state != StudySession.FocusState.ACTIVE:
            return Response({'detail': 'Smart Break answers can only be submitted during active Focus time.'}, status=status.HTTP_409_CONFLICT)
        try:
            correct, _ = grade_smart_break_answer(session, serializer.validated_data['answer'])
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        response = {'correct': correct, 'focus_state': session.focus_state}
        if correct:
            response['break_unlock_expires_at'] = session.break_unlock_expires_at
            response['break_seconds'] = 10 * 60
        return Response(response)