from datetime import datetime

from django.utils import timezone
from .priority_engine import calculate_subject_priority, calculate_topic_priority
from .workload_engine import build_workload_plan

def build_context(user, day=None):
    from apps.academics.models import CollegeClass, Exam, Subject, Topic
    from apps.integrations.models_calendar import GoogleCalendarEvent
    from apps.tasks.models import StudySession, Task
    current = user.semesters.filter(is_current=True).first() or user.semesters.first()
    subjects = list(Subject.objects.filter(semester__student=user, semester=current).prefetch_related('topics')) if current else []
    topics = list(Topic.objects.filter(subject__in=subjects).select_related('subject'))
    exams = list(Exam.objects.filter(semester__student=user, semester=current).select_related('subject')) if current else []
    tasks = list(Task.objects.filter(student=user).select_related('subject'))
    sessions = list(StudySession.objects.filter(student=user).select_related('subject'))
    blocked = []
    planning_date = day or timezone.localdate()
    for item in CollegeClass.objects.filter(semester__student=user, semester=current) if current else []:
        if item.day_of_week != planning_date.weekday():
            continue
        start = timezone.make_aware(datetime.combine(planning_date, item.start_time))
        end = timezone.make_aware(datetime.combine(planning_date, item.end_time))
        blocked.append((start, end))
    for event in GoogleCalendarEvent.objects.filter(google_calendar__google_connection__user=user, is_active=True):
        if event.start_datetime and event.end_datetime: blocked.append((event.start_datetime, event.end_datetime))
    return {'today': day or timezone.localdate(), 'now': timezone.now(), 'subjects': subjects, 'topics': topics, 'exams': exams, 'tasks': tasks, 'sessions': sessions, 'exam_dates': {exam.subject_id: exam.exam_date for exam in exams}, 'topics_by_subject': {subject.id: list(subject.topics.all()) for subject in subjects}, 'tasks_by_subject': {subject.id: [task for task in tasks if task.subject_id == subject.id] for subject in subjects}, 'sessions_by_subject': {subject.id: [session for session in sessions if session.subject_id == subject.id] for subject in subjects}, 'blocked_windows': blocked}

def calculate_priorities(context):
    topics = [calculate_topic_priority(topic, context) for topic in context['topics']]
    if not topics: topics = [calculate_subject_priority(subject, context) for subject in context['subjects']]
    return sorted(topics, key=lambda item: (-item['priority_score'], item.get('topic', item.get('subject', ''))))

def recalculate_subject_priorities(context):
    results = [calculate_subject_priority(subject, context) for subject in context['subjects']]
    for result in results:
        subject = next(subject for subject in context['subjects'] if str(subject.id) == result['subject_id'])
        if subject.priority_score != result['priority_score']:
            subject.priority_score = result['priority_score']
            subject.save(update_fields=('priority_score', 'updated_at'))
    return results

def build_next_action(context):
    priorities = calculate_priorities(context)
    if not priorities: return {'action': None, 'reason': 'Add a subject, topic, or exam to let RISE prioritize your next move.'}
    item = priorities[0]
    duration = 45 if item.get('topic') else 30
    reason = item['reasons'][0]['label'] if item.get('reasons') else 'This is currently your highest-impact academic priority.'
    return {'action': {'type': 'STUDY_TOPIC' if item.get('topic') else 'STUDY_SUBJECT', 'subject': item.get('subject'), 'topic': item.get('topic'), 'duration_minutes': duration, 'priority_score': item['priority_score']}, 'reason': reason}

def build_daily_plan(context, available_minutes=90):
    priorities = calculate_priorities(context)
    return build_workload_plan(priorities, context['tasks'], context, available_minutes)
