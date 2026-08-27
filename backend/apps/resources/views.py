from io import BytesIO
import logging
from urllib.parse import parse_qs, urlparse

from django.http import FileResponse
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import Resource
from .serializers import ResourceSerializer
from apps.ai.services.resource_processing import process_resource
from apps.integrations.services.google_classroom import ClassroomApiError, GoogleClassroomService
from apps.integrations.services.google_tokens import GoogleAuthenticationRequired

logger = logging.getLogger(__name__)


def _drive_id_from_url(value):
    if not value:
        return ''
    parsed = urlparse(value)
    query_id = parse_qs(parsed.query).get('id', [''])[-1]
    if query_id:
        return query_id
    parts = [part for part in parsed.path.split('/') if part]
    for marker in ('d', 'file'):
        if marker in parts:
            index = parts.index(marker)
            if index + 1 < len(parts):
                return parts[index + 1]
    return ''

class ResourceViewSet(viewsets.ModelViewSet):
    serializer_class = ResourceSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_value_regex = '[0-9a-f-]{36}'
    def get_queryset(self): return Resource.objects.filter(student=self.request.user).select_related('subject', 'subject__semester')
    def perform_create(self, serializer):
        resource = serializer.save()
        process_resource(resource)

    @action(detail=True, methods=('get',), url_path='preview')
    def preview(self, request, pk=None):
        resource = self.get_object()
        if resource.file:
            return FileResponse(resource.file.open('rb'), as_attachment=False, filename=resource.file.name.rsplit('/', 1)[-1])
        material = resource.google_materials.select_related('google_course__google_connection').first()
        if not material:
            logger.warning('Resource preview failed stage=relation resource_id=%s user_id=%s', resource.id, request.user.id)
            return Response({'detail': 'This resource has no downloadable file.'}, status=status.HTTP_404_NOT_FOUND)
        connection = material.google_course.google_connection
        if connection.user_id != request.user.id:
            logger.error('Resource preview denied stage=ownership resource_id=%s connection_id=%s user_id=%s', resource.id, connection.id, request.user.id)
            return Response({'detail': 'This Google resource is not connected to your RISE account.'}, status=status.HTTP_403_FORBIDDEN)
        drive_file_id = material.drive_file_id or _drive_id_from_url(material.source_url)
        if not drive_file_id:
            logger.error('Resource preview failed stage=file_id resource_id=%s material_id=%s source_url_present=%s', resource.id, material.google_material_id, bool(material.source_url))
            return Response({'detail': 'Google Drive file ID is missing for this resource.'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        try:
            logger.info('Resource preview fetch stage=drive resource_id=%s drive_file_id=%s user_id=%s', resource.id, drive_file_id, request.user.id)
            service = GoogleClassroomService(connection)
            downloaded = service.download_drive_file(drive_file_id, material.title, material.mime_type)
            if not downloaded:
                logger.warning('Resource preview failed stage=empty_response resource_id=%s drive_file_id=%s', resource.id, drive_file_id)
                return Response({'detail': 'This Classroom item does not contain a downloadable file.'}, status=status.HTTP_404_NOT_FOUND)
            logger.info('Resource preview success resource_id=%s drive_file_id=%s mime_type=%s bytes=%s', resource.id, drive_file_id, downloaded['mime_type'], len(downloaded['content']))
            return FileResponse(
                BytesIO(downloaded['content']),
                as_attachment=False,
                filename=downloaded['filename'],
                content_type=downloaded['mime_type'],
            )
        except (GoogleAuthenticationRequired, ClassroomApiError) as exc:
            logger.error('Resource preview failed stage=google_api resource_id=%s drive_file_id=%s error_type=%s', resource.id, drive_file_id, type(exc).__name__, exc_info=True)
            return Response({'detail': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as exc:
            logger.error('Resource preview failed stage=unexpected resource_id=%s drive_file_id=%s error_type=%s', resource.id, drive_file_id, type(exc).__name__, exc_info=True)
            return Response({'detail': 'Google Drive could not provide this resource.'}, status=status.HTTP_502_BAD_GATEWAY)
