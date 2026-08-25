from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, serializers, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.intelligence.services.recommendation_engine import build_context, build_next_action
from apps.tasks.serializers import PlannerEventSerializer

from .models import ExamScheduleUpload
from .serializers import (
    ConfirmExamScheduleSerializer,
    ExamScheduleUploadSerializer,
    PlanCommitSerializer,
    PlanPreviewSerializer,
)
from .services.exam_schedule_parser import confirm_exam_rows, create_rows_for_upload
from .services.overview import build_overview
from .services.plan_builder import build_plan_preview, commit_plan


class OverviewView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        start_date = parse_date(request.query_params.get('start_date', '')) or timezone.localdate()
        try:
            days = int(request.query_params.get('days', 7))
        except (TypeError, ValueError):
            return Response({'detail': 'days must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)
        if not 1 <= days <= 14:
            return Response({'detail': 'days must be between 1 and 14.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(build_overview(request.user, start_date, days))


class NextActionView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        return Response(build_next_action(build_context(request.user)))


class PlanPreviewView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(request=PlanPreviewSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        serializer = PlanPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        return Response(build_plan_preview(
            request.user,
            data.get('start_date') or timezone.localdate(),
            data['days'],
            data['daily_minutes'],
            data['day_start'],
            data['day_end'],
        ))


class PlanCommitView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(request=PlanCommitSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        serializer = PlanCommitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            events = commit_plan(request.user, serializer.validated_data['blocks'])
        except ValidationError as exc:
            detail = exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
            return Response({'detail': detail}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'created': PlannerEventSerializer(events, many=True).data, 'count': len(events)}, status=status.HTTP_201_CREATED)


class ExamScheduleUploadCreateView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    @extend_schema(request=ExamScheduleUploadSerializer, responses=ExamScheduleUploadSerializer)
    def post(self, request):
        serializer = ExamScheduleUploadSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        upload = serializer.save(student=request.user, original_filename=request.FILES['file'].name)
        create_rows_for_upload(upload, request.data.get('ocr_text', ''))
        upload.refresh_from_db()
        return Response(ExamScheduleUploadSerializer(upload, context={'request': request}).data, status=status.HTTP_201_CREATED)


class ExamScheduleUploadDetailView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses=ExamScheduleUploadSerializer)
    def get(self, request, upload_id):
        upload = get_object_or_404(ExamScheduleUpload.objects.prefetch_related('rows'), id=upload_id, student=request.user)
        return Response(ExamScheduleUploadSerializer(upload, context={'request': request}).data)


class ExamScheduleUploadConfirmView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(request=ConfirmExamScheduleSerializer, responses=ExamScheduleUploadSerializer)
    def post(self, request, upload_id):
        upload = get_object_or_404(ExamScheduleUpload, id=upload_id, student=request.user)
        serializer = ConfirmExamScheduleSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        row_ids = [item['id'] for item in serializer.validated_data['rows']]
        if len(row_ids) != len(set(row_ids)):
            raise serializers.ValidationError({'rows': 'Each exam row may be submitted only once.'})
        try:
            confirm_exam_rows(upload, serializer.validated_data['rows'])
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        upload.refresh_from_db()
        return Response(ExamScheduleUploadSerializer(upload, context={'request': request}).data)
