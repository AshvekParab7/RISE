import requests
from django.conf import settings


class GeminiUnavailable(Exception):
    pass


GEMINI_FALLBACK_MODEL = 'gemini-3.6-flash'


def generate_text_with_gemini(instructions, input_text):
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        raise GeminiUnavailable('Gemini is not configured.')
    payload = {
        'systemInstruction': {'parts': [{'text': instructions}]},
        'contents': [{'role': 'user', 'parts': [{'text': input_text}]}],
        'generationConfig': {'temperature': 0.35, 'responseMimeType': 'application/json'},
    }
    configured_model = getattr(settings, 'GEMINI_MODEL', GEMINI_FALLBACK_MODEL) or GEMINI_FALLBACK_MODEL
    models = tuple(dict.fromkeys((configured_model, GEMINI_FALLBACK_MODEL)))
    try:
        for model in models:
            response = requests.post(
                f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
                headers={'x-goog-api-key': api_key},
                json=payload,
                timeout=30,
            )
            if response.status_code == 404 and model != GEMINI_FALLBACK_MODEL:
                continue
            response.raise_for_status()
            data = response.json()
            text = ''.join(
                part.get('text', '')
                for part in data['candidates'][0]['content']['parts']
                if isinstance(part, dict)
            ).strip()
            if text:
                return text
            raise KeyError('empty response')
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
        raise GeminiUnavailable('Gemini could not complete the planner request.') from exc
    raise GeminiUnavailable('Gemini could not complete the planner request.')