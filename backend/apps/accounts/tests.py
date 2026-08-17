from datetime import date, time, timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from apps.academics.models import CollegeClass, Exam, Semester, Subject, Syllabus, Topic
from apps.resources.models import Resource
from apps.tasks.models import StudySession, Task
from .models import User

class CoreApiTests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user('a@example.com', 'Password123!')
        self.user_b = User.objects.create_user('b@example.com', 'Password123!')
        self.client.force_authenticate(self.user_a)

    def create_semester(self):
        response = self.client.post('/api/semesters/', {'name': 'Semester 5', 'year': 2026, 'semester_number': 5, 'is_current': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data['id']

    def create_subject(self, semester_id, name='Computer Networks'):
        response = self.client.post('/api/subjects/', {'semester': semester_id, 'name': name, 'code': 'CN', 'mastery_percentage': 52, 'priority_score': 91}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data['id']

    def test_registration_login_and_current_user(self):
        self.client.force_authenticate(None)
        register = self.client.post('/api/auth/register/', {'email': 'new@example.com', 'password': 'Password123!', 'first_name': 'New'}, format='json')
        self.assertEqual(register.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', register.data)
        login = self.client.post('/api/auth/login/', {'email': 'new@example.com', 'password': 'Password123!'}, format='json')
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        self.assertEqual(self.client.get('/api/auth/me/').data['email'], 'new@example.com')
        logout = self.client.post('/api/auth/logout/', {'refresh': login.data['refresh']}, format='json')
        self.assertEqual(logout.status_code, status.HTTP_204_NO_CONTENT)
        refresh = self.client.post('/api/token/refresh/', {'refresh': login.data['refresh']}, format='json')
        self.assertEqual(refresh.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_requests_are_rejected(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/semesters/').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_academic_crud_and_validation(self):
        semester_id = self.create_semester()
        subject_id = self.create_subject(semester_id)
        topic = self.client.post('/api/topics/', {'subject': subject_id, 'unit_name': 'Unit 1', 'name': 'TCP', 'mastery_percentage': 20}, format='json')
        self.assertEqual(topic.status_code, status.HTTP_201_CREATED)
        invalid = self.client.post('/api/topics/', {'subject': subject_id, 'unit_name': 'Unit 1', 'name': 'Bad', 'mastery_percentage': 101}, format='json')
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        exam = self.client.post('/api/exams/', {'semester': semester_id, 'subject': subject_id, 'title': 'CN Exam', 'exam_date': '2026-08-25', 'start_time': '09:00', 'end_time': '11:00'}, format='json')
        self.assertEqual(exam.status_code, status.HTTP_201_CREATED)
        timetable = self.client.post('/api/college-timetable/', {'semester': semester_id, 'subject': subject_id, 'day_of_week': 0, 'start_time': '09:00', 'end_time': '10:00'}, format='json')
        self.assertEqual(timetable.status_code, status.HTTP_201_CREATED)

    def test_upload_task_completion_and_study_session(self):
        semester_id = self.create_semester()
        subject_id = self.create_subject(semester_id)
        topic_id = self.client.post('/api/topics/', {'subject': subject_id, 'unit_name': 'Unit 1', 'name': 'TCP'}, format='json').data['id']
        file = SimpleUploadedFile('cn-notes.pdf', b'%PDF demo', content_type='application/pdf')
        resource = self.client.post('/api/resources/', {'subject': subject_id, 'title': 'CN Notes', 'file': file, 'resource_type': 'NOTE'}, format='multipart')
        self.assertEqual(resource.status_code, status.HTTP_201_CREATED)
        task = self.client.post('/api/tasks/', {'subject': subject_id, 'title': 'CN Lab', 'deadline': (timezone.now() + timedelta(days=1)).isoformat(), 'estimated_minutes': 90, 'priority': 'HIGH'}, format='json')
        self.assertEqual(task.status_code, status.HTTP_201_CREATED)
        completed = self.client.patch(f"/api/tasks/{task.data['id']}/", {'status': 'COMPLETED'}, format='json')
        self.assertEqual(completed.status_code, status.HTTP_200_OK)
        session = self.client.post('/api/study-sessions/', {'subject': subject_id, 'topic': topic_id, 'planned_minutes': 45}, format='json')
        self.assertEqual(session.status_code, status.HTTP_201_CREATED)

    def test_syllabus_upload(self):
        semester_id = self.create_semester()
        file = SimpleUploadedFile('semester-syllabus.pdf', b'%PDF syllabus', content_type='application/pdf')
        response = self.client.post('/api/syllabus/', {'semester': semester_id, 'title': 'Semester Syllabus', 'file': file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_data_isolation_for_get_and_write(self):
        semester_id = self.create_semester()
        subject_id = self.create_subject(semester_id)
        self.client.force_authenticate(self.user_b)
        other_semester = self.client.post('/api/semesters/', {'name': 'Other', 'year': 2026, 'semester_number': 1}, format='json').data['id']
        self.assertEqual(self.client.get('/api/subjects/').data, [])
        forbidden = self.client.post('/api/subjects/', {'semester': semester_id, 'name': 'Cross-user'}, format='json')
        self.assertEqual(forbidden.status_code, status.HTTP_400_BAD_REQUEST)
        self.client.force_authenticate(self.user_a)
        self.assertEqual(self.client.delete(f'/api/subjects/{subject_id}/').status_code, status.HTTP_204_NO_CONTENT)
        self.client.force_authenticate(self.user_b)
        self.assertEqual(self.client.get(f'/api/semesters/{other_semester}/').status_code, status.HTTP_200_OK)

    def test_health_and_schema(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/health/').json(), {'status': 'ok'})
        self.assertEqual(self.client.get('/api/schema/').status_code, status.HTTP_200_OK)
