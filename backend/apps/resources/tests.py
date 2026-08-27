from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.academics.models import Semester, Subject
from .models import Resource


class ResourceUploadApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('resource-upload@example.com', 'Password123!')
        self.client.force_authenticate(self.user)
        semester = Semester.objects.create(
            student=self.user,
            name='Semester 5',
            year=2026,
            semester_number=5,
            is_current=True,
        )
        self.subject = Subject.objects.create(semester=semester, name='Computer Networks')

    @patch('apps.resources.views.process_resource')
    def test_pdf_upload_saves_resource_and_runs_processing(self, process_resource):
        def mark_ready(resource):
            resource.processing_status = Resource.ProcessingStatus.READY
            resource.is_ai_ready = True
            resource.save(update_fields=('processing_status', 'is_ai_ready', 'updated_at'))
            return resource

        process_resource.side_effect = mark_ready
        response = self.client.post(
            '/api/resources/',
            {
                'subject': str(self.subject.id),
                'title': 'Unit 2 Question Answers.pdf',
                'resource_type': Resource.ResourceType.DOCUMENT,
                'file': SimpleUploadedFile('Unit 2 Question Answers.pdf', b'%PDF test', content_type='application/pdf'),
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['processing_status'], Resource.ProcessingStatus.READY)
        process_resource.assert_called_once()
