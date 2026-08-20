from unittest.mock import patch

from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

from .services.flashcards import generate_flashcards


class FlashcardTests(TestCase):
    @override_settings(OPENAI_API_KEY='')
    def test_flashcards_have_requested_count_without_provider(self):
        cards = generate_flashcards('TCP congestion control', 4)
        self.assertEqual(len(cards), 4)
        self.assertTrue(all(card['question'] and card['answer'] for card in cards))

    @patch('apps.smart_tutor.views.generate_flashcards', return_value=[{'question': 'Q', 'answer': 'A'}] * 3)
    def test_flashcard_endpoint_defaults_to_three(self, generate):
        upload = SimpleUploadedFile('notes.pdf', b'%PDF', content_type='application/pdf')
        response = self.client.post('/api/smart-tutor/flashcards/', {'topic': 'binary trees', 'file': upload})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['flashcards']), 3)
        self.assertEqual(generate.call_args.args[:2], ('binary trees', 3))
