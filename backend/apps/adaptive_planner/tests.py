import json
from datetime import date, datetime, time, timedelta
from unittest.mock import Mock, patch

import requests
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.academics.models import CollegeClass, Exam, Semester, Subject, Topic
from apps.accounts.models import User
from apps.integrations.models import GoogleConnection
from apps.integrations.models_classroom import GoogleCourse, GoogleCoursework
from apps.resources.models import Resource
from apps.tasks.models import PlannerEvent, Task

from .models import ExamScheduleUpload
from .services.exam_schedule_parser import extract_schedule_text, parse_exam_rows
from .services.plan_builder import build_plan_preview


class ExamScheduleParserTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('parser@example.com', 'Password123!')
        semester = Semester.objects.create(student=self.user, name='Semester 5', year=2026, semester_number=5, is_current=True)
        self.subject = Subject.objects.create(semester=semester, name='Computer Networks', code='CN')

    @patch('apps.adaptive_planner.services.exam_schedule_parser.PdfReader')
    def test_pdf_text_is_normalized_into_exam_row(self, reader):
        page = Mock()
        page.extract_text.return_value = 'Computer Networks Final 2026-09-20 09:00 11:00 Room 101'
        reader.return_value.pages = [page]
        upload = SimpleUploadedFile('exam.pdf', b'%PDF-1.4', content_type='application/pdf')

        rows = parse_exam_rows(extract_schedule_text(upload), [self.subject])

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['subject'], self.subject)
        self.assertEqual(rows[0]['exam_date'], date(2026, 9, 20))
        self.assertEqual(rows[0]['start_time'], time(9))
        self.assertEqual(rows[0]['end_time'], time(11))
        self.assertEqual(rows[0]['confidence'], 95)

    def test_ocr_table_text_supports_ordinal_dates_and_dotted_times(self):
        content = Subject.objects.create(semester=self.subject.semester, name='Content Writing')
        communication = Subject.objects.create(semester=self.subject.semester, name='Effective Communication Skills-II')
        text = '07-02-2024 (Wednesday)\n11.00 am to 11.40 am\nContent Writing\n11.40 am to 12.20 pm\nEffective Communication Skills-II'

        rows = parse_exam_rows(text, [self.subject, content, communication])

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['exam_date'], date(2024, 2, 7))
        self.assertEqual(rows[0]['start_time'], time(11))
        self.assertEqual(rows[0]['end_time'], time(11, 40))
        self.assertEqual(rows[0]['subject'], content)
        self.assertEqual(rows[1]['start_time'], time(11, 40))
        self.assertEqual(rows[1]['end_time'], time(12, 20))

    def test_ocr_table_text_supports_ordinal_month_dates(self):
        subject = Subject.objects.create(semester=self.subject.semester, name='Hindi Course-B', code='085')
        text = 'Friday, 10th March, 2017 10.30 A.M. TO 1.30 P.M. 085 Hindi Course-B'

        rows = parse_exam_rows(text, [subject])

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['exam_date'], date(2017, 3, 10))
        self.assertEqual(rows[0]['start_time'], time(10, 30))
        self.assertEqual(rows[0]['end_time'], time(13, 30))

    def test_global_written_exam_time_backfills_date_rows(self):
        history = Subject.objects.create(semester=self.subject.semester, name='History')
        maths = Subject.objects.create(semester=self.subject.semester, name='Maths')
        text = '11/10/2019 Friday History Maths\n12/10/2019 Saturday History Maths\nTime for written examination is 9.00 a.m. to 11.15 am.'

        rows = parse_exam_rows(text, [history, maths])

        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row['start_time'] == time(9) for row in rows))
        self.assertTrue(all(row['end_time'] == time(11, 15) for row in rows))

    @patch.dict('sys.modules', {'pytesseract': None})
    def test_image_without_ocr_dependency_requires_review(self):
        upload = SimpleUploadedFile('exam.png', b'not-an-image', content_type='image/png')
        with self.assertRaises(Exception) as raised:
            extract_schedule_text(upload)
        self.assertIn('OCR', str(raised.exception))


