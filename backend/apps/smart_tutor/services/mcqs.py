import json

from apps.ai.services.llm import AIProviderError, AIUnavailable, generate_text
from .flashcards import _pdf_text


def _fallback_mcqs(topic, count, reference):
    detail = ' '.join(reference.split())[:400] or f'the key concepts of {topic}'
    return [
        {
            'question': f'Which statement best describes {topic}?',
            'options': [detail, 'An unrelated concept', 'A contradictory claim', 'None of these'],
            'correct_answer': detail,
            'explanation': 'This option is supported by the uploaded PDF.',
        }
        for _ in range(count)
    ]


def generate_mcqs(topic, count=4, file=None):
    reference = _pdf_text(file) if file else ''
    instructions = '''You are RISE Tutor. Create multiple-choice questions in valid JSON only, using only the uploaded PDF.
Return exactly: {"mcqs": [{"question": "...", "options": ["...", "...", "...", "..."], "correct_answer": "exact option text", "explanation": "..."}]}.
Create the requested number of distinct questions. Include exactly four options per question. Do not invent facts or use outside knowledge. Do not include text outside the JSON.'''
    try:
        raw = generate_text(instructions, f'Topic: {topic}\nNumber of MCQs: {count}\n<uploaded_pdf>\n{reference}\n</uploaded_pdf>')
        payload = json.loads(raw.strip().removeprefix('```json').removesuffix('```').strip())
        mcqs = []
        for item in payload.get('mcqs', [])[:count]:
            options = [str(option).strip() for option in item.get('options', []) if str(option).strip()]
            answer = str(item.get('correct_answer', '')).strip()
            if isinstance(item, dict) and item.get('question') and len(options) == 4 and answer in options:
                mcqs.append({'question': str(item['question']).strip(), 'options': options, 'correct_answer': answer, 'explanation': str(item.get('explanation', '')).strip()})
        if len(mcqs) != count:
            raise AIProviderError('MCQ response did not contain the requested number of valid questions.')
        return mcqs
    except (AIUnavailable, AIProviderError, TypeError, AttributeError, json.JSONDecodeError):
        return _fallback_mcqs(topic, count, reference)
