import re
from urllib.parse import parse_qs, urlparse
import requests

YOUTUBE_HOSTS = {'youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be'}
VIDEO_ID_RE = re.compile(r'^[A-Za-z0-9_-]{11}$')


class YouTubeVideoError(ValueError):
    pass


def extract_video_id(url):
    try:
        parsed = urlparse(url.strip())
    except (TypeError, ValueError) as exc:
        raise YouTubeVideoError('Enter a valid YouTube URL.') from exc
    if parsed.scheme not in ('http', 'https') or parsed.hostname not in YOUTUBE_HOSTS:
        raise YouTubeVideoError('Enter a valid YouTube URL.')
    video_id = parsed.path.strip('/') if parsed.hostname == 'youtu.be' else parse_qs(parsed.query).get('v', [''])[0]
    if not VIDEO_ID_RE.fullmatch(video_id):
        raise YouTubeVideoError('The YouTube URL does not contain a valid video ID.')
    return video_id


def canonical_url(video_id):
    return f'https://www.youtube.com/watch?v={video_id}'


def fetch_video_title(url):
    try:
        response = requests.get('https://www.youtube.com/oembed', params={'url': url, 'format': 'json'}, timeout=10)
    except requests.RequestException as exc:
        raise YouTubeVideoError('YouTube video details are temporarily unavailable.') from exc
    if response.status_code in (401, 403, 404):
        raise YouTubeVideoError('This video is unavailable, private, or restricted.')
    if response.status_code != 200:
        raise YouTubeVideoError('YouTube video details could not be loaded.')
    return response.json().get('title', 'YouTube Learning Path')[:300]
