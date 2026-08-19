from datetime import date, timedelta
from math import exp

DIFFICULTY_WEIGHT = {'EASY': 0, 'MEDIUM': 5, 'HARD': 10}
PRIORITY_WEIGHT = {'LOW': 0, 'MEDIUM': 4, 'HIGH': 8, 'URGENT': 12}

def _days_until(value, today):
    return (value - today).days if value else None

def exam_impact(exam_date, today):
    days = _days_until(exam_date, today)
    if days is None: return 0, None
    if days <= 0: return 30, 'Exam is due or overdue'
    impact = round(30 / (1 + days / 7))
    return impact, f'Exam in {days} days'

def mastery_impact(mastery):
    value = max(0, min(100, mastery or 0))
    return round(25 * (1 - value / 100)), f'Mastery is only {value}%'

def workload_impact(tasks, now):
    pending = [task for task in tasks if task.status != task.Status.COMPLETED]
    if not pending: return 0, None
    impact = 0
    labels = []
    for task in pending:
        days = (task.deadline.date() - now.date()).days
        urgency = 12 if days <= 0 else 10 if days <= 1 else 6 if days <= 3 else 2
        effort = min(8, round((task.estimated_minutes or 0) / 120 * 8))
        impact = max(impact, urgency + effort + PRIORITY_WEIGHT.get(task.priority, 0) // 3)
        if days <= 1: labels.append(f'{task.title} due tomorrow' if days >= 0 else f'{task.title} is overdue')
    return min(20, impact), labels[0] if labels else 'Pending assignment workload'

def calculate_subject_priority(subject, context):
    today = context.get('today', date.today())
    now = context.get('now')
    if now is None: now = context.get('now_factory', lambda: None)() or __import__('django.utils.timezone', fromlist=['now']).now()
    reasons = []
    score = 0
    impact, label = exam_impact(context.get('exam_dates', {}).get(subject.id, subject.exam_date), today)
    if impact: score += impact; reasons.append({'code': 'EXAM_SOON', 'label': label, 'impact': impact})
    topics = context.get('topics_by_subject', {}).get(subject.id, [])
    mastery = round(sum(topic.mastery_percentage for topic in topics) / len(topics)) if topics else subject.mastery_percentage
    impact, label = mastery_impact(mastery); score += impact; reasons.append({'code': 'LOW_MASTERY', 'label': label, 'impact': impact}) if impact else None
    difficulty = DIFFICULTY_WEIGHT.get(subject.difficulty, 5); score += difficulty; reasons.append({'code': 'DIFFICULT_SUBJECT', 'label': f'{subject.get_difficulty_display()} subject', 'impact': difficulty}) if difficulty else None
    tasks = context.get('tasks_by_subject', {}).get(subject.id, [])
    impact, label = workload_impact(tasks, now); score += impact; reasons.append({'code': 'PENDING_ASSIGNMENT', 'label': label, 'impact': impact}) if impact else None
    syllabus_impact = round(10 * (1 - mastery / 100)); score += syllabus_impact; reasons.append({'code': 'SYLLABUS_REMAINING', 'label': f'{100 - mastery}% of topic mastery remains', 'impact': syllabus_impact}) if syllabus_impact else None
    sessions = context.get('sessions_by_subject', {}).get(subject.id, [])
    recent_minutes = sum(session.actual_minutes for session in sessions if session.status == session.Status.COMPLETED and session.created_at.date() >= today - timedelta(days=7))
    gap = 5 if recent_minutes == 0 and mastery < 80 else 0
    score += gap; reasons.append({'code': 'LOW_RECENT_STUDY', 'label': 'No completed study time in the last 7 days', 'impact': gap}) if gap else None
    return {'subject_id': str(subject.id), 'subject': subject.name, 'priority_score': min(100, round(score)), 'reasons': reasons}

def calculate_topic_priority(topic, context):
    subject_priority = calculate_subject_priority(topic.subject, context)
    score = round(subject_priority['priority_score'] * 0.45)
    reasons = list(subject_priority['reasons'])
    impact, label = mastery_impact(topic.mastery_percentage)
    topic_impact = round(30 * (1 - (topic.mastery_percentage or 0) / 100)); score += topic_impact
    if topic_impact: reasons.append({'code': 'TOPIC_LOW_MASTERY', 'label': f'{topic.name} mastery is {topic.mastery_percentage}%', 'impact': topic_impact})
    score += DIFFICULTY_WEIGHT.get(topic.subject.difficulty, 5) // 2
    reasons.sort(key=lambda item: item['impact'], reverse=True)
    return {'topic_id': str(topic.id), 'subject_id': str(topic.subject_id), 'subject': topic.subject.name, 'topic': topic.name, 'priority_score': min(100, round(score)), 'reasons': reasons[:5]}
