from django.db import transaction
from apps.academics.models import Subject, Topic

MASTERY_OLD_WEIGHT = 0.7
MASTERY_TEST_WEIGHT = 0.3

@transaction.atomic
def apply_assessment_results(test, performance):
    changes = []
    for topic_id, result in performance.items():
        topic = Topic.objects.filter(id=topic_id, subject__semester__student=test.student).first()
        if not topic: continue
        old = topic.mastery_percentage
        score = result['percentage']
        new = round(old * MASTERY_OLD_WEIGHT + score * MASTERY_TEST_WEIGHT)
        topic.mastery_percentage = max(0, min(100, new))
        topic.status = Topic.Status.MASTERED if new >= 80 else Topic.Status.IN_PROGRESS if new > 0 else Topic.Status.NOT_STARTED
        topic.save(update_fields=['mastery_percentage', 'status', 'updated_at'])
        changes.append({'topic_id': str(topic.id), 'topic': topic.name, 'before': old, 'after': new, 'percentage': score, 'correct': result['correct'], 'total': result['total']})
    subjects = {topic.subject_id for topic_id in performance for topic in Topic.objects.filter(id=topic_id, subject__semester__student=test.student)}
    for subject_id in subjects:
        subject = Subject.objects.filter(id=subject_id).first()
        if subject:
            values = list(subject.topics.values_list('mastery_percentage', flat=True))
            subject.mastery_percentage = round(sum(values) / len(values)) if values else subject.mastery_percentage
            subject.save(update_fields=['mastery_percentage', 'updated_at'])
            from apps.intelligence.services.recommendation_engine import build_context, recalculate_subject_priorities
            recalculate_subject_priorities(build_context(test.student))
    return changes
