from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.academics.models import Semester, Subject


class PlannerEventApiTests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user('planner-a@example.com', 'Password123!')
        self.user_b = User.objects.create_user('planner-b@example.com', 'Password123!')
        self.client.force_authenticate(self.user_a)
        semester = Semester.objects.create(student=self.user_a, name='Semester 5', year=2026, semester_number=5, is_current=True)
        self.subject = Subject.objects.create(semester=semester, name='Computer Networks', code='CN')
        self.start = (timezone.now() + timedelta(days=1)).replace(second=0, microsecond=0)

    def create_event(self):
        response = self.client.post('/api/planner-events/', {
            'subject': str(self.subject.id),
            'title': 'TCP revision',
            'subtopics': 'Congestion control and flow control',
            'start_at': self.start.isoformat(),
            'duration_minutes': 60,
            'color': '#E7984A',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response

    def test_planner_event_crud_and_day_filter(self):
        created = self.create_event()
        self.assertEqual(created.data['duration_minutes'], 60)
        self.assertEqual(created.data['subtopics'], 'Congestion control and flow control')
        self.assertEqual(self.client.get(f"/api/planner-events/?day={self.start.date().isoformat()}").data[0]['id'], created.data['id'])
        updated = self.client.patch(f"/api/planner-events/{created.data['id']}/", {'duration_minutes': 90}, format='json')
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data['duration_minutes'], 90)
        self.assertEqual(self.client.delete(f"/api/planner-events/{created.data['id']}/").status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.client.get('/api/planner-events/').data, [])

    def test_planner_events_are_user_scoped_for_reads_and_writes(self):
        created = self.create_event()
        self.client.force_authenticate(self.user_b)
        self.assertEqual(self.client.get('/api/planner-events/').data, [])
        self.assertEqual(self.client.get(f"/api/planner-events/{created.data['id']}/").status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.patch(f"/api/planner-events/{created.data['id']}/", {'title': 'Changed'}, format='json').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(f"/api/planner-events/{created.data['id']}/").status_code, status.HTTP_404_NOT_FOUND)

    def test_planner_event_rejects_subject_from_another_user(self):
        other_semester = Semester.objects.create(student=self.user_b, name='Other', year=2026, semester_number=1)
        other_subject = Subject.objects.create(semester=other_semester, name='Other Subject', code='OS')
        response = self.client.post('/api/planner-events/', {'subject': str(other_subject.id), 'title': 'Cross user', 'start_at': self.start.isoformat(), 'duration_minutes': 45}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
