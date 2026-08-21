from types import SimpleNamespace
from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APITestCase
from apps.accounts.models import User
from ..models import LearningLevel, LearningPath
from ..services.chunker import chunk_transcript
from ..services.processor import process_learning_path
from ..services.transcript import fetch_transcript
from ..services.youtube import YouTubeVideoError, extract_video_id


class PipelineUnitTests(TestCase):
    def test_youtube_url_validation(self):
        self.assertEqual(extract_video_id('https://www.youtube.com/watch?v=dQw4w9WgXcQ'), 'dQw4w9WgXcQ')
        self.assertEqual(extract_video_id('https://youtu.be/dQw4w9WgXcQ?t=10'), 'dQw4w9WgXcQ')
        with self.assertRaises(YouTubeVideoError): extract_video_id('https://example.com/video')

    @patch('apps.learning_paths.services.transcript.YouTubeTranscriptApi')
    def test_transcript_preserves_timestamps(self, api):
        transcript = [SimpleNamespace(text=' First line\n', start=0.5, duration=2.0), SimpleNamespace(text='Second line', start=3.0, duration=4.0)]
        api.return_value.fetch.return_value = transcript
        segments, language = fetch_transcript('dQw4w9WgXcQ')
        self.assertEqual(segments[0], {'text': 'First line', 'start': 0.5, 'duration': 2.0})
        self.assertEqual(segments[1]['start'], 3.0)

    def test_long_transcript_is_bounded_and_ordered(self):
        segments = [{'text': f'lecture section {index}', 'start': index * 60, 'duration': 50} for index in range(130)]
        chunks = chunk_transcript(segments, max_seconds=480, max_characters=6000)
        self.assertGreater(len(chunks), 10)
        self.assertEqual(chunks[0]['start_seconds'], 0)
        self.assertTrue(all(chunk['end_seconds'] - chunk['start_seconds'] <= 540 for chunk in chunks))
        self.assertEqual(chunks, sorted(chunks, key=lambda item: item['start_seconds']))

    @patch('apps.learning_paths.services.processor.generate_level')
    @patch('apps.learning_paths.services.processor.fetch_transcript')
    @patch('apps.learning_paths.services.processor.fetch_video_title')
    def test_processing_creates_ordered_levels(self, title, transcript, generate):
        user = User.objects.create_user('pipeline@example.com', 'Password123!')
        path = LearningPath.objects.create(user=user, youtube_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ', video_id='dQw4w9WgXcQ')
        title.return_value = 'Real Lecture'
        transcript.return_value = ([{'text': f'topic {index}', 'start': index * 300, 'duration': 280} for index in range(4)], 'en')
        generate.side_effect = lambda chunk, order: {'title': f'Level {order}', 'description': chunk['text'], 'objectives': [], 'key_concepts': [], 'notes': chunk['text'], 'checkpoint': {'type': 'SHORT_ANSWER', 'question': 'Explain this section', 'correct_answer': ['topic']}}
        process_learning_path(path)
        path.refresh_from_db()
        self.assertEqual(path.status, LearningPath.Status.READY)
        self.assertEqual(list(path.levels.values_list('order', flat=True)), [1, 2, 3, 4])
        self.assertEqual(path.levels.first().status, LearningLevel.Status.AVAILABLE)
        self.assertEqual(path.levels.last().status, LearningLevel.Status.LOCKED)


class LearningPathApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('learner@example.com', 'Password123!')
        self.other = User.objects.create_user('other-learner@example.com', 'Password123!')
        self.client.force_authenticate(self.user)
        self.path = LearningPath.objects.create(user=self.user, youtube_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ', video_id='dQw4w9WgXcQ', title='Lecture', status=LearningPath.Status.READY, processing_progress=100)
        self.level_one = LearningLevel.objects.create(learning_path=self.path, order=1, title='Foundations', transcript_text='classification probability', start_seconds=0, end_seconds=300, notes='Classification produces probabilities.', checkpoint={'type': 'SHORT_ANSWER', 'question': 'What does it produce?', 'correct_answer': ['probability'], 'explanation': 'It produces probabilities.'}, status=LearningLevel.Status.AVAILABLE)
        self.level_two = LearningLevel.objects.create(learning_path=self.path, order=2, title='Application', transcript_text='apply model', start_seconds=300, end_seconds=600, notes='Apply the model.', checkpoint={'type': 'SHORT_ANSWER', 'question': 'How is it applied?', 'correct_answer': ['model']}, status=LearningLevel.Status.LOCKED)

    @patch('apps.learning_paths.views.enqueue_learning_path')
    def test_duplicate_submission_returns_existing_path(self, process):
        response = self.client.post('/api/learning/youtube/', {'url': self.path.youtube_url}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], str(self.path.id))
        process.assert_not_called()

    @patch('apps.learning_paths.views.enqueue_learning_path')
    def test_new_submission_is_queued_with_processing_status(self, enqueue):
        response = self.client.post('/api/learning/youtube/', {'url': 'https://youtu.be/9bZkp7q19f0'}, format='json')
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['status'], LearningPath.Status.PROCESSING)
        enqueue.assert_called_once()

    def test_user_isolation_and_locked_level(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f'/api/learning/{self.path.id}/').status_code, 404)
        self.client.force_authenticate(self.user)
        response = self.client.post(f'/api/learning/{self.path.id}/levels/{self.level_two.id}/start/', format='json')
        self.assertEqual(response.status_code, 409)

    def test_owner_can_delete_learning_path(self):
        response = self.client.delete(f'/api/learning/{self.path.id}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(LearningPath.objects.filter(id=self.path.id).exists())

    def test_checkpoint_unlocks_level_and_persists_notes_and_xp(self):
        self.client.post(f'/api/learning/{self.path.id}/levels/{self.level_one.id}/start/', format='json')
        response = self.client.post(f'/api/learning/{self.path.id}/checkpoint/', {'level_id': self.level_one.id, 'answer': 'It outputs a probability.'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['attempt']['correct'])
        self.level_two.refresh_from_db(); self.path.refresh_from_db()
        self.assertEqual(self.level_two.status, LearningLevel.Status.AVAILABLE)
        self.assertEqual(self.path.xp, 25)
        self.assertIn('Classification produces probabilities.', self.path.cumulative_notes)

    def test_incorrect_checkpoint_allows_retry_without_unlocking(self):
        response = self.client.post(f'/api/learning/{self.path.id}/checkpoint/', {'level_id': self.level_one.id, 'answer': 'A continuous price'}, format='json')
        self.assertFalse(response.data['attempt']['correct'])
        self.level_two.refresh_from_db(); self.assertEqual(self.level_two.status, LearningLevel.Status.LOCKED)

    def test_mcq_accepts_option_text_when_key_is_stored(self):
        self.level_one.checkpoint = {'type': 'multiple_choice', 'question': 'Which extension?', 'options': {'A': '.js', 'B': '.html', 'C': '.jsx'}, 'correct_answer': 'C', 'explanation': 'JSX mixes markup and JavaScript.'}
        self.level_one.save(update_fields=['checkpoint'])
        response = self.client.post(f'/api/learning/{self.path.id}/checkpoint/', {'level_id': self.level_one.id, 'answer': '.jsx'}, format='json')
        self.assertTrue(response.data['attempt']['correct'])
        self.assertIn('C. .jsx', response.data['level']['checkpoint']['options'])

    def test_mcq_accepts_labeled_option_text(self):
        self.level_one.checkpoint = {'type': 'multiple_choice', 'question': 'What does it mean?', 'options': ['A. Give something', 'B. Seem like a kind of person', 'C. Arrive early'], 'correct_answer': 'Seem like a kind of person', 'explanation': 'This is the meaning.'}
        self.level_one.save(update_fields=['checkpoint'])
        response = self.client.post(f'/api/learning/{self.path.id}/checkpoint/', {'level_id': self.level_one.id, 'answer': 'B. Seem like a kind of person'}, format='json')
        self.assertTrue(response.data['attempt']['correct'])

    def test_mcq_maps_letter_key_to_list_option_text(self):
        self.level_one.checkpoint = {'type': 'multiple_choice', 'question': 'What advice?', 'options': ['A. Pretend to be perfect.', 'B. Be yourself: smile, listen carefully, share ideas, breathe, and speak slowly.', 'C. Stay silent.', 'D. Change jobs.'], 'correct_answer': 'B', 'explanation': 'This is the advice from the transcript.'}
        self.level_one.save(update_fields=['checkpoint'])
        response = self.client.post(f'/api/learning/{self.path.id}/checkpoint/', {'level_id': self.level_one.id, 'answer': 'B. Be yourself: smile, listen carefully, share ideas, breathe, and speak slowly.'}, format='json')
        self.assertTrue(response.data['attempt']['correct'])

    def test_final_challenge_completes_course_without_exposing_answers(self):
        self.level_one.status = LearningLevel.Status.COMPLETED; self.level_one.save(update_fields=['status'])
        self.level_two.status = LearningLevel.Status.COMPLETED; self.level_two.save(update_fields=['status'])
        self.path.final_challenge = {'title': 'Final Challenge', 'questions': [{'id': str(self.level_one.id), 'question': 'What is produced?', 'type': 'SHORT_ANSWER', 'options': [], 'correct_answer': ['probability'], 'explanation': 'A probability.'}]}
        self.path.save(update_fields=['final_challenge'])
        challenge = self.client.get(f'/api/learning/{self.path.id}/final-challenge/')
        self.assertNotIn('correct_answer', challenge.data['questions'][0])
        response = self.client.post(f'/api/learning/{self.path.id}/final-challenge/', {'answers': {str(self.level_one.id): 'A probability'}}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['path']['status'], LearningPath.Status.COMPLETED)
        self.assertEqual(response.data['result']['mastery_percentage'], 100)

    @patch('apps.learning_paths.services.processor.fetch_video_title', side_effect=ValueError('Video unavailable'))
    def test_failed_processing_persists_reason(self, _title):
        failed = LearningPath.objects.create(user=self.user, youtube_url='https://www.youtube.com/watch?v=9bZkp7q19f0', video_id='9bZkp7q19f0')
        process_learning_path(failed); failed.refresh_from_db()
        self.assertEqual(failed.status, LearningPath.Status.FAILED)
        self.assertIn('Video unavailable', failed.failure_reason)
