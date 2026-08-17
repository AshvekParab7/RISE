import hashlib
import math
from django.conf import settings
from openai import OpenAI

class EmbeddingUnavailable(Exception): pass

def _local_embedding(text, dimensions=64):
    vector = [0.0] * dimensions
    for token in text.lower().split(): vector[int(hashlib.sha256(token.encode()).hexdigest(), 16) % dimensions] += 1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]

def embed_text(text):
    if settings.EMBEDDING_PROVIDER == 'openai' and settings.OPENAI_API_KEY:
        try: return OpenAI(api_key=settings.OPENAI_API_KEY, timeout=20, max_retries=2).embeddings.create(model=settings.OPENAI_EMBEDDING_MODEL, input=text).data[0].embedding
        except Exception as exc: raise EmbeddingUnavailable() from exc
    return _local_embedding(text)
