import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class TwilioWhatsAppError(Exception):
    pass


def send_whatsapp_message(to, body):
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN or not settings.TWILIO_WHATSAPP_NUMBER:
        raise TwilioWhatsAppError('Twilio WhatsApp is not configured.')
    if not to.startswith('whatsapp:+'):
        raise TwilioWhatsAppError('WhatsApp destination must use the whatsapp:+countrycode format.')
    try:
        from twilio.rest import Client
        message = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN).messages.create(
            body=body,
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            to=to,
        )
    except Exception as exc:
        logger.exception('Twilio WhatsApp send failed to=%s error_type=%s', to, type(exc).__name__)
        raise TwilioWhatsAppError(f'Twilio WhatsApp send failed: {exc}') from exc
    logger.info('Twilio WhatsApp message accepted to=%s message_sid=%s status=%s', to, message.sid, getattr(message, 'status', 'unknown'))
    return {'sid': message.sid, 'status': getattr(message, 'status', 'unknown'), 'to': to}


def send_assignment_reminder(to, assignment_name, deadline):
    if not settings.TWILIO_ASSIGNMENT_CONTENT_SID:
        raise TwilioWhatsAppError('Twilio assignment template is not configured.')
    if not to.startswith('whatsapp:+'):
        raise TwilioWhatsAppError('WhatsApp destination must use the whatsapp:+countrycode format.')
    try:
        from twilio.rest import Client
        message = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN).messages.create(
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            to=to,
            content_sid=settings.TWILIO_ASSIGNMENT_CONTENT_SID,
            content_variables=json.dumps({'1': assignment_name, '2': deadline}),
        )
    except Exception as exc:
        logger.exception('Twilio assignment reminder failed to=%s error_type=%s', to, type(exc).__name__)
        raise TwilioWhatsAppError(f'Twilio assignment reminder failed: {exc}') from exc
    logger.info('Twilio assignment reminder accepted to=%s message_sid=%s status=%s', to, message.sid, getattr(message, 'status', 'unknown'))
    return {'sid': message.sid, 'status': getattr(message, 'status', 'unknown'), 'to': to}