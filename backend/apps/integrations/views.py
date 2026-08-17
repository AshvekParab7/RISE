import logging
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from .models import GoogleConnection
from .serializers import GoogleConnectionSerializer
from .services.google_oauth import CALENDAR_SCOPES, CLASSROOM_SCOPES, authorization_url, exchange_callback, revoke

logger = logging.getLogger(__name__)

class GoogleConnectionView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    @extend_schema(responses=GoogleConnectionSerializer)
    def get(self, request):
        connection = GoogleConnection.objects.filter(user=request.user, is_active=True).first()
        if not connection:
            return Response({'connected': False, 'email': None, 'display_name': None, 'picture': None, 'scopes': [], 'connected_at': None, 'last_synced_at': None, 'is_active': False})
        return Response(GoogleConnectionSerializer(connection).data)
    @extend_schema(request=None, responses={204: None})
    def delete(self, request):
        connection = GoogleConnection.objects.filter(user=request.user, is_active=True).first()
        if connection:
            revoke(connection)
        return Response(status=status.HTTP_204_NO_CONTENT)

class GoogleOAuthStartView(APIView):
    permission_classes = (permissions.AllowAny,)
    @extend_schema(responses={200: OpenApiTypes.OBJECT, 503: OpenApiTypes.OBJECT})
    def get(self, request):
        try:
            integration = request.query_params.get('integration')
            if integration in ('classroom', 'calendar') and not request.user.is_authenticated:
                return Response({'detail': 'Authentication is required before connecting an integration.'}, status=status.HTTP_401_UNAUTHORIZED)
            extra_scopes = CLASSROOM_SCOPES if integration == 'classroom' else CALENDAR_SCOPES if integration == 'calendar' else ()
            url = authorization_url(request, extra_scopes)
            if request.query_params.get('redirect') == '1':
                return HttpResponseRedirect(url)
            return Response({'authorization_url': url})
        except ImproperlyConfigured:
            return Response({'detail': 'Google OAuth is not configured.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

class GoogleOAuthCallbackView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()
    @extend_schema(responses={302: None, 400: OpenApiTypes.OBJECT})
    def get(self, request):
        result = exchange_callback(request)
        if not isinstance(result, GoogleConnection):
            return result
        refresh = RefreshToken.for_user(result.user)
        logger.warning('Google OAuth callback jwt_creation=success')
        redirect = settings.GOOGLE_SUCCESS_REDIRECT_URI.split('#', 1)[0]
        return HttpResponseRedirect(f'{redirect}#rise_access={refresh.access_token}&rise_refresh={refresh}')
