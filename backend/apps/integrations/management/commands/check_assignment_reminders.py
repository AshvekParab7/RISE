from django.core.management.base import BaseCommand

from apps.integrations.services.assignment_reminders import send_due_assignment_reminders


class Command(BaseCommand):
    help = 'Send one-time WhatsApp reminders for incomplete Classroom assignments due in two days.'

    def handle(self, *args, **options):
        summary = send_due_assignment_reminders()
        self.stdout.write(self.style.SUCCESS(str(summary)))
