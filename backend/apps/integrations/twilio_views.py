from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services.twilio_whatsapp import TwilioWhatsAppError, send_whatsapp_message


class TwilioWhatsAppTestView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        if not settings.DEBUG:
            return Response({'detail': 'Twilio test messaging is disabled outside development.'}, status=status.HTTP_404_NOT_FOUND)
        destination = str(request.data.get('to', '')).strip()
        if not destination:
            return Response({'detail': 'Provide a test WhatsApp destination.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = send_whatsapp_message(destination, 'RISE WhatsApp test successful 🚀')
        except TwilioWhatsAppError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({'sent': True, **result}, status=status.HTTP_201_CREATED)