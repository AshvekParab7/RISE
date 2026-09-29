import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class GeminiUnavailable(Exception):
    pass


# Try multiple model names in order
CANDIDATE_MODELS = [
    'gemini-2.5-flash',
    'gemini-2.5-flash-preview-05-20',
    'gemini-2.0-flash',
    'gemini-2.0-flash-exp',
    'gemini-1.5-flash',
    'gemini-1.5-pro',
]

# Try multiple API versions
API_VERSIONS = ['v1beta', 'v1']


def _try_request(api_key, model, api_version, payload):
    """Try one combination of model + API version + auth method."""
    base_url = f'https://generativelanguage.googleapis.com/{api_version}/models/{model}:generateContent'

    # Method 1: key as header
    try:
        resp = requests.post(
            base_url,
            headers={'x-goog-api-key': api_key, 'Content-Type': 'application/json'},
            json=payload,
            timeout=45,
        )
        if resp.status_code not in (401, 403, 404):
            resp.raise_for_status()
            return resp
    except requests.HTTPError:
        pass

    # Method 2: key as query param
    resp = requests.post(
        base_url,
        params={'key': api_key},
        json=payload,
        timeout=45,
    )
    return resp


def generate_text_with_gemini(instructions, input_text):
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        raise GeminiUnavailable('Gemini is not configured.')

    configured_model = getattr(settings, 'GEMINI_MODEL', '') or ''
    models = list(dict.fromkeys(
        ([configured_model] if configured_model else []) + CANDIDATE_MODELS
    ))

    # Use plain text response for flexibility — caller handles JSON parsing
    payload = {
        'systemInstruction': {'parts': [{'text': instructions}]},
        'contents': [{'role': 'user', 'parts': [{'text': input_text}]}],
        'generationConfig': {'temperature': 0.35},
    }

    last_error = None
    for model in models:
        for api_version in API_VERSIONS:
            try:
                resp = _try_request(api_key, model, api_version, payload)
                if resp.status_code in (404, 400) and model != models[-1]:
                    logger.debug('Gemini model %s/%s not found, trying next', api_version, model)
                    continue
                resp.raise_for_status()
                data = resp.json()
                text = ''.join(
                    part.get('text', '')
                    for part in data['candidates'][0]['content']['parts']
                    if isinstance(part, dict)
                ).strip()
                if text:
                    logger.info('Gemini success model=%s api_version=%s', model, api_version)
                    return text
            except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
                last_error = exc
                logger.debug('Gemini attempt failed model=%s api_version=%s error=%s', model, api_version, exc)
                continue

    logger.error('All Gemini attempts failed. Last error: %s', last_error)
    raise GeminiUnavailable('Gemini could not complete the request.') from last_error