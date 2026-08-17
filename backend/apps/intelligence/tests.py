from datetime import date, datetime, time, timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase
from apps.accounts.models import User
from apps.academics.models import CollegeClass, Exam, Semester, Subject, Topic
from apps.tasks.models import Task
from .services.priority_engine import calculate_subject_priority, calculate_topic_priority
from .services.recommendation_engine import build_context, build_next_action, calculate_priorities
from .services.workload_engine import build_workload_plan

class IntelligenceEngineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('intelligence@example.com', 'Password123!')
        self.semester = Semester.objects.create(student=self.user, name='Semester 5', year=2026, semester_number=5, is_current=True)
        self.subject = Subject.objects.create(semester=self.semester, name='Computer Networks', code='CN', difficulty=Subject.Difficulty.HARD, mastery_percentage=40, priority_score=0)
        self.topic = Topic.objects.create(subject=self.subject, unit_name='Unit 1', name='Transport Layer', mastery_percentage=20)

    def test_exam_proximity_and_low_mastery_raise_score(self):
        Exam.objects.create(semester=self.semester, subject=self.subject, title='Final', exam_date=date.today() + timedelta(days=1), start_time=time(9), end_time=time(11))
        context = build_context(self.user)
        result = calculate_subject_priority(self.subject, context)
        self.assertGreaterEqual(result['priority_score'], 50)
        self.assertTrue(any(reason['code'] == 'EXAM_SOON' for reason in result['reasons']))
        self.assertTrue(any(reason['code'] == 'LOW_MASTERY' for reason in result['reasons']))

    def test_mastered_subject_is_lower_priority_than_weak_topic(self):
        self.topic.mastery_percentage = 100; self.topic.save()
        result = calculate_topic_priority(self.topic, build_context(self.user))
        self.assertLess(result['priority_score'], 60)

    def test_deadline_and_effort_are_explainable(self):
        Task.objects.create(student=self.user, subject=self.subject, title='Lab', deadline=timezone.now() + timedelta(days=1), estimated_minutes=120, priority=Task.Priority.HIGH)
        result = calculate_subject_priority(self.subject, build_context(self.user))
        self.assertTrue(any(reason['code'] == 'PENDING_ASSIGNMENT' for reason in result['reasons']))

    def test_same_input_is_deterministic(self):
        context = build_context(self.user)
        self.assertEqual(calculate_subject_priority(self.subject, context), calculate_subject_priority(self.subject, context))

    def test_available_time_is_not_overbooked(self):
        priorities = [{'subject': 'CN', 'topic': 'TCP', 'priority_score': 90, 'estimated_minutes': 45, 'reasons': []}, {'subject': 'DB', 'topic': 'Normalization', 'priority_score': 80, 'estimated_minutes': 45, 'reasons': []}]
        result = build_workload_plan(priorities, [], {'blocked_windows': [], 'now': timezone.now()}, available_minutes=60)
        self.assertLessEqual(result['scheduled_minutes'], 60)
        self.assertEqual(result['status'], 'HEALTHY')

    def test_empty_academic_data_has_safe_next_action(self):
        empty = User.objects.create_user('empty@example.com', 'Password123!')
        self.assertIsNone(build_next_action(build_context(empty))['action'])

    def test_today_college_class_blocks_planning_window(self):
        now = timezone.localtime()
        CollegeClass.objects.create(semester=self.semester, subject=self.subject, day_of_week=now.weekday(), start_time=(now + timedelta(minutes=10)).time(), end_time=(now + timedelta(minutes=40)).time())
        context = build_context(self.user, day=now.date())
        result = build_workload_plan([{'subject': 'CN', 'topic': 'TCP', 'priority_score': 90, 'estimated_minutes': 45, 'reasons': []}], [], context, available_minutes=60)
        self.assertLess(result['available_minutes'], 60)
        self.assertLessEqual(result['scheduled_minutes'], result['available_minutes'])

class IntelligenceApiTests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user('priority-a@example.com', 'Password123!')
        self.user_b = User.objects.create_user('priority-b@example.com', 'Password123!')
        semester = Semester.objects.create(student=self.user_a, name='A Semester', year=2026, semester_number=1, is_current=True)
        Subject.objects.create(semester=semester, name='A Subject', code='A')
        self.client.force_authenticate(self.user_a)

    def test_priority_endpoints_are_authenticated_and_user_scoped(self):
        priorities = self.client.get('/api/intelligence/priorities/').data
        self.assertIn('priorities', priorities)
        self.assertEqual(priorities['priorities'][0]['subject'], 'A Subject')
        self.assertEqual(self.client.get('/api/intelligence/next-action/').status_code, 200)
        self.assertEqual(self.client.get('/api/intelligence/daily-plan/?available_minutes=30').status_code, 200)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/intelligence/priorities/').status_code, 401)
