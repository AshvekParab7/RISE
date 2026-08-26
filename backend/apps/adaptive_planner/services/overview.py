from datetime import datetime, timedelta

from django.utils import timezone

from apps.academics.models import CollegeClass
from apps.integrations.models_calendar import GoogleCalendarEvent
from apps.integrations.models_classroom import GoogleCoursework
from apps.intelligence.services.recommendation_engine import build_context, build_daily_plan, build_next_action, calculate_priorities
from apps.tasks.models import PlannerEvent, Task
from apps.resources.models import Resource


def _resource_data(resource):
    return {
        'id': str(resource.id),
        'title': resource.title,
        'resource_type': resource.resource_type,
        'source': resource.source,
        'is_ai_ready': resource.is_ai_ready,
        'file': resource.file.url if resource.file else '',
    }


def _event_data(event, source, subject_name='', read_only=False, **extra):
    result = {
        'id': str(event.id),
        'title': event.title if hasattr(event, 'title') else event.summary,
        'start_at': event.start_at.isoformat() if hasattr(event, 'start_at') else event.start_datetime.isoformat() if event.start_datetime else None,
        'end_at': event.end_at.isoformat() if hasattr(event, 'end_at') else event.end_datetime.isoformat() if event.end_datetime else None,
        'source': source,
        'subject': subject_name,
        'read_only': read_only,
    }
    result.update(extra)
    return result


def _timetable(user, start_date, days, context):
    end_date = start_date + timedelta(days=days)
    events = []
    planner_events = PlannerEvent.objects.filter(student=user, start_at__date__gte=start_date, start_at__date__lt=end_date).select_related('subject')
    for event in planner_events:
        events.append(_event_data(event, 'RISE', event.subject.name if event.subject else ''))
    semester = context.get('semester')
    classes = CollegeClass.objects.filter(semester=semester).select_related('subject') if semester else CollegeClass.objects.none()
    for day_offset in range(days):
        day = start_date + timedelta(days=day_offset)
        for college_class in classes:
            if college_class.day_of_week != day.weekday():
                continue
            start = timezone.make_aware(datetime.combine(day, college_class.start_time))
            end = timezone.make_aware(datetime.combine(day, college_class.end_time))
            events.append({
                'id': str(college_class.id),
                'title': college_class.subject.name,
                'start_at': start.isoformat(),
                'end_at': end.isoformat(),
                'source': 'COLLEGE',
                'subject': college_class.subject.name,
                'room': college_class.room,
                'instructor': college_class.instructor,
                'read_only': True,
            })
    calendar_events = GoogleCalendarEvent.objects.filter(
        google_calendar__google_connection__user=user,
        is_active=True,
        start_datetime__lt=timezone.make_aware(datetime.combine(end_date, datetime.min.time())),
        end_datetime__gt=timezone.make_aware(datetime.combine(start_date, datetime.min.time())),
    )
    for event in calendar_events:
        events.append(_event_data(event, 'GOOGLE_CALENDAR', read_only=True, all_day=event.all_day, link=event.html_link))
    for exam in context.get('exams', []):
        if not start_date <= exam.exam_date < end_date:
            continue
        start = timezone.make_aware(datetime.combine(exam.exam_date, exam.start_time))
        end = timezone.make_aware(datetime.combine(exam.exam_date, exam.end_time))
        events.append({
            'id': str(exam.id),
            'title': exam.title,
            'start_at': start.isoformat(),
            'end_at': end.isoformat(),
            'source': 'EXAM',
            'subject': exam.subject.name,
            'venue': exam.venue,
            'read_only': True,
        })
    return sorted(events, key=lambda event: event.get('start_at') or '')


