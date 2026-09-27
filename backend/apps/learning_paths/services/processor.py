from django.db import transaction
import logging
from .chunker import chunk_transcript
from .path_generator import generate_final_challenge, generate_level
from .audio_transcript import AudioTranscriptError, fetch_audio_transcript
from .transcript import TranscriptError, fetch_transcript
from .youtube import fetch_video_title
from ..models import LearningLevel, LearningPath

logger = logging.getLogger(__name__)


def process_learning_path(path):
    try:
        _progress(path, 10, 'Loading video details')
        path.title = fetch_video_title(path.youtube_url)
        path.save(update_fields=['title', 'updated_at'])
        _progress(path, 25, 'Analyzing lecture')
        try:
            segments, language = fetch_transcript(path.video_id)
            logger.info('YouTube learning path stage=captions_ready video_id=%s language=%s segments=%s', path.video_id, language, len(segments))
        except TranscriptError as exc:
            logger.info('YouTube learning path stage=captions_unavailable video_id=%s reason=%s', path.video_id, str(exc))
            _progress(path, 35, 'Processing audio')
            try:
                segments, language = fetch_audio_transcript(path.youtube_url)
            except AudioTranscriptError:
                logger.exception('YouTube learning path fallback failed stage=audio_fallback video_id=%s', path.video_id)
                raise
        _progress(path, 45, 'Creating transcript')
        path.transcript_segments = segments
        path.transcript_language = language
        path.transcript_duration = round(segments[-1]['start'] + segments[-1]['duration'], 3)
        path.save(update_fields=['transcript_segments', 'transcript_language', 'transcript_duration', 'updated_at'])
        logger.info('YouTube learning path stage=transcript_ready video_id=%s language=%s segments=%s', path.video_id, language, len(segments))
        _progress(path, 55, 'Building learning levels')
        chunks = chunk_transcript(segments)
        if not chunks:
            raise ValueError('The transcript could not be divided into lessons.')
        with transaction.atomic():
            path.levels.all().delete()
            levels = []
            study_notes = []
            for index, chunk in enumerate(chunks, 1):
                _progress(path, min(90, 55 + round(index / len(chunks) * 35)), f'Generating level {index} of {len(chunks)}')
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
                study_notes.append({
                    'order': index,
                    'title': generated['title'][:240],
                    'key_concepts': generated.get('key_concepts', []),
                    'notes': generated.get('notes', ''),
                    'lesson_steps': generated.get('lesson_steps', []),
                })
            path.study_notes = study_notes
            path.final_challenge = generate_final_challenge(levels)
        path.status = LearningPath.Status.READY
        path.processing_stage = 'Ready to learn'
        path.processing_progress = 100
        path.failure_reason = ''
        path.save(update_fields=['status', 'processing_stage', 'processing_progress', 'failure_reason', 'study_notes', 'final_challenge', 'updated_at'])
        return path
    except Exception as exc:
        logger.exception('YouTube learning path failed video_id=%s stage=%s error_type=%s', path.video_id, path.processing_stage, type(exc).__name__)
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
