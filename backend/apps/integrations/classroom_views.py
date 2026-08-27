from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from .models import GoogleConnection
from .models_classroom import GoogleCourse, GoogleCoursework, GoogleMaterial
from .services.classroom_sync import ClassroomSyncEngine
from .services.google_classroom import ClassroomApiError
from .services.google_tokens import GoogleAuthenticationRequired
from .services.google_classroom_gis import CLASSROOM_GIS_SCOPES, ClassroomTokenError, authorize_classroom_connection

class ClassroomStatusView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        connection = GoogleConnection.objects.filter(user=request.user, is_active=True).first()
        if not connection:
            return Response({'connected': False, 'last_synced_at': None, 'courses': 0, 'assignments': 0, 'materials': 0, 'sync_status': 'NOT_CONNECTED'})
        courses = GoogleCourse.objects.filter(google_connection=connection)
        return Response({'connected': True, 'last_synced_at': connection.last_synced_at, 'courses': courses.count(), 'assignments': GoogleCoursework.objects.filter(google_course__in=courses).count(), 'materials': GoogleMaterial.objects.filter(google_course__in=courses).count(), 'sync_status': 'SUCCESS' if connection.last_synced_at else 'NOT_SYNCED'})

class ClassroomSyncView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        connection = GoogleConnection.objects.filter(user=request.user, is_active=True).first()
        if not connection:
            return Response({'detail': 'Classroom access needs your permission. Connect Classroom to continue.'}, status=status.HTTP_403_FORBIDDEN)
        missing_scopes = sorted(set(CLASSROOM_GIS_SCOPES) - set(connection.scopes or []))
        if missing_scopes:
            return Response({'detail': 'Additional Google Classroom permission is required to download materials.', 'missing_scopes': missing_scopes}, status=status.HTTP_403_FORBIDDEN)
        try:
            result = ClassroomSyncEngine(connection).sync()
            return Response(result)
        except GoogleAuthenticationRequired:
            return Response({'detail': 'Google authorization is required before syncing Classroom.'}, status=status.HTTP_403_FORBIDDEN)
        except ClassroomApiError as exc:
            return Response({'detail': 'Google Classroom is unavailable right now.'}, status=exc.status if exc.status in (403, 404, 429) else status.HTTP_502_BAD_GATEWAY)
        except Exception:
            return Response({'detail': 'Classroom synchronization failed.'}, status=status.HTTP_502_BAD_GATEWAY)

class ClassroomAuthorizeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        access_token = request.data.get('access_token')
        try:
            connection = authorize_classroom_connection(request.user, access_token)
        except ClassroomTokenError as exc:
            return Response({'detail': str(exc), 'missing_scopes': exc.missing_scopes}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'authorized': True, 'scopes': connection.scopes, 'expires_at': connection.token_expiry})
