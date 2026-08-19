from apps.intelligence.services.recommendation_engine import build_context, build_next_action

def academic_context(user, subject_id=None, topic_id=None):
    context = build_context(user)
    next_action = build_next_action(context)
    subject = next(item for item in context['subjects'] if str(item.id) == str(subject_id)) if subject_id else None
    topic = next(item for item in context['topics'] if str(item.id) == str(topic_id)) if topic_id else None
    return {'subject': subject.name if subject else None, 'topic': topic.name if topic else None, 'next_action': next_action, 'pending_tasks': [{'title': task.title, 'deadline': task.deadline.isoformat()} for task in context['tasks'] if task.status != task.Status.COMPLETED][:8]}
