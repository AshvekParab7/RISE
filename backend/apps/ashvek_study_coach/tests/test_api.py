from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APITestCase
from apps.accounts.models import User
from apps.academics.models import Semester, Subject, Topic
from apps.resources.models import Resource
from ..models import TutorSession


class TutorApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('ashvek@example.com', 'Password123!')
        self.other = User.objects.create_user('other@example.com', 'Password123!')
        self.semester = Semester.objects.create(student=self.user, name='Semester 5', year=2026, semester_number=5, is_current=True)
        self.subject = Subject.objects.create(semester=self.semester, name='Machine Learning', code='ML')
        self.topic = Topic.objects.create(subject=self.subject, unit_name='Unit 4', name='K-Means', mastery_percentage=20)
        self.client.force_authenticate(self.user)

    def test_session_creation_is_owned_and_validates_resources(self):
        response = self.client.post('/api/ashvek/study-coach/sessions/', {'topic': 'K-Means', 'subject_id': self.subject.id, 'topic_id': self.topic.id}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TutorSession.objects.get().user, self.user)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f"/api/ashvek/study-coach/sessions/{response.data['id']}/").status_code, 404)

    @patch('apps.ashvek_study_coach.services.coach.generate_text', side_effect=RuntimeError('offline'))
    def test_teach_answer_and_continue_are_persistent_with_fallback(self, _generate):
        session = TutorSession.objects.create(user=self.user, subject=self.subject, topic=self.topic, topic_label='K-Means', resource_ids=[])
        teach = self.client.post('/api/ashvek/study-coach/teach/', {'session_id': session.id, 'prompt': 'Teach me K-Means'}, format='json')
        self.assertEqual(teach.status_code, 200)
        answer = self.client.post('/api/ashvek/study-coach/answer/', {'session_id': session.id, 'answer': 'It groups similar points around representatives.'}, format='json')
        self.assertEqual(answer.status_code, 200)
        session.refresh_from_db()
        self.assertGreaterEqual(session.points, 20)
        self.assertTrue(session.current_question)
        self.assertGreaterEqual(len(session.messages), 3)

    def test_resource_isolation_rejects_other_student_resource(self):
        other_semester = Semester.objects.create(student=self.other, name='Other', year=2026, semester_number=1)
        other_subject = Subject.objects.create(semester=other_semester, name='Other Subject', code='OT')
        resource = Resource.objects.create(student=self.other, subject=other_subject, title='Private', processing_status=Resource.ProcessingStatus.READY)
        response = self.client.post('/api/ashvek/study-coach/sessions/', {'topic': 'K-Means', 'subject_id': self.subject.id, 'resource_ids': [resource.id]}, format='json')
        self.assertEqual(response.status_code, 400)

    @patch('apps.ashvek_study_coach.services.coach.generate_text', side_effect=RuntimeError('offline'))
    def test_help_request_reteaches_and_asks_simpler_question(self, _generate):
        session = TutorSession.objects.create(user=self.user, subject=self.subject, topic=self.topic, topic_label='K-Means')
        self.client.post('/api/ashvek/study-coach/teach/', {'session_id': session.id}, format='json')
        response = self.client.post('/api/ashvek/study-coach/answer/', {'session_id': session.id, 'help_requested': True}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['evaluation']['help_requested'])
        self.assertIn('explanation', response.data['reteach'])
        self.assertEqual(response.data['session']['points'], 7)

    @patch('apps.ashvek_study_coach.services.coach.generate_text')
    def test_correct_answer_increases_follow_up_difficulty(self, generate):
        generate.side_effect = [
            '{"explanation":"A short concept.","example":"A simple example.","question":{"id":"q1","type":"CONCEPTUAL","prompt":"What is it?","options":[]}}',
            '{"correct":true,"score":95,"feedback":"You identified the concept.","missing_points":[],"misconception":"","understood":["Core idea"],"weakness":""}',
            '{"id":"q2","type":"SCENARIO","prompt":"Apply it.","options":[],"difficulty":"APPLICATION"}',
        ]
        session = TutorSession.objects.create(user=self.user, subject=self.subject, topic=self.topic, topic_label='K-Means')
        self.client.post('/api/ashvek/study-coach/teach/', {'session_id': session.id}, format='json')
        response = self.client.post('/api/ashvek/study-coach/answer/', {'session_id': session.id, 'answer': 'It groups similar data points.'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['next_question']['difficulty'], 'APPLICATION')
        self.assertEqual(response.data['session']['concepts']['Core idea'], 'STRONG')

    @patch('apps.ashvek_study_coach.services.coach.generate_text')
    def test_incorrect_answer_records_weakness_and_simplifies(self, generate):
        generate.side_effect = [
            '{"explanation":"A short concept.","example":"A simple example.","question":{"id":"q1","type":"CONCEPTUAL","prompt":"What is it?","options":[]}}',
            '{"correct":false,"score":20,"feedback":"That mixes up the main idea.","missing_points":["classification target"],"misconception":"You confused categories with continuous values.","understood":[],"weakness":"Target variable"}',
            '{"id":"q2","type":"CONCEPTUAL","prompt":"Which target is a category?","options":["spam or not spam","house price"],"difficulty":"FOUNDATION"}',
        ]
        session = TutorSession.objects.create(user=self.user, subject=self.subject, topic=self.topic, topic_label='K-Means')
        self.client.post('/api/ashvek/study-coach/teach/', {'session_id': session.id}, format='json')
        response = self.client.post('/api/ashvek/study-coach/answer/', {'session_id': session.id, 'answer': 'It predicts an exact number.'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Target variable', response.data['session']['weaknesses'])
        self.assertEqual(response.data['next_question']['difficulty'], 'FOUNDATION')

    @patch('apps.ashvek_study_coach.services.coach.generate_assessment')
    def test_practice_keeps_answer_key_server_side(self, generate):
        from apps.ai.models import GeneratedQuestion, GeneratedTest
        test = GeneratedTest.objects.create(student=self.user, subject=self.subject, topic=self.topic, difficulty='EASY', question_count=1)
        GeneratedQuestion.objects.create(test=test, order=0, question='Which center is updated?', options=['Centroid', 'Database'], correct_answer='Centroid')
        generate.return_value = (test, [], True)
        session = TutorSession.objects.create(user=self.user, subject=self.subject, topic=self.topic, topic_label='K-Means')
        response = self.client.post('/api/ashvek/study-coach/practice/', {'session_id': session.id, 'question_count': 1, 'difficulty': 'EASY'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('correct_answer', response.data['questions'][0])

    def test_complete_report_and_points(self):
        session = TutorSession.objects.create(user=self.user, topic_label='K-Means', concepts={'centroids': 'STRONG'}, weaknesses=['Choosing K'])
        response = self.client.post(f'/api/ashvek/study-coach/sessions/{session.id}/complete/', format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], TutorSession.Status.COMPLETED)
        self.assertIn('Choosing K', response.data['report']['weak_concepts'])
        self.assertGreaterEqual(response.data['points'], 25)
