import json
from datetime import timedelta
from unittest.mock import patch

from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.academics.models import Semester, Subject, Topic
from apps.ai.models import GeneratedQuestion, ResourceChunk
from apps.resources.models import Resource
from apps.tasks.models import StudySession


class FocusSessionApiTests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user('focus-a@example.com', 'Password123!')
        self.user_b = User.objects.create_user('focus-b@example.com', 'Password123!')
        self.client.force_authenticate(self.user_a)
        semester_a = Semester.objects.create(student=self.user_a, name='Semester 5', year=2026, semester_number=5, is_current=True)
        semester_b = Semester.objects.create(student=self.user_b, name='Semester 1', year=2026, semester_number=1, is_current=True)
        self.subject = Subject.objects.create(semester=semester_a, name='Computer Networks', code='CN')
        self.topic = Topic.objects.create(subject=self.subject, unit_name='Transport', name='Congestion control')
        self.other_subject = Subject.objects.create(semester=semester_b, name='Other Subject', code='OS')
        self.resource = Resource.objects.create(
            student=self.user_a, subject=self.subject, title='Transport notes',
            processing_status=Resource.ProcessingStatus.READY, is_ai_ready=True,
        )
        self.other_resource = Resource.objects.create(
            student=self.user_b, subject=self.other_subject, title='Other notes',
            processing_status=Resource.ProcessingStatus.READY, is_ai_ready=True,
        )

    def start(self, resource_ids=None, subject=None, topic=None):
        payload = {
            'subject': str((subject or self.subject).id),
            'selected_resource_ids': [str(value) for value in (resource_ids or [self.resource.id])],
        }
        if topic:
            payload['topic'] = str(topic.id)
        return self.client.post('/api/study-sessions/focus/start/', payload, format='json')

    def test_focus_start_persists_ready_resources_and_server_state(self):
        response = self.start()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        session = StudySession.objects.get(pk=response.data['id'])
        self.assertEqual(session.focus_state, StudySession.FocusState.ACTIVE)
        self.assertEqual(session.status, StudySession.Status.ACTIVE)
        self.assertEqual(session.remaining_seconds, 45 * 60)
        self.assertEqual([str(value) for value in response.data['selected_resources']], [str(self.resource.id)])

    def test_study_guide_uses_selected_resource_content(self):
        started = self.start(topic=self.topic)
        ResourceChunk.objects.create(
            resource=self.resource,
            student=self.user_a,
            subject=self.subject,
            text='Congestion control regulates traffic to prevent overload and packet loss.',
            chunk_index=0,
        )
        response = self.client.post(
            f"/api/study-sessions/{started.data['id']}/focus/study-guide/",
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['source_titles'], ['Transport notes'])
        self.assertIn('Congestion control regulates traffic', response.data['key_takeaways'][0])
        self.assertEqual(len(response.data['steps']), 4)

    def test_focus_start_rejects_another_users_resource(self):
        response = self.start(resource_ids=[self.other_resource.id])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_focus_state_pause_resume_and_quit_are_server_owned(self):
        started = self.start()
        session_id = started.data['id']
        paused = self.client.post(f'/api/study-sessions/{session_id}/focus/state/', {'action': 'pause'}, format='json')
        self.assertEqual(paused.status_code, status.HTTP_200_OK)
        self.assertEqual(paused.data['focus_state'], StudySession.FocusState.PAUSED_BREAK)
        resumed = self.client.post(f'/api/study-sessions/{session_id}/focus/state/', {'action': 'resume'}, format='json')
        self.assertEqual(resumed.status_code, status.HTTP_200_OK)
        self.assertEqual(resumed.data['focus_state'], StudySession.FocusState.ACTIVE)
        quit_response = self.client.post(
            f'/api/study-sessions/{session_id}/focus/state/',
            {'action': 'quit', 'end_reason': 'Need to leave'},
            format='json',
        )
        self.assertEqual(quit_response.status_code, status.HTTP_200_OK)
        self.assertEqual(quit_response.data['status'], StudySession.Status.ABANDONED)
        self.assertEqual(quit_response.data['end_reason'], 'Need to leave')

    @patch('apps.ai.services.assessment_service.retrieve', return_value=[])
    def test_smart_break_question_is_scoped_and_hides_answer_key(self, retrieve):
        started = self.start(topic=self.topic)
        response = self.client.post(f"/api/study-sessions/{started.data['id']}/focus/smart-break/question/", format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('correct_answer', response.data['question'])
        self.assertEqual(response.data['question']['options'][0], f'Understanding {self.topic.name}')
        retrieve.assert_called_once()
        self.assertEqual(set(str(value) for value in retrieve.call_args.kwargs['resource_ids']), {str(self.resource.id)})

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('apps.ai.services.assessment_service.generate_text')
    @patch('apps.ai.services.assessment_service.retrieve')
    def test_quit_quiz_uses_openai_with_selected_note_context(self, retrieve, generate):
        chunk = ResourceChunk.objects.create(
            resource=self.resource,
            student=self.user_a,
            subject=self.subject,
            text='Logistic Regression uses the sigmoid function for binary classification.',
            chunk_index=0,
        )
        retrieve.return_value = [chunk]
        generate.return_value = json.dumps([{
            'question': 'What does Logistic Regression use for binary classification?',
            'options': ['The sigmoid function', 'A sorting algorithm', 'A database index', 'A network socket'],
            'correct_answer': 'The sigmoid function',
            'explanation': 'The notes describe the sigmoid function as the core component.',
        }])
        started = self.start(topic=self.topic)
        response = self.client.post(
            f"/api/study-sessions/{started.data['id']}/focus/smart-break/question/",
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['question']['question'], 'What does Logistic Regression use for binary classification?')
        self.assertIn(chunk.text, generate.call_args.args[1])

    @patch('apps.ai.services.assessment_service.retrieve', return_value=[])
    def test_incorrect_smart_break_answer_keeps_session_active(self, _retrieve):
        started = self.start(topic=self.topic)
        session_id = started.data['id']
        self.client.post(f'/api/study-sessions/{session_id}/focus/smart-break/question/', format='json')
        response = self.client.post(f'/api/study-sessions/{session_id}/focus/smart-break/answer/', {'answer': 'wrong'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['correct'])
        self.assertEqual(response.data['focus_state'], StudySession.FocusState.ACTIVE)
        self.assertIsNone(StudySession.objects.get(pk=session_id).smart_break_test_id)

    @patch('apps.ai.services.assessment_service.retrieve', return_value=[])
    def test_correct_smart_break_answer_authorizes_ten_minute_break(self, _retrieve):
        started = self.start(topic=self.topic)
        session_id = started.data['id']
        self.client.post(f'/api/study-sessions/{session_id}/focus/smart-break/question/', format='json')
        question = GeneratedQuestion.objects.get(test__focus_break_sessions__id=session_id)
        response = self.client.post(
            f'/api/study-sessions/{session_id}/focus/smart-break/answer/',
            {'answer': question.correct_answer},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['correct'])
        self.assertEqual(response.data['break_seconds'], 600)
        session = StudySession.objects.get(pk=session_id)
        self.assertEqual(session.focus_state, StudySession.FocusState.PAUSED_BREAK)
        self.assertGreater(session.break_unlock_expires_at, timezone.now() + timedelta(minutes=9))

    def test_expired_smart_break_relocks_session_as_active(self):
        started = self.start(topic=self.topic)
        session = StudySession.objects.get(pk=started.data['id'])
        session.focus_state = StudySession.FocusState.PAUSED_BREAK
        session.break_unlock_expires_at = timezone.now() - timedelta(seconds=1)
        session.save(update_fields=('focus_state', 'break_unlock_expires_at'))
        response = self.client.get('/api/study-sessions/focus/current/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['focus_state'], StudySession.FocusState.ACTIVE)