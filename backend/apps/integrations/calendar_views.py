from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from .models import GoogleConnection
from .models_calendar import GoogleCalendar, GoogleCalendarEvent
from .services.calendar_sync import CalendarSyncEngine
from .services.google_calendar import CalendarApiError
from .services.google_tokens import GoogleAuthenticationRequired

class CalendarStatusView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        connection = GoogleConnection.objects.filter(user=request.user, is_active=True).first()
        calendars = GoogleCalendar.objects.filter(google_connection=connection, is_active=True) if connection else GoogleCalendar.objects.none()
        return Response({'connected': bool(connection), 'last_synced_at': connection.last_synced_at if connection else None, 'selected_calendars': calendars.filter(selected=True).count(), 'events': GoogleCalendarEvent.objects.filter(google_calendar__in=calendars, is_active=True).count(), 'sync_status': 'SUCCESS' if connection and connection.last_synced_at else 'NOT_SYNCED'})

class CalendarListView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        connection = GoogleConnection.objects.filter(user=request.user, is_active=True).first()
        if not connection: return Response({'detail': 'Connect Google before configuring Calendar.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            remote, _ = __import__('apps.integrations.services.google_calendar', fromlist=['GoogleCalendarService']).GoogleCalendarService(connection).get_calendar_list()
        except GoogleAuthenticationRequired: return Response({'detail': 'Google authorization is required.'}, status=status.HTTP_403_FORBIDDEN)
        except Exception: return Response({'detail': 'Google Calendar is unavailable right now.'}, status=status.HTTP_502_BAD_GATEWAY)
        output = []
        for item in remote:
            calendar, _ = GoogleCalendar.objects.update_or_create(google_connection=connection, google_calendar_id=item['id'], defaults={'summary': item.get('summary', ''), 'description': item.get('description', ''), 'time_zone': item.get('timeZone', ''), 'access_role': item.get('accessRole', ''), 'is_active': item.get('deleted') is not True})
            output.append({'id': calendar.google_calendar_id, 'summary': calendar.summary, 'time_zone': calendar.time_zone, 'selected': calendar.selected, 'access_role': calendar.access_role})
        return Response(output)
    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        connection = GoogleConnection.objects.filter(user=request.user, is_active=True).first()
        selected_ids = set(request.data.get('calendar_ids', []))
        calendars = GoogleCalendar.objects.filter(google_connection=connection, is_active=True)
        calendars.update(selected=False)
        calendars.filter(google_calendar_id__in=selected_ids).update(selected=True)
        return Response({'selected_calendars': calendars.filter(selected=True).count()})
    @extend_schema(request=OpenApiTypes.OBJECT, responses={204: None})
    def delete(self, request):
        connection = GoogleConnection.objects.filter(user=request.user, is_active=True).first()
        GoogleCalendar.objects.filter(google_connection=connection, google_calendar_id=request.data.get('calendar_id')).update(selected=False, is_active=False)
        return Response(status=status.HTTP_204_NO_CONTENT)

class CalendarSyncView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        connection = GoogleConnection.objects.filter(user=request.user, is_active=True).first()
        if not connection: return Response({'detail': 'Connect Google before syncing Calendar.'}, status=status.HTTP_400_BAD_REQUEST)
        try: return Response(CalendarSyncEngine(connection).sync(request.data.get('calendar_ids')))
        except GoogleAuthenticationRequired: return Response({'detail': 'Google authorization is required.'}, status=status.HTTP_403_FORBIDDEN)
        except CalendarApiError as exc: return Response({'detail': 'Google Calendar is unavailable right now.'}, status=exc.status if exc.status in (403, 404, 429) else status.HTTP_502_BAD_GATEWAY)
        except Exception: return Response({'detail': 'Calendar synchronization failed.'}, status=status.HTTP_502_BAD_GATEWAY)
