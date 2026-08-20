import json

from pypdf import PdfReader

from apps.ai.services.llm import AIProviderError, AIUnavailable, generate_text


def _fallback_flashcards(topic, count, reference=''):
    detail = ' '.join(reference.split())[:500] or f'the key concepts that make up {topic}'
    prompts = (
        ('What is the central idea of {topic}?', 'According to the uploaded PDF: {detail}'),
        ('Why is {topic} important according to the PDF?', 'The uploaded PDF explains: {detail}'),
        ('What is one key detail about {topic}?', 'A key detail from the uploaded PDF is: {detail}'),
    )
    return [
        {'question': question.format(topic=topic), 'answer': answer.format(topic=topic, detail=detail)}
        for question, answer in (prompts[index % len(prompts)] for index in range(count))
    ]


def _pdf_text(file):
    try:
        pages = [' '.join((page.extract_text() or '').split()) for page in PdfReader(file).pages]
    except Exception as exc:
        raise ValueError('The PDF could not be read.') from exc
    text = '\n'.join(f'[Page {index}] {page}' for index, page in enumerate(pages, 1) if page)
    if not text:
        raise ValueError('The PDF does not contain readable text.')
    return text[:60000]


def generate_flashcards(topic, count=3, file=None):
    reference = _pdf_text(file) if file else ''
    instructions = '''You are RISE Tutor. Create concise study flashcards in valid JSON only.
Return exactly this shape: {"flashcards": [{"question": "...", "answer": "..."}]}.
Create the requested number of distinct cards about the requested topic, using only the uploaded PDF as reference. Do not invent facts or use outside knowledge. Questions should test understanding, not trivia. Answers must be accurate, concise, and written in Markdown when formatting helps. Do not include any text outside the JSON.'''
    try:
        raw = generate_text(instructions, f'Topic: {topic}\nNumber of flashcards: {count}\n<uploaded_pdf>\n{reference}\n</uploaded_pdf>')
        payload = json.loads(raw.strip().removeprefix('```json').removesuffix('```').strip())
        cards = payload.get('flashcards', [])
        if not isinstance(cards, list):
            raise AIProviderError('Flashcards response was not a list.')
        cards = [
            {'question': str(card.get('question', '')).strip(), 'answer': str(card.get('answer', '')).strip()}
            for card in cards
            if isinstance(card, dict) and card.get('question') and card.get('answer')
        ][:count]
        if len(cards) != count:
            raise AIProviderError('Flashcards response did not contain the requested number of cards.')
        return cards
    except (AIUnavailable, AIProviderError, TypeError, json.JSONDecodeError):
        return _fallback_flashcards(topic, count, reference)
