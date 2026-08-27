from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.academics.models import Subject
from apps.intelligence.services.recommendation_engine import build_context, calculate_priorities
from apps.resources.models import Resource
from apps.tasks.models import PlannerEvent, Task


def _aware(day, value):
    return timezone.make_aware(datetime.combine(day, value))


def _free_windows(start, end, blocked):
    cursor = start
    windows = []
    for block_start, block_end in sorted(blocked):
        if block_end <= start or block_start >= end:
            continue
        block_start = max(start, block_start)
        block_end = min(end, block_end)
        if cursor < block_start:
            windows.append((cursor, block_start))
        cursor = max(cursor, block_end)
    if cursor < end:
        windows.append((cursor, end))
    return windows


def _resource_map(user):
    resources = Resource.objects.filter(student=user, is_ai_ready=True, processing_status=Resource.ProcessingStatus.READY).select_related('subject').order_by('-uploaded_at')
    result = {}
    for resource in resources:
        result.setdefault(str(resource.subject_id), []).append({
            'id': str(resource.id),
            'title': resource.title,
            'resource_type': resource.resource_type,
            'source': resource.source,
            'file': resource.file.url if resource.file else '',
        })
    return result


def _existing_blockers(user, start, end):
    events = PlannerEvent.objects.filter(student=user, start_at__lt=end).select_related('subject')
    blockers = []
    for event in events:
        event_end = event.start_at + timedelta(minutes=event.duration_minutes)
        if event_end > start and event.start_at < end:
            blockers.append((event.start_at, event_end, event.title))
    return blockers


def _task_candidates(user, start_date, days):
    end_date = start_date + timedelta(days=days)
    tasks = Task.objects.filter(student=user, deadline__date__lt=end_date).exclude(status=Task.Status.COMPLETED).select_related('subject').order_by('deadline', '-priority')
    return list(tasks)


