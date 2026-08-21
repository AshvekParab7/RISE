from django.db import transaction
from .chunker import chunk_transcript
from .path_generator import generate_final_challenge, generate_level
from .transcript import fetch_transcript
from .youtube import fetch_video_title
from ..models import LearningLevel, LearningPath


def process_learning_path(path):
    try:
        _progress(path, 10, 'Loading video details')
        path.title = fetch_video_title(path.youtube_url)
        path.save(update_fields=['title', 'updated_at'])
        _progress(path, 25, 'Retrieving captions')
        segments, language = fetch_transcript(path.video_id)
        path.transcript_segments = segments
        path.transcript_language = language
        path.transcript_duration = round(segments[-1]['start'] + segments[-1]['duration'], 3)
        path.save(update_fields=['transcript_segments', 'transcript_language', 'transcript_duration', 'updated_at'])
        _progress(path, 45, 'Detecting lecture sections')
        chunks = chunk_transcript(segments)
        if not chunks:
            raise ValueError('The transcript could not be divided into lessons.')
        with transaction.atomic():
            path.levels.all().delete()
            levels = []
            for index, chunk in enumerate(chunks, 1):
                _progress(path, min(90, 45 + round(index / len(chunks) * 45)), f'Generating level {index} of {len(chunks)}')
                generated = generate_level(chunk, index)
                levels.append(LearningLevel.objects.create(
                    learning_path=path,
                    order=index,
                    title=generated['title'][:240],
                    description=generated.get('description', ''),
                    objectives=generated.get('objectives', []),
                    transcript_text=chunk['text'],
                    start_seconds=chunk['start_seconds'],
                    end_seconds=chunk['end_seconds'],
                    key_concepts=generated.get('key_concepts', []),
                    lesson_steps=generated.get('lesson_steps', []),
                    notes=generated.get('notes', ''),
                    checkpoint=generated.get('checkpoint', {}),
                    estimated_minutes=max(1, round((chunk['end_seconds'] - chunk['start_seconds']) / 60)),
                    status=LearningLevel.Status.AVAILABLE if index == 1 else LearningLevel.Status.LOCKED,
                ))
            path.final_challenge = generate_final_challenge(levels)
        path.status = LearningPath.Status.READY
        path.processing_stage = 'Ready to learn'
        path.processing_progress = 100
        path.failure_reason = ''
        path.save(update_fields=['status', 'processing_stage', 'processing_progress', 'failure_reason', 'final_challenge', 'updated_at'])
        return path
    except Exception as exc:
        path.status = LearningPath.Status.FAILED
        path.processing_stage = 'Processing failed'
        path.processing_progress = 0
        path.failure_reason = str(exc)[:500] or 'The learning path could not be created.'
        path.save(update_fields=['status', 'processing_stage', 'processing_progress', 'failure_reason', 'updated_at'])
        return path


def _progress(path, percent, stage):
    path.processing_progress = percent
    path.processing_stage = stage
    path.save(update_fields=['processing_progress', 'processing_stage', 'updated_at'])
