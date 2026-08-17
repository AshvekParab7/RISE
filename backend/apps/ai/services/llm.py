from django.conf import settings
from openai import OpenAI

class AIUnavailable(Exception): pass
class AIProviderError(Exception): pass

def generate_text(instructions, input_text):
    if not settings.OPENAI_API_KEY: raise AIUnavailable('AI temporarily unavailable.')
    try:
        response = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=30, max_retries=2).responses.create(model=settings.OPENAI_MODEL, instructions=instructions, input=input_text)
        return response.output_text
    except Exception as exc: raise AIProviderError('AI provider unavailable.') from exc
