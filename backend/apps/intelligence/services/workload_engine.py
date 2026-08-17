from datetime import datetime, timedelta
from django.utils import timezone

def _conflicts(start, end, blocked):
    return any(start < block_end and end > block_start for block_start, block_end in blocked)

def available_windows(context, available_minutes):
    now = context.get('now') or timezone.now()
    end = now + timedelta(minutes=available_minutes)
    blocked = []
    for item in context.get('blocked_windows', []):
        if item[1] > now and item[0] < end: blocked.append((max(now, item[0]), min(end, item[1])))
    windows = []
    cursor = now
    for start, stop in sorted(blocked):
        if cursor < start: windows.append((cursor, start))
        cursor = max(cursor, stop)
    if cursor < end: windows.append((cursor, end))
    return windows

def build_workload_plan(priorities, tasks, context, available_minutes=90):
    windows = available_windows(context, max(0, int(available_minutes)))
    effective_minutes = sum(int((stop - start).total_seconds() // 60) for start, stop in windows)
    remaining = effective_minutes
    plan = []
    scheduled_work = 0
    ordered = sorted(priorities, key=lambda item: item.get('priority_score', 0), reverse=True)
    task_minutes = sum(task.estimated_minutes for task in tasks if task.status != task.Status.COMPLETED)
    for item in ordered:
        if remaining <= 0: break
        duration = min(45 if item.get('topic') else 30, remaining)
        plan.append({'type': 'STUDY_TOPIC' if item.get('topic') else 'STUDY_SUBJECT', 'subject': item.get('subject'), 'topic': item.get('topic'), 'duration_minutes': duration, 'priority_score': item.get('priority_score', 0), 'reasons': item.get('reasons', [])})
        remaining -= duration
        scheduled_work += duration
    status = 'HEALTHY'
    total_work = task_minutes
    if total_work > effective_minutes * 3: status = 'CRITICAL'
    elif total_work > effective_minutes: status = 'OVERLOADED'
    elif total_work > effective_minutes * 0.75: status = 'BUSY'
    return {'status': status, 'available_minutes': effective_minutes, 'scheduled_minutes': effective_minutes - remaining, 'plan': plan, 'message': f'{total_work / 60:.1f} hours of estimated work is competing for {effective_minutes} available minutes.' if status in ('OVERLOADED', 'CRITICAL') else 'Your workload fits the available study window.'}