@override_settings(GEMINI_API_KEY='')
class AdaptivePlannerApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('planner@example.com', 'Password123!')
        self.other = User.objects.create_user('other-planner@example.com', 'Password123!')
        self.semester = Semester.objects.create(student=self.user, name='Semester 5', year=2026, semester_number=5, is_current=True)
        self.subject = Subject.objects.create(semester=self.semester, name='Computer Networks', code='CN', difficulty=Subject.Difficulty.HARD, mastery_percentage=35)
        self.topic = Topic.objects.create(subject=self.subject, unit_name='Unit 1', name='Transport Layer', mastery_percentage=20)
        self.client.force_authenticate(self.user)

    def create_upload(self):
        response = self.client.post(
            '/api/adaptive-planner/exam-schedule-uploads/',
            {'file': SimpleUploadedFile('exam.pdf', b'not-a-readable-pdf', content_type='application/pdf')},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response

    def test_upload_returns_editable_review_row_and_confirmation_creates_exam(self):
        upload_response = self.create_upload()
        self.assertEqual(upload_response.data['status'], ExamScheduleUpload.Status.NEEDS_REVIEW)
        row = upload_response.data['rows'][0]
        confirm = self.client.post(
            f"/api/adaptive-planner/exam-schedule-uploads/{upload_response.data['id']}/confirm/",
            {'rows': [{
                'id': row['id'],
                'subject': str(self.subject.id),
                'title': 'CN Final',
                'exam_date': '2026-09-20',
                'start_time': '09:00',
                'end_time': '11:00',
                'venue': 'Room 101',
            }]},
            format='json',
        )
        self.assertEqual(confirm.status_code, status.HTTP_200_OK)
        self.assertEqual(confirm.data['status'], ExamScheduleUpload.Status.CONFIRMED)
        self.assertEqual(Exam.objects.get().source, Exam.Source.IMPORTED)

        repeat = self.client.post(
            f"/api/adaptive-planner/exam-schedule-uploads/{upload_response.data['id']}/confirm/",
            {'rows': [{
                'id': row['id'],
                'subject': str(self.subject.id),
                'title': 'CN Final Updated',
                'exam_date': '2026-09-20',
                'start_time': '09:00',
                'end_time': '11:00',
                'venue': 'Room 102',
            }]},
            format='json',
        )
        self.assertEqual(repeat.status_code, status.HTTP_200_OK)
        self.assertEqual(Exam.objects.count(), 1)
        self.assertEqual(Exam.objects.get().title, 'CN Final Updated')

    def test_client_ocr_text_is_parsed_without_server_ocr(self):
        response = self.client.post(
            '/api/adaptive-planner/exam-schedule-uploads/',
            {
                'file': SimpleUploadedFile('exam.jpg', b'not-an-image', content_type='image/jpeg'),
                'ocr_text': '07-02-2024 11.00 am to 11.40 am Computer Networks',
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(response.data['rows'][0]['subject']), str(self.subject.id))
        self.assertEqual(response.data['rows'][0]['exam_date'], '2024-02-07')

    @override_settings(GEMINI_API_KEY='test-key', GEMINI_MODEL='gemini-test')
    @patch('apps.adaptive_planner.services.exam_schedule_parser.requests.post')
    def test_gemini_extracts_all_exam_rows_from_uploaded_document(self, post):
        maths = Subject.objects.create(semester=self.semester, name='Mathematics', code='MATH')
        response = Mock()
        response.json.return_value = {'candidates': [{
            'content': {'parts': [{'text': json.dumps([
                {'subject_name': 'Computer Networks', 'subject_code': 'CN', 'title': 'CN Final', 'exam_date': '2026-09-20', 'start_time': '09:00', 'end_time': '11:00', 'venue': 'Room 101'},
                {'subject_name': 'Mathematics', 'subject_code': 'MATH', 'title': 'Mathematics Final', 'exam_date': '2026-09-22', 'start_time': '13:00', 'end_time': '15:00', 'venue': 'Hall A'},
            ])}]},
        }]}
        response.raise_for_status.return_value = None
        post.return_value = response

        upload = self.client.post(
            '/api/adaptive-planner/exam-schedule-uploads/',
            {'file': SimpleUploadedFile('exam.pdf', b'%PDF schedule', content_type='application/pdf')},
            format='multipart',
        )

        self.assertEqual(upload.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(upload.data['rows']), 2)
        self.assertEqual(str(upload.data['rows'][0]['subject']), str(self.subject.id))
        self.assertEqual(str(upload.data['rows'][1]['subject']), str(maths.id))
        self.assertEqual(upload.data['rows'][1]['exam_date'], '2026-09-22')
        self.assertEqual(upload.data['rows'][1]['venue'], 'Hall A')
        self.assertIn('gemini-test:generateContent', post.call_args.args[0])

    @override_settings(GEMINI_API_KEY='test-key', GEMINI_MODEL='retired-model')
    @patch('apps.adaptive_planner.services.exam_schedule_parser.requests.post')
    def test_gemini_retries_with_current_model_after_model_not_found(self, post):
        unavailable = Mock(status_code=404)
        available = Mock(status_code=200)
        available.json.return_value = {'candidates': [{
            'content': {'parts': [{'text': json.dumps([{
                'subject_name': 'Computer Networks', 'subject_code': 'CN', 'title': 'CN Final', 'exam_date': '2026-09-20', 'start_time': '09:00', 'end_time': '11:00', 'venue': 'Room 101',
            }])}]},
        }]}
        available.raise_for_status.return_value = None
        post.side_effect = [unavailable, available]

        upload = self.client.post(
            '/api/adaptive-planner/exam-schedule-uploads/',
            {'file': SimpleUploadedFile('exam.pdf', b'%PDF schedule', content_type='application/pdf')},
            format='multipart',
        )

        self.assertEqual(upload.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(upload.data['rows']), 1)
        self.assertEqual(post.call_count, 2)
        self.assertIn('gemini-3.6-flash:generateContent', post.call_args.args[0])

    @override_settings(GEMINI_API_KEY='test-key')
    @patch('apps.adaptive_planner.services.exam_schedule_parser.requests.post')
    def test_local_parser_is_used_when_gemini_is_unavailable(self, post):
        post.side_effect = requests.RequestException('network unavailable')

        response = self.client.post(
            '/api/adaptive-planner/exam-schedule-uploads/',
            {
                'file': SimpleUploadedFile('exam.jpg', b'not-an-image', content_type='image/jpeg'),
                'ocr_text': '07-02-2024 11.00 am to 11.40 am Computer Networks',
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(response.data['rows'][0]['subject']), str(self.subject.id))
        self.assertEqual(response.data['rows'][0]['exam_date'], '2024-02-07')

    def test_upload_is_user_scoped(self):
        response = self.create_upload()
        self.client.force_authenticate(self.other)
        detail = self.client.get(f"/api/adaptive-planner/exam-schedule-uploads/{response.data['id']}/")
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_overview_contains_mission_weak_topic_resource_and_classroom_deadline(self):
        Exam.objects.create(semester=self.semester, subject=self.subject, title='CN Final', exam_date=date.today() + timedelta(days=5), start_time=time(9), end_time=time(11))
        Resource.objects.create(
            student=self.user,
            subject=self.subject,
            title='Transport notes',
            file=SimpleUploadedFile('transport.pdf', b'%PDF-1.4', content_type='application/pdf'),
            is_ai_ready=True,
            processing_status=Resource.ProcessingStatus.READY,
        )
        task = Task.objects.create(student=self.user, subject=self.subject, title='CN assignment', deadline=timezone.now() + timedelta(days=1), estimated_minutes=90, priority=Task.Priority.HIGH, source=Task.Source.GOOGLE_CLASSROOM)
        connection = GoogleConnection.objects.create(user=self.user, google_user_id='google-planner', email='planner@gmail.com')
        course = GoogleCourse.objects.create(google_connection=connection, google_course_id='course-1', name='Computer Networks', rise_subject=self.subject)
        GoogleCoursework.objects.create(google_course=course, google_coursework_id='work-1', title=task.title, due_date=date.today() + timedelta(days=1), rise_task=task, alternate_link='https://classroom.google.com/work-1')

        overview = self.client.get('/api/adaptive-planner/overview/')

        self.assertEqual(overview.status_code, status.HTTP_200_OK)
        self.assertEqual(overview.data['exam_missions'][0]['status'], 'AT_RISK')
        self.assertEqual(overview.data['weak_topics'][0]['topic'], 'Transport Layer')
        self.assertEqual(overview.data['weak_topics'][0]['difficulty_label'], 'Hard')
        self.assertEqual(overview.data['weak_topics'][0]['resources'][0]['title'], 'Transport notes')
        self.assertEqual(overview.data['deadline_rescue'][0]['link'], 'https://classroom.google.com/work-1')
        self.assertIn('action', overview.data['next_action'])

    def test_plan_preview_links_subject_resources_to_study_block(self):
        resource = Resource.objects.create(
            student=self.user,
            subject=self.subject,
            title='Transport notes',
            file=SimpleUploadedFile('transport.pdf', b'%PDF-1.4', content_type='application/pdf'),
            is_ai_ready=True,
            processing_status=Resource.ProcessingStatus.READY,
        )
        Resource.objects.create(
            student=self.user,
            subject=self.subject,
            title='Still processing notes',
            is_ai_ready=False,
            processing_status=Resource.ProcessingStatus.PROCESSING,
        )
        start_date = date.today() + timedelta(days=1)

        preview = self.client.post('/api/adaptive-planner/plan/preview/', {
            'start_date': start_date.isoformat(),
            'days': 1,
            'daily_minutes': 60,
            'day_start': '08:00',
            'day_end': '14:00',
        }, format='json')

        self.assertEqual(preview.status_code, status.HTTP_200_OK)
        self.assertTrue(preview.data['blocks'])
        self.assertEqual(preview.data['blocks'][0]['resource_ids'], [str(resource.id)])
        self.assertEqual(preview.data['blocks'][0]['resource_titles'], ['Transport notes'])

    def test_plan_preview_avoids_college_class_and_commit_persists(self):
        start_date = date.today() + timedelta(days=1)
        CollegeClass.objects.create(semester=self.semester, subject=self.subject, day_of_week=start_date.weekday(), start_time=time(8), end_time=time(12), room='A-101')
        preview = self.client.post('/api/adaptive-planner/plan/preview/', {
            'start_date': start_date.isoformat(),
            'days': 1,
            'daily_minutes': 60,
            'day_start': '08:00',
            'day_end': '14:00',
        }, format='json')

        self.assertEqual(preview.status_code, status.HTTP_200_OK)
        self.assertTrue(preview.data['blocks'])
        block = preview.data['blocks'][0]
        self.assertGreaterEqual(datetime.fromisoformat(block['start_at'].replace('Z', '+00:00')).hour, 12)
        self.assertEqual(PlannerEvent.objects.count(), 0)
        commit = self.client.post('/api/adaptive-planner/plan/commit/', {'blocks': [block]}, format='json')
        self.assertEqual(commit.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PlannerEvent.objects.count(), 1)

    def test_plan_preview_avoids_exam_time(self):
        start_date = date.today() + timedelta(days=1)
        Exam.objects.create(semester=self.semester, subject=self.subject, title='CN Final', exam_date=start_date, start_time=time(8), end_time=time(12))

        preview = self.client.post('/api/adaptive-planner/plan/preview/', {
            'start_date': start_date.isoformat(),
            'days': 1,
            'daily_minutes': 60,
            'day_start': '08:00',
            'day_end': '14:00',
        }, format='json')

        self.assertEqual(preview.status_code, status.HTTP_200_OK)
        self.assertTrue(preview.data['blocks'])
        block_start = datetime.fromisoformat(preview.data['blocks'][0]['start_at'].replace('Z', '+00:00'))
        self.assertGreaterEqual(block_start.hour, 12)

    def test_plan_preview_caps_repeated_focus_blocks_per_day(self):
        start_date = date.today() + timedelta(days=1)
        preview = self.client.post('/api/adaptive-planner/plan/preview/', {
            'start_date': start_date.isoformat(),
            'days': 1,
            'daily_minutes': 180,
            'day_start': '08:00',
            'day_end': '20:00',
        }, format='json')

        self.assertEqual(preview.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(preview.data['blocks']), 2)
        self.assertLessEqual(preview.data['scheduled_minutes'], 90)

    def test_next_action_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.get('/api/adaptive-planner/next-action/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
