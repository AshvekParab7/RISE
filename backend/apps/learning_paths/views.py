from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import LearningLevel, LearningPath
from .serializers import CheckpointAttemptSerializer, CheckpointSerializer, FinalChallengeSerializer, LearningLevelSerializer, LearningPathSerializer, YouTubeCreateSerializer
from .services.tasks import enqueue_learning_path
from .services.progress import evaluate_checkpoint, evaluate_final_challenge
from .services.youtube import YouTubeVideoError, canonical_url, extract_video_id


class YouTubeLearningCreateView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = YouTubeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            video_id = extract_video_id(serializer.validated_data['url'])
        except YouTubeVideoError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        path = LearningPath.objects.filter(user=request.user, video_id=video_id).first()
        if path and not serializer.validated_data['retry']:
            return Response(LearningPathSerializer(path).data, status=status.HTTP_200_OK)
        if path:
            path.status = LearningPath.Status.PROCESSING
            path.processing_stage = 'Validating video'
            path.processing_progress = 0
            path.failure_reason = ''
            path.save(update_fields=['status', 'processing_stage', 'processing_progress', 'failure_reason', 'updated_at'])
        else:
            path = LearningPath.objects.create(user=request.user, youtube_url=canonical_url(video_id), video_id=video_id)
        enqueue_learning_path(path.id)
        return Response(LearningPathSerializer(path).data, status=status.HTTP_202_ACCEPTED)


class LearningPathListView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request): return Response(LearningPathSerializer(LearningPath.objects.filter(user=request.user).prefetch_related('levels'), many=True).data)


class LearningPathDetailView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request, path_id): return Response(LearningPathSerializer(get_object_or_404(LearningPath.objects.prefetch_related('levels'), id=path_id, user=request.user)).data)
    def delete(self, request, path_id):
        path = get_object_or_404(LearningPath, id=path_id, user=request.user)
        path.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LearningPathStatusView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request, path_id):
        path = get_object_or_404(LearningPath, id=path_id, user=request.user)
        return Response({'id': path.id, 'status': path.status, 'stage': path.processing_stage, 'progress': path.processing_progress, 'failure_reason': path.failure_reason})


class LevelListView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request, path_id): return Response(LearningLevelSerializer(LearningLevel.objects.filter(learning_path__id=path_id, learning_path__user=request.user), many=True).data)


class LevelDetailView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request, path_id, level_id): return Response(LearningLevelSerializer(get_object_or_404(LearningLevel, id=level_id, learning_path__id=path_id, learning_path__user=request.user)).data)


class LevelStartView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def post(self, request, path_id, level_id):
        level = get_object_or_404(LearningLevel, id=level_id, learning_path__id=path_id, learning_path__user=request.user)
        if level.status == LearningLevel.Status.LOCKED:
            return Response({'detail': f'Complete Level {level.order - 1} checkpoint to unlock this level.'}, status=status.HTTP_409_CONFLICT)
        if level.status == LearningLevel.Status.AVAILABLE:
            level.status = LearningLevel.Status.STARTED; level.started_at = timezone.now(); level.save(update_fields=['status', 'started_at'])
        return Response(LearningLevelSerializer(level).data)


class LevelCompleteView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def post(self, request, path_id, level_id):
        level = get_object_or_404(LearningLevel, id=level_id, learning_path__id=path_id, learning_path__user=request.user)
        if not level.attempts.filter(correct=True).exists():
            return Response({'detail': 'Pass this level checkpoint before completing it.'}, status=status.HTTP_409_CONFLICT)
        return Response(LearningLevelSerializer(level).data)


class CheckpointView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def post(self, request, path_id):
        serializer = CheckpointSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        path = get_object_or_404(LearningPath, id=path_id, user=request.user)
        level = get_object_or_404(LearningLevel, id=serializer.validated_data['level_id'], learning_path=path)
        if level.status == LearningLevel.Status.LOCKED:
            return Response({'detail': 'This level is locked.'}, status=status.HTTP_409_CONFLICT)
        attempt = evaluate_checkpoint(request.user, path, level, serializer.validated_data['answer'])
        path.refresh_from_db(); level.refresh_from_db()
        return Response({'attempt': CheckpointAttemptSerializer(attempt).data, 'level': LearningLevelSerializer(level).data, 'path': LearningPathSerializer(path).data})


class NotesView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request, path_id):
        path = get_object_or_404(LearningPath, id=path_id, user=request.user)
        return Response({'title': path.title, 'youtube_url': path.youtube_url, 'notes': path.cumulative_notes})


class FinalChallengeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, path_id):
        path = get_object_or_404(LearningPath, id=path_id, user=request.user)
        if path.levels.exclude(status=LearningLevel.Status.COMPLETED).exists():
            return Response({'detail': 'Complete every level before starting the final challenge.'}, status=status.HTTP_409_CONFLICT)
        return Response(LearningPathSerializer(path).data['final_challenge'])

    def post(self, request, path_id):
        serializer = FinalChallengeSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        path = get_object_or_404(LearningPath, id=path_id, user=request.user)
        if path.levels.exclude(status=LearningLevel.Status.COMPLETED).exists():
            return Response({'detail': 'Complete every level before submitting the final challenge.'}, status=status.HTTP_409_CONFLICT)
        try:
            result = evaluate_final_challenge(path, serializer.validated_data['answers'])
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'result': result, 'path': LearningPathSerializer(path).data})


class ResumeView(LearningPathDetailView):
    def post(self, request, path_id): return self.get(request, path_id)
