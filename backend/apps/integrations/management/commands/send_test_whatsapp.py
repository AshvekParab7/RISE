import re

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.integrations.services.twilio_whatsapp import (
    TwilioWhatsAppError,
    send_assignment_reminder,
)


class Command(BaseCommand):
    help = 'Send one manual rise_assignment WhatsApp template message.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            dest='to',
            help='Override the configured test destination (international format, e.g. +919876543210).',
        )

    def handle(self, *args, **options):
        destination = options.get('to') or settings.TWILIO_TEST_WHATSAPP_NUMBER
        if destination and not destination.startswith('whatsapp:'):
            destination = f'whatsapp:{destination}'
        if not destination:
            raise CommandError(
                'Set TWILIO_TEST_WHATSAPP_NUMBER in backend/.env or pass --to +countrycode...'
            )
        if not re.fullmatch(r'whatsapp:\+\d{7,15}', destination):
            raise CommandError(
                'The test destination must be a real WhatsApp number in international format, '
                'for example whatsapp:+919876543210.'
            )

        try:
            result = send_assignment_reminder(
                destination,
                'RISE WhatsApp test assignment',
                '31 Aug 2026 at 5:00 PM',
            )
        except TwilioWhatsAppError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"WhatsApp template sent: SID={result['sid']} status={result['status']}"
            )
        )