def _mission(exam, today, topics_by_subject):
    topics = topics_by_subject.get(exam.subject_id, [])
    progress = round(sum(topic.mastery_percentage for topic in topics) / len(topics)) if topics else exam.subject.mastery_percentage
    days_remaining = (exam.exam_date - today).days
    if days_remaining < 0:
        status = 'OVERDUE'
    elif progress >= 80:
        status = 'READY'
    elif days_remaining <= 7 and progress < 60:
        status = 'AT_RISK'
    elif progress > 0:
        status = 'IN_PROGRESS'
    else:
        status = 'NOT_STARTED'
    weak_topics = sorted(topics, key=lambda topic: topic.mastery_percentage)[:4]
    return {
        'id': str(exam.id),
        'title': exam.title,
        'subject_id': str(exam.subject_id),
        'subject': exam.subject.name,
        'exam_date': exam.exam_date.isoformat(),
        'start_time': exam.start_time.isoformat(),
        'end_time': exam.end_time.isoformat(),
        'venue': exam.venue,
        'source': exam.source,
        'days_remaining': days_remaining,
        'progress_percentage': progress,
        'total_topics': len(topics),
        'mastered_topics': sum(topic.mastery_percentage >= 80 for topic in topics),
        'difficulty': exam.subject.difficulty,
        'difficulty_label': exam.subject.get_difficulty_display(),
        'status': status,
        'weak_topics': [{'id': str(topic.id), 'name': topic.name, 'mastery_percentage': topic.mastery_percentage} for topic in weak_topics],
    }


def _deadline_rescue(user):
    tasks = Task.objects.filter(student=user, source=Task.Source.GOOGLE_CLASSROOM).exclude(status=Task.Status.COMPLETED).select_related('subject').order_by('deadline', '-priority')[:8]
    result = []
    today = timezone.localdate()
    for task in tasks:
        coursework = GoogleCoursework.objects.filter(rise_task=task).first()
        result.append({
            'id': str(task.id),
            'title': task.title,
            'description': task.description,
            'subject': task.subject.name if task.subject else '',
            'deadline': task.deadline.isoformat(),
            'days_remaining': (task.deadline.date() - today).days,
            'estimated_minutes': task.estimated_minutes,
            'priority': task.priority,
            'status': task.status,
            'link': coursework.alternate_link if coursework else '',
        })
    return result


def build_overview(user, start_date=None, days=7):
    start_date = start_date or timezone.localdate()
    context = build_context(user, day=start_date)
    subjects = context['subjects']
    topics_by_subject = context['topics_by_subject']
    semester = context.get('semester')
    resources = Resource.objects.filter(student=user, subject__semester=semester).select_related('subject').order_by('-is_ai_ready', '-uploaded_at') if semester else Resource.objects.none()
    resources_by_subject = {}
    for resource in resources:
        resources_by_subject.setdefault(resource.subject_id, []).append(_resource_data(resource))
    priorities = calculate_priorities(context)
    topics = {str(topic.id): topic for topic in context['topics']}
    subjects_by_id = {str(subject.id): subject for subject in subjects}
    weak_topics = []
    for priority in priorities[:8]:
        topic = topics.get(priority.get('topic_id'))
        subject = subjects_by_id.get(priority.get('subject_id'))
        weak_topics.append({
            **priority,
            'mastery_percentage': topic.mastery_percentage if topic else subject.mastery_percentage if subject else 0,
            'difficulty': subject.difficulty if subject else '',
            'difficulty_label': subject.get_difficulty_display() if subject else '',
            'resources': resources_by_subject.get(subject.id, [])[:3] if subject else [],
        })
    exams = sorted(context['exams'], key=lambda exam: (exam.exam_date, exam.start_time))
    daily_plan = build_daily_plan(context, 90)
    return {
        'generated_at': timezone.now().isoformat(),
        'start_date': start_date.isoformat(),
        'days': days,
        'subjects': [{'id': str(subject.id), 'name': subject.name, 'code': subject.code, 'difficulty': subject.difficulty} for subject in subjects],
        'timetable': _timetable(user, start_date, days, context),
        'exam_missions': [_mission(exam, start_date, topics_by_subject) for exam in exams],
        'weak_topics': weak_topics,
        'deadline_rescue': _deadline_rescue(user),
        'next_action': build_next_action(context),
        'overall_status': daily_plan['status'],
        'resource_count': resources.count(),
        'subjects_count': len(subjects),
    }
