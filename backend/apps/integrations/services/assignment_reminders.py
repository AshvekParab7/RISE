import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.tasks.models import Task
from .twilio_whatsapp import TwilioWhatsAppError, send_assignment_reminder
from ..models import WhatsAppAssignmentReminder

logger = logging.getLogger(__name__)


def _whatsapp_destination(phone_number):
    value = str(phone_number or '').strip()
    if value.startswith('whatsapp:'):
        return value
    return f'whatsapp:{value}' if value.startswith('+') else ''


def _deadline_label(deadline):
    return timezone.localtime(deadline).strftime('%b %d, %Y at %I:%M %p').replace(' 0', ' ')


def send_due_assignment_reminders(now=None):
    now = now or timezone.now()
    target_date = timezone.localtime(now).date() + timedelta(days=2)
    tasks = Task.objects.filter(
        source=Task.Source.GOOGLE_CLASSROOM,
        status__in=(Task.Status.TODO, Task.Status.IN_PROGRESS),
        deadline__date=target_date,
    ).exclude(student__phone_number='').select_related('student')
    summary = {'eligible': 0, 'sent': 0, 'skipped': 0, 'failed': 0, 'errors': []}
    for task in tasks.iterator():
        summary['eligible'] += 1
        destination = _whatsapp_destination(task.student.phone_number)
        if not destination:
            summary['skipped'] += 1
            continue
        with transaction.atomic():
            reminder, _ = WhatsAppAssignmentReminder.objects.select_for_update().get_or_create(task=task)
            if reminder.sent_at:
                summary['skipped'] += 1
                continue
            try:
                result = send_assignment_reminder(destination, task.title, _deadline_label(task.deadline))
            except TwilioWhatsAppError as exc:
                reminder.error = str(exc)
                reminder.save(update_fields=('error', 'updated_at'))
                summary['failed'] += 1
                summary['errors'].append({'task_id': str(task.id), 'message': str(exc)})
                logger.error('Assignment reminder failed task_id=%s student_id=%s', task.id, task.student_id, exc_info=True)
                continue
            reminder.sent_at = now
            reminder.message_sid = result['sid']
            reminder.error = ''
            reminder.save(update_fields=('sent_at', 'message_sid', 'error', 'updated_at'))
            summary['sent'] += 1
            logger.info('Assignment reminder sent task_id=%s student_id=%s message_sid=%s', task.id, task.student_id, result['sid'])
    return summary
