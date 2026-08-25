import re
from datetime import timedelta
from urllib.parse import parse_qs, urlparse
import requests
from django.conf import settings

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


def search_videos(query):
    if not settings.YOUTUBE_API_KEY:
        raise YouTubeVideoError('YouTube search is not configured. Paste a YouTube URL to continue.')
    try:
        response = requests.get('https://www.googleapis.com/youtube/v3/search', params={
            'part': 'snippet', 'type': 'video', 'maxResults': 8,
            'q': query, 'key': settings.YOUTUBE_API_KEY,
        }, timeout=10)
        response.raise_for_status()
        items = response.json().get('items', [])
        ids = [item.get('id', {}).get('videoId') for item in items]
        details = requests.get('https://www.googleapis.com/youtube/v3/videos', params={
            'part': 'contentDetails', 'id': ','.join(filter(None, ids)), 'key': settings.YOUTUBE_API_KEY,
        }, timeout=10)
        details.raise_for_status()
        durations = {item['id']: item.get('contentDetails', {}).get('duration', '') for item in details.json().get('items', [])}
    except requests.RequestException as exc:
        raise YouTubeVideoError('YouTube search is temporarily unavailable.') from exc
    return [{
        'video_id': item['id']['videoId'],
        'url': canonical_url(item['id']['videoId']),
        'title': item['snippet'].get('title', ''),
        'channel': item['snippet'].get('channelTitle', ''),
        'description': item['snippet'].get('description', ''),
        'thumbnail': item['snippet'].get('thumbnails', {}).get('medium', item['snippet'].get('thumbnails', {}).get('default', {})).get('url', ''),
        'duration': format_duration(durations.get(item['id']['videoId'], '')),
    } for item in items]


def format_duration(value):
    match = re.fullmatch(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', value or '')
    if not match:
        return '—'
    hours, minutes, seconds = (int(part or 0) for part in match.groups())
    total = int(timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds())
    return f'{total // 3600}:{(total % 3600) // 60:02d}:{total % 60:02d}' if hours else f'{total // 60}:{total % 60:02d}'
