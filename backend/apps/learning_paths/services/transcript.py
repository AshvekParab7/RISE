from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import CouldNotRetrieveTranscript, NoTranscriptFound, TranscriptsDisabled, VideoUnavailable


class TranscriptError(ValueError):
    pass


def fetch_transcript(video_id, languages=None):
    try:
        transcript = YouTubeTranscriptApi().fetch(video_id, languages=languages or ['en', 'en-US', 'en-GB'])
    except TranscriptsDisabled as exc:
        raise TranscriptError('This video does not provide captions or a transcript.') from exc
    except NoTranscriptFound as exc:
        raise TranscriptError('No supported transcript was found for this video.') from exc
    except VideoUnavailable as exc:
        raise TranscriptError('This video is unavailable, private, or restricted.') from exc
    except CouldNotRetrieveTranscript as exc:
        raise TranscriptError('YouTube could not provide the transcript right now. Please retry later.') from exc
    except Exception as exc:
        raise TranscriptError('Transcript retrieval failed. Please check the video and try again.') from exc
    segments = []
    for snippet in transcript:
        text = ' '.join((snippet.text or '').replace('\n', ' ').split())
        if text:
            segments.append({'text': text, 'start': round(float(snippet.start), 3), 'duration': round(float(snippet.duration), 3)})
    if not segments:
        raise TranscriptError('The available transcript is empty.')
    language = getattr(transcript, 'language_code', '') or 'unknown'
    return segments, language
