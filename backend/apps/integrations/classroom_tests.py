from datetime import timedelta
from unittest.mock import Mock, patch
from django.test import TestCase
from django.utils import timezone as django_timezone
from apps.accounts.models import User
from apps.academics.models import Semester, Subject
from apps.resources.models import Resource
from apps.tasks.models import Task
from .models import GoogleConnection
from .models_classroom import GoogleCourse, GoogleCoursework, GoogleMaterial
from .services.classroom_sync import ClassroomSyncEngine
from .services.google_classroom import GoogleClassroomService
from .services.google_tokens import GoogleAuthenticationRequired, credentials_for
from .services.google_classroom_gis import CLASSROOM_GIS_SCOPES, ClassroomTokenError, authorize_classroom_connection

class FakeSyncService:
    def __init__(self, connection): self.connection = connection
    def get_courses(self): return [{'id': 'course-1', 'name': 'Computer Networks', 'courseState': 'ACTIVE', 'creationTime': '2026-08-01T00:00:00Z', 'updateTime': '2026-08-02T00:00:00Z'}]
    def get_coursework(self, course_id): return [{'id': 'work-1', 'title': 'Implement Binary Search', 'description': 'Submit the report.', 'state': 'PUBLISHED', 'workType': 'ASSIGNMENT', 'dueDate': {'year': 2026, 'month': 9, 'day': 20}, 'dueTime': {'hours': 17, 'minutes': 0}, 'alternateLink': 'https://classroom.google.com/work-1', 'updateTime': '2026-08-02T00:00:00Z'}]
    def get_course_materials(self, course_id): return [{'id': 'material-1', 'title': 'Transport Slides', 'alternateLink': 'https://classroom.google.com/material-1', 'materials': [{'link': {'url': 'https://example.com/slides'}}]}]
    def get_student_submissions(self, course_id, coursework_id): return [{'id': 'submission-1', 'state': 'TURNED_IN', 'late': False, 'updateTime': '2026-08-03T00:00:00Z'}]

class ClassroomSyncTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('classroom@example.com', 'Password123!')
        self.semester = Semester.objects.create(student=self.user, name='Semester 5', year=2026, semester_number=5, is_current=True)
        self.subject = Subject.objects.create(semester=self.semester, name='Computer Networks', code='CN')
        self.connection = GoogleConnection.objects.create(user=self.user, google_user_id='google-1', email='classroom@gmail.com', scopes=['openid'])

    def test_sync_is_idempotent_and_maps_courses_and_materials(self):
        first = ClassroomSyncEngine(self.connection, FakeSyncService).sync()
        second = ClassroomSyncEngine(self.connection, FakeSyncService).sync()
        self.assertEqual(first['courses_created'], 1)
        self.assertEqual(first['tasks_created'], 0)
        self.assertEqual(first['resources_created'], 1)
        self.assertEqual(second['courses_created'], 0)
        self.assertEqual(GoogleCourse.objects.count(), 1)
        self.assertEqual(GoogleCoursework.objects.count(), 0)
        self.assertEqual(GoogleMaterial.objects.count(), 1)
        self.assertEqual(Task.objects.filter(source=Task.Source.GOOGLE_CLASSROOM).count(), 0)
        self.assertEqual(Resource.objects.filter(source=Resource.Source.GOOGLE_CLASSROOM).count(), 1)

    def test_course_archive_does_not_delete_rise_subject(self):
        ClassroomSyncEngine(self.connection, FakeSyncService).sync()
        course = GoogleCourse.objects.get()
        course.course_state = 'ARCHIVED'; course.is_active = False; course.save()
        self.assertTrue(Subject.objects.filter(pk=self.subject.pk).exists())

    @patch('apps.integrations.services.google_classroom.build')
    @patch('apps.integrations.services.google_classroom.credentials_for')
    def test_classroom_list_follows_next_page_token(self, credentials_for_mock, build_mock):
        credentials_for_mock.return_value = Mock()
        class Request:
            def __init__(self, payload): self.payload = payload
            def execute(self): return self.payload
        class Courses:
            def __init__(self): self.calls = 0
            def list(self, **_kwargs):
                self.calls += 1
                return Request({'courses': [{'id': 'one'}], 'nextPageToken': 'next'} if self.calls == 1 else {'courses': [{'id': 'two'}]})
        class Client:
            def __init__(self): self.resource = Courses()
            def courses(self): return self.resource
        build_mock.return_value = Client()
        result = GoogleClassroomService(self.connection, client_builder=build_mock).get_courses()
        self.assertEqual([item['id'] for item in result], ['one', 'two'])
        self.assertEqual(build_mock.return_value.resource.calls, 2)

    @patch('apps.integrations.services.google_tokens.Request')
    def test_refresh_failure_marks_connection_inactive(self, request_mock):
        connection = self.connection
        connection.set_tokens('expired', 'refresh'); connection.token_expiry = django_timezone.now() - timedelta(minutes=5); connection.save()
        with patch('apps.integrations.services.google_tokens.Credentials.refresh', side_effect=RuntimeError('refresh failed')):
            with self.assertRaises(GoogleAuthenticationRequired): credentials_for(connection)
        connection.refresh_from_db()
        self.assertFalse(connection.is_active)

class ClassroomGisAuthorizationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('gis@example.com', 'Password123!')

    @patch('apps.integrations.services.google_classroom_gis.requests.get')
    @patch('apps.integrations.services.google_classroom_gis.settings.GOOGLE_CLIENT_ID', 'gis-client')
    def test_valid_gis_token_is_encrypted_and_owned_by_user(self, get_mock):
        response = Mock(status_code=200)
        response.json.return_value = {'aud': 'gis-client', 'user_id': 'google-student', 'email': 'student@gmail.com', 'scope': ' '.join(CLASSROOM_GIS_SCOPES), 'expires_in': '3600'}
        get_mock.return_value = response
        connection = authorize_classroom_connection(self.user, 'browser-access-token')
        self.assertTrue(connection.is_active)
        self.assertEqual(connection.google_user_id, 'google-student')
        self.assertEqual(connection.get_access_token(), 'browser-access-token')
        self.assertNotEqual(connection.access_token_encrypted, 'browser-access-token')

    @patch('apps.integrations.services.google_classroom_gis.requests.get')
    @patch('apps.integrations.services.google_classroom_gis.settings.GOOGLE_CLIENT_ID', 'gis-client')
    def test_valid_gis_token_without_identity_claim_is_owned_by_rise_user(self, get_mock):
        response = Mock(status_code=200)
        response.json.return_value = {'aud': 'gis-client', 'scope': ' '.join(CLASSROOM_GIS_SCOPES), 'expires_in': '3600'}
        get_mock.return_value = response
        connection = authorize_classroom_connection(self.user, 'browser-access-token')
        self.assertTrue(connection.is_active)
        self.assertEqual(connection.user_id, self.user.id)
        self.assertEqual(connection.google_user_id, '')
        self.assertEqual(connection.email, '')

    @patch('apps.integrations.services.google_classroom_gis.requests.get')
    def test_invalid_gis_token_is_rejected(self, get_mock):
        get_mock.return_value = Mock(status_code=401)
        with self.assertRaises(ClassroomTokenError): authorize_classroom_connection(self.user, 'invalid')

    @patch('apps.integrations.services.google_classroom_gis.requests.get')
    @patch('apps.integrations.services.google_classroom_gis.settings.GOOGLE_CLIENT_ID', 'gis-client')
    def test_missing_classroom_scope_is_rejected(self, get_mock):
        response = Mock(status_code=200)
        response.json.return_value = {'aud': 'gis-client', 'user_id': 'google-student', 'email': 'student@gmail.com', 'scope': CLASSROOM_GIS_SCOPES[0], 'expires_in': '3600'}
        get_mock.return_value = response
        with self.assertRaises(ClassroomTokenError): authorize_classroom_connection(self.user, 'browser-access-token')

    @patch('apps.integrations.services.google_classroom_gis.requests.get')
    @patch('apps.integrations.services.google_classroom_gis.settings.GOOGLE_CLIENT_ID', 'gis-client')
    def test_google_identity_cannot_be_claimed_by_another_user(self, get_mock):
        other = User.objects.create_user('other-gis@example.com', 'Password123!')
        GoogleConnection.objects.create(user=other, google_user_id='google-student', email='student@gmail.com')
        response = Mock(status_code=200)
        response.json.return_value = {'aud': 'gis-client', 'user_id': 'google-student', 'email': 'student@gmail.com', 'scope': ' '.join(CLASSROOM_GIS_SCOPES), 'expires_in': '3600'}
        get_mock.return_value = response
        with self.assertRaises(ClassroomTokenError): authorize_classroom_connection(self.user, 'browser-access-token')
