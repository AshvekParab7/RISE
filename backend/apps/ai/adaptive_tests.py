from django.test import TestCase, override_settings
from rest_framework.test import APITestCase
from apps.accounts.models import User
from apps.academics.models import Semester, Subject, Topic
from .models import GeneratedTest

class AdaptiveAssessmentApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('adaptive@example.com', 'Password123!')
        semester = Semester.objects.create(student=self.user, name='Semester 5', year=2026, semester_number=5, is_current=True)
        self.subject = Subject.objects.create(semester=semester, name='Database Systems')
        self.topic = Topic.objects.create(subject=self.subject, unit_name='Unit 3', name='Normalization', mastery_percentage=40)
        self.client.force_authenticate(self.user)

    @override_settings(OPENAI_API_KEY='')
    def test_generation_hides_answer_key_and_submission_updates_mastery(self):
        response = self.client.post('/api/ai/tests/generate/', {'subject_id': self.subject.id, 'topic_id': self.topic.id, 'difficulty': 'MEDIUM', 'question_count': 3}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertNotIn('correct_answer', response.data['questions'][0])
        answers = [{'question_id': item['id'], 'selected_option': item['options'][0]} for item in response.data['questions']]
        result = self.client.post(f"/api/ai/tests/{response.data['assessment_id']}/submit/", {'answers': answers}, format='json')
        self.assertEqual(result.status_code, 200)
        self.assertIn('mastery_change', result.data)
        self.assertIn('daily_plan', result.data)
        self.assertIn('next_action', result.data)
        self.topic.refresh_from_db()
        self.assertGreater(self.topic.mastery_percentage, 40)
        self.subject.refresh_from_db()
        self.assertGreater(self.subject.priority_score, 0)
        duplicate = self.client.post(f"/api/ai/tests/{response.data['assessment_id']}/submit/", {'answers': answers}, format='json')
        self.assertEqual(duplicate.status_code, 409)

    @override_settings(OPENAI_API_KEY='')
    def test_generation_adapts_difficulty_for_low_mastery(self):
        self.topic.mastery_percentage = 20
        self.topic.save(update_fields=['mastery_percentage'])
        response = self.client.post('/api/ai/tests/generate/', {'subject_id': self.subject.id, 'topic_id': self.topic.id, 'question_count': 1}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['questions'][0]['difficulty'], 'EASY')