def build_plan_preview(user, start_date, days=7, daily_minutes=180, day_start=None, day_end=None):
    day_start = day_start or datetime.min.time().replace(hour=8)
    day_end = day_end or datetime.min.time().replace(hour=22)
    priorities_cache = {}
    resources = _resource_map(user)
    tasks = _task_candidates(user, start_date, days)
    scheduled_tasks = set()
    blocks = []
    blocked_summary = []
    priority_index = 0
    for day_offset in range(days):
        day = start_date + timedelta(days=day_offset)
        context = build_context(user, day=day)
        priorities = priorities_cache.setdefault(day, calculate_priorities(context))
        day_window_start = _aware(day, day_start)
        day_window_end = _aware(day, day_end)
        blockers = [(start, end, 'College or calendar event') for start, end in context['blocked_windows']]
        blockers.extend((_aware(exam.exam_date, exam.start_time), _aware(exam.exam_date, exam.end_time), f'Exam: {exam.title}') for exam in context['exams'] if exam.exam_date == day)
        blockers.extend(_existing_blockers(user, day_window_start, day_window_end))
        blocked_summary.extend({'day': day.isoformat(), 'start_at': start.isoformat(), 'end_at': end.isoformat(), 'title': title} for start, end, title in blockers if start.date() == day)
        remaining = daily_minutes
        blocks_today = 0
        for window_start, window_end in _free_windows(day_window_start, day_window_end, [(start, end) for start, end, _ in blockers]):
            cursor = window_start
            while cursor < window_end and remaining >= 20 and blocks_today < 2:
                task = next((item for item in tasks if str(item.id) not in scheduled_tasks and item.deadline.date() <= day + timedelta(days=2)), None)
                if task:
                    duration = min(60, task.estimated_minutes, remaining, int((window_end - cursor).total_seconds() // 60))
                    if duration < 20:
                        break
                    subject_id = str(task.subject_id) if task.subject_id else None
                    block = {
                        'title': f'Assignment: {task.title}',
                        'subtopics': 'Deadline Rescue',
                        'start_at': cursor.isoformat(),
                        'duration_minutes': duration,
                        'color': task.subject.color if task.subject else '#D65B72',
                        'event_type': 'STUDY',
                        'subject': subject_id,
                        'task_id': str(task.id),
                        'resource_ids': [item['id'] for item in resources.get(subject_id, [])[:3]],
                        'resource_titles': [item['title'] for item in resources.get(subject_id, [])[:3]],
                        'reason': f'Due {task.deadline.isoformat()}',
                    }
                    scheduled_tasks.add(str(task.id))
                else:
                    if not priorities:
                        break
                    item = priorities[priority_index % len(priorities)]
                    priority_index += 1
                    subject = next((subject for subject in context['subjects'] if str(subject.id) == item.get('subject_id')), None)
                    duration = min(45 if item.get('topic') else 30, remaining, int((window_end - cursor).total_seconds() // 60))
                    if duration < 20:
                        break
                    subject_id = item.get('subject_id')
                    block = {
                        'title': f'Review {item.get("topic") or item.get("subject")}',
                        'subtopics': item.get('topic') or 'Focused subject review',
                        'start_at': cursor.isoformat(),
                        'duration_minutes': duration,
                        'color': subject.color if subject else '#6D5EF5',
                        'event_type': 'STUDY',
                        'subject': subject_id,
                        'topic_id': item.get('topic_id'),
                        'resource_ids': [resource['id'] for resource in resources.get(subject_id, [])[:3]],
                        'resource_titles': [resource['title'] for resource in resources.get(subject_id, [])[:3]],
                        'reason': item.get('reasons', [{}])[0].get('label', 'Highest current academic priority'),
                        'priority_score': item.get('priority_score', 0),
                    }
                blocks.append(block)
                blocks_today += 1
                cursor += timedelta(minutes=duration)
                remaining -= duration
    return {
        'start_date': start_date.isoformat(),
        'days': days,
        'daily_minutes': daily_minutes,
        'blocks': blocks,
        'blocked_events': blocked_summary,
        'scheduled_minutes': sum(block['duration_minutes'] for block in blocks),
        'status': 'READY' if blocks else 'EMPTY',
    }


def _parse_start(value):
    if not isinstance(value, str):
        raise ValidationError('Every plan block needs a valid start_at value.')
    normalized = value.replace('Z', '+00:00')
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValidationError('Every plan block needs a valid start_at value.') from exc
    return timezone.make_aware(parsed) if timezone.is_naive(parsed) else parsed


def _conflicts(start, end, blocked):
    return any(start < block_end and end > block_start for block_start, block_end, _ in blocked)


def commit_plan(user, blocks):
    created = []
    pending = []
    with transaction.atomic():
        for block in blocks:
            start = _parse_start(block.get('start_at'))
            try:
                duration = int(block.get('duration_minutes', 0))
            except (TypeError, ValueError) as exc:
                raise ValidationError('Every plan block needs a positive duration.') from exc
            if duration <= 0:
                raise ValidationError('Every plan block needs a positive duration.')
            end = start + timedelta(minutes=duration)
            context = build_context(user, day=timezone.localtime(start).date())
            blocked = [(item_start, item_end, 'College or calendar event') for item_start, item_end in context['blocked_windows']]
            blocked.extend((item.start_at, item.start_at + timedelta(minutes=item.duration_minutes), item.title) for item in PlannerEvent.objects.filter(student=user, start_at__date=timezone.localtime(start).date()))
            blocked.extend(pending)
            if _conflicts(start, end, blocked):
                raise ValidationError({'blocks': [f'Block at {start.isoformat()} conflicts with an existing timetable event.']})
            subject = None
            subject_id = block.get('subject')
            if subject_id:
                subject = Subject.objects.filter(id=subject_id, semester__student=user).first()
                if not subject:
                    raise ValidationError({'subject': 'A plan subject does not belong to the authenticated user.'})
            resource_titles = [str(title) for title in block.get('resource_titles', []) if title]
            subtopics = str(block.get('subtopics') or '')
            if resource_titles:
                subtopics = f'{subtopics} | Use: {", ".join(resource_titles[:3])}'.strip(' |')
            event = PlannerEvent.objects.create(
                student=user,
                subject=subject,
                title=str(block.get('title') or 'Adaptive study block')[:220],
                subtopics=subtopics,
                start_at=start,
                duration_minutes=duration,
                color=str(block.get('color') or '#6D5EF5')[:20],
                event_type='STUDY',
            )
            pending.append((start, end, event.title))
            created.append(event)
    return created
