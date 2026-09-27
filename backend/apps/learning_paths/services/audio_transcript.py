import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)


class AudioTranscriptError(ValueError):
    pass


def _transcribe(client, audio_path):
    with audio_path.open('rb') as audio_file:
        return client.audio.transcriptions.create(
            model='whisper-1',
            file=audio_file,
            response_format='verbose_json',
            temperature=0,
        )


def _transcribe_chunks(client, audio_path, ffmpeg_path, directory):
    chunk_pattern = str(Path(directory) / 'chunk_%03d.mp3')
    logger.info('YouTube audio fallback stage=transcription_chunking chunk_seconds=300')
    subprocess.run(
        [ffmpeg_path, '-y', '-i', str(audio_path), '-f', 'segment', '-segment_time', '300', '-reset_timestamps', '1', '-acodec', 'copy', chunk_pattern],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    segments = []
    language = ''
    for index, chunk in enumerate(sorted(Path(directory).glob('chunk_*.mp3'))):
        logger.info('YouTube audio fallback stage=transcription_chunk index=%s bytes=%s', index, chunk.stat().st_size)
        response = _transcribe(client, chunk)
        language = language or str(getattr(response, 'language', '') or '')
        for segment in getattr(response, 'segments', []) or []:
            start = float(segment.get('start', 0) if isinstance(segment, dict) else getattr(segment, 'start', 0))
            end = float(segment.get('end', start) if isinstance(segment, dict) else getattr(segment, 'end', start))
            text = str(segment.get('text', '') if isinstance(segment, dict) else getattr(segment, 'text', '')).strip()
            if text:
                segments.append({'text': text, 'start': start + index * 300, 'duration': max(0.1, end - start)})
    return SimpleNamespace(language=language or 'unknown', segments=segments, text=' '.join(segment['text'] for segment in segments))


def fetch_audio_transcript(youtube_url):
    if not settings.OPENAI_API_KEY:
        logger.error('YouTube audio fallback failed stage=configuration reason=openai_key_missing')
        raise AudioTranscriptError('This video has no usable captions and audio transcription is not configured.')
    try:
        from yt_dlp import YoutubeDL
    except ImportError as exc:
        logger.exception('YouTube audio fallback failed stage=dependency reason=ytdlp_missing')
        raise AudioTranscriptError('This video has no usable captions and audio processing is unavailable.') from exc

    with tempfile.TemporaryDirectory(prefix='rise-youtube-audio-') as directory:
        output_template = str(Path(directory) / 'lecture.%(ext)s')
        options = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 20,
        }
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            options['ffmpeg_location'] = ffmpeg_path
            logger.info('YouTube audio fallback stage=ffmpeg_ready path=%s', ffmpeg_path)
        else:
            logger.warning('YouTube audio fallback stage=ffmpeg_missing mode=direct_audio')
        try:
            logger.info('YouTube audio fallback stage=audio_extraction video_url=%s', youtube_url)
            with YoutubeDL(options) as downloader:
                downloader.extract_info(youtube_url, download=True)
            audio_path = next(Path(directory).glob('lecture.*'), None)
            if not audio_path or not audio_path.is_file():
                raise AudioTranscriptError('RISE could not extract an audio track from this video.')
            ffmpeg_path = shutil.which('ffmpeg')
            if not ffmpeg_path:
                try:
                    import imageio_ffmpeg
                    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
                    logger.info('YouTube audio fallback stage=ffmpeg_ready path=%s', ffmpeg_path)
                except Exception:
                    ffmpeg_path = None
            transcription_path = audio_path
            if ffmpeg_path:
                transcription_path = Path(directory) / 'lecture.mp3'
                logger.info('YouTube audio fallback stage=audio_normalization ffmpeg=%s input=%s', ffmpeg_path, audio_path.suffix)
                try:
                    subprocess.run(
                        [ffmpeg_path, '-y', '-i', str(audio_path), '-vn', '-acodec', 'libmp3lame', '-ar', '16000', '-ac', '1', str(transcription_path)],
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=90,
                    )
                except subprocess.CalledProcessError as exc:
                    detail = (exc.stderr or exc.stdout or '').replace('\n', ' ').strip()[-400:]
                    logger.exception('YouTube audio fallback failed stage=audio_normalization detail=%s', detail)
                    raise AudioTranscriptError(f'Audio normalization failed: {detail or "FFmpeg returned an error."}') from exc
                except Exception as exc:
                    logger.exception('YouTube audio fallback failed stage=audio_normalization error_type=%s', type(exc).__name__)
                    raise AudioTranscriptError(f'Audio normalization failed ({type(exc).__name__}).') from exc
            elif transcription_path.suffix.lower() not in {'.mp3', '.m4a', '.wav', '.mp4', '.mpeg', '.mpga', '.webm'}:
                raise AudioTranscriptError('Audio extraction succeeded, but the file format cannot be sent to transcription.')
            if transcription_path.stat().st_size > 25 * 1024 * 1024:
                raise AudioTranscriptError('The normalized audio is larger than the supported 25 MB transcription limit.')
            logger.info('YouTube audio fallback stage=transcription audio_bytes=%s format=%s', transcription_path.stat().st_size, transcription_path.suffix)
            client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=180, max_retries=2)
            try:
                response = _transcribe(client, transcription_path)
            except Exception as exc:
                if type(exc).__name__ != 'APITimeoutError' or not ffmpeg_path:
                    raise
                logger.warning('YouTube audio fallback stage=transcription_timeout action=chunk_and_retry')
                response = _transcribe_chunks(client, transcription_path, ffmpeg_path, directory)
        except AudioTranscriptError:
            raise
        except Exception as exc:
            detail = str(exc).replace('\n', ' ').strip()[:400]
            logger.exception('YouTube audio fallback failed stage=extraction_or_transcription error_type=%s detail=%s', type(exc).__name__, detail)
            raise AudioTranscriptError(f'Audio transcription failed ({type(exc).__name__}): {detail or "no additional details"}') from exc

    segments = [
        {
            'text': str(segment.get('text', '') if isinstance(segment, dict) else getattr(segment, 'text', '')).strip(),
            'start': float(segment.get('start', 0) if isinstance(segment, dict) else getattr(segment, 'start', 0)),
            'duration': max(0.1, float(segment.get('end', 0) if isinstance(segment, dict) else getattr(segment, 'end', 0)) - float(segment.get('start', 0) if isinstance(segment, dict) else getattr(segment, 'start', 0))),
        }
        for segment in getattr(response, 'segments', []) or []
    ]
    if not segments:
        text = str(getattr(response, 'text', '') or '').strip()
        if text:
            segments = [{'text': text, 'start': 0.0, 'duration': 1.0}]
    if not segments:
        raise AudioTranscriptError('RISE could not find spoken content in the extracted audio.')
    language = str(getattr(response, 'language', '') or 'unknown')
    logger.info('YouTube audio fallback stage=transcript_ready language=%s segments=%s', language, len(segments))
    return segments, language