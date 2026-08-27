import re
from django.db import transaction
from django.utils import timezone
from ..models import CheckpointAttempt, LearningLevel, LearningPath


def evaluate_checkpoint(user, path, level, answer):
    checkpoint = level.checkpoint or {}
    expected = checkpoint.get('correct_answer')
    answer_text = str(answer or '').strip()
    answer_value = re.sub(r'^[A-Za-z][\.)]\s*', '', answer_text).strip()
    options = checkpoint.get('options')
    accepted_answers = {answer_text.casefold()}
    if isinstance(options, dict) and expected in options:
        accepted_answers.update({str(expected).casefold(), str(options[expected]).casefold(), f'{expected}. {options[expected]}'.casefold()})
        expected = options[expected]
    elif isinstance(options, list) and isinstance(expected, str) and re.fullmatch(r'[A-Za-z]', expected):
        option_index = ord(expected.upper()) - ord('A')
        if 0 <= option_index < len(options):
            expected = options[option_index]
    if isinstance(expected, list):
        matches = sum(1 for keyword in expected if keyword.lower() in answer_value.lower())
        score = round(matches / max(len(expected), 1) * 100)
        correct = score >= 60
    else:
        expected_value = re.sub(r'^[A-Za-z][\.)]\s*', '', str(expected or '').strip()).strip()
        correct = answer_value.casefold() == expected_value.casefold() or answer_text.casefold() == str(expected or '').strip().casefold() or bool(accepted_answers.intersection({str(expected or '').strip().casefold()}))
        score = 100 if correct and not isinstance(expected, list) else score if correct else 0
    stars = 3 if score >= 95 else 2 if score >= 80 else 1 if score >= 60 else 0
    feedback = 'Correct. The next level is now unlocked.' if correct else checkpoint.get('explanation', 'Review this section and try again.')
    with transaction.atomic():
        attempt = CheckpointAttempt.objects.create(user=user, learning_path=path, level=level, answer=answer_text, correct=correct, score=score, feedback=feedback)
        if correct and level.status != LearningLevel.Status.COMPLETED:
            level.status = LearningLevel.Status.COMPLETED
            level.completed_at = timezone.now()
            level.best_score = max(level.best_score, score)
            level.best_stars = max(level.best_stars, stars)
            level.save(update_fields=['status', 'completed_at', 'best_score', 'best_stars'])
            path.xp += 25
            notes_header = f'\n\n# {level.title}\nSource: {path.youtube_url}&t={int(level.start_seconds)}s\n'
            path.cumulative_notes = f'{path.cumulative_notes}{notes_header}{level.notes}'.strip()
            next_level = path.levels.filter(order=level.order + 1).first()
            if next_level:
                next_level.status = LearningLevel.Status.AVAILABLE
                next_level.save(update_fields=['status'])
                path.current_level_order = next_level.order
            else:
                _complete_path(path)
            path.save(update_fields=['xp', 'cumulative_notes', 'current_level_order', 'status', 'processing_stage', 'mastery_percentage', 'completed_at', 'updated_at'])
        elif score > level.best_score:
            level.best_score = score
            level.best_stars = max(level.best_stars, stars)
            level.save(update_fields=['best_score', 'best_stars'])
    return attempt


def _complete_path(path):
    attempts = path.attempts.all()
    total = attempts.count()
    correct = attempts.filter(correct=True).count()
    path.status = LearningPath.Status.READY
    path.processing_stage = 'Final challenge unlocked'
    path.mastery_percentage = round(correct / total * 100) if total else 0


def evaluate_final_challenge(path, answers):
    questions = path.final_challenge.get('questions', [])
    if not questions:
        raise ValueError('The final challenge is unavailable.')
    correct = 0
    for question in questions:
        answer = str(answers.get(question['id'], '')).strip()
        answer_value = re.sub(r'^[A-Za-z][\.)]\s*', '', answer).strip()
        expected = question.get('correct_answer')
        options = question.get('options')
        if isinstance(options, dict) and expected in options:
            expected = options[expected]
        elif isinstance(options, list) and isinstance(expected, str) and re.fullmatch(r'[A-Za-z]', expected):
            option_index = ord(expected.upper()) - ord('A')
            if 0 <= option_index < len(options):
                expected = options[option_index]
        if isinstance(expected, list):
            matches = sum(1 for keyword in expected if str(keyword).lower() in answer_value.lower())
            correct += int(matches / max(len(expected), 1) >= 0.6)
        else:
            expected_value = re.sub(r'^[A-Za-z][\.)]\s*', '', str(expected or '').strip()).strip()
            correct += int(answer_value.casefold() == expected_value.casefold() or answer.casefold() == str(expected or '').strip().casefold())
    total = len(questions)
    path.mastery_percentage = round(correct / total * 100)
    path.status = LearningPath.Status.COMPLETED
    path.completed_at = timezone.now()
    path.xp += 50
    path.processing_stage = 'Course complete'
    path.save(update_fields=['mastery_percentage', 'status', 'completed_at', 'xp', 'processing_stage', 'updated_at'])
    return {'score': correct, 'total': total, 'mastery_percentage': path.mastery_percentage, 'xp': path.xp}
