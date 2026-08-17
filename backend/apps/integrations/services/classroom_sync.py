from datetime import datetime, time
from django.db import transaction
from django.utils import timezone
from apps.academics.models import Semester, Subject
from apps.resources.models import Resource
from apps.tasks.models import Task
from .google_classroom import ClassroomApiError, GoogleClassroomService
from ..models_classroom import GoogleCourse, GoogleCoursework, GoogleMaterial, GoogleSubmission


def _parse_google_datetime(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def _due(coursework):
    due = coursework.get('dueDate')
    if not due:
        return timezone.now()
    due_date = datetime(int(due['year']), int(due['month']), int(due['day']))
    due_time = coursework.get('dueTime', {})
    due_date = due_date.replace(hour=int(due_time.get('hours', 23)), minute=int(due_time.get('minutes', 59)), second=int(due_time.get('seconds', 0)))
    return timezone.make_aware(due_date)


def _resource_type(material):
    if material.get('driveFile'):
        mime = material['driveFile'].get('driveFile', {}).get('mimeType', '')
        return Resource.ResourceType.SLIDES if 'presentation' in mime else Resource.ResourceType.DOCUMENT
    if material.get('youTubeVideo'):
        return Resource.ResourceType.OTHER
    if material.get('link'):
        return Resource.ResourceType.OTHER
    return Resource.ResourceType.OTHER


def _material_details(item):
    materials = item.get('materials', [])
    if not materials:
        return 'OTHER', '', ''
    material = materials[0]
    if 'driveFile' in material:
        drive = material['driveFile'].get('driveFile', {})
        return _resource_type(material), drive.get('alternateLink', ''), drive.get('mimeType', '')
    if 'link' in material:
        return Resource.ResourceType.OTHER, material['link'].get('url', ''), ''
    if 'youTubeVideo' in material:
        return Resource.ResourceType.OTHER, material['youTubeVideo'].get('alternateLink', ''), 'video/*'
    return Resource.ResourceType.OTHER, '', ''

class ClassroomSyncEngine:
    def __init__(self, connection, service_class=GoogleClassroomService):
        self.connection = connection
        self.service = service_class(connection)

    @transaction.atomic
    def sync(self):
        summary = {'courses_found': 0, 'courses_created': 0, 'courses_updated': 0, 'tasks_created': 0, 'tasks_updated': 0, 'resources_created': 0, 'resources_updated': 0, 'errors': []}
        courses = self.service.get_courses(); summary['courses_found'] = len(courses)
        semester = Semester.objects.filter(student=self.connection.user, is_current=True).first() or Semester.objects.filter(student=self.connection.user).first()
        for course in courses:
            try:
                course_id = course['id']
                subject = Subject.objects.filter(semester__student=self.connection.user, name=course.get('name', '')).first()
                if not subject and semester:
                    subject = Subject.objects.create(semester=semester, name=course.get('name', 'Google Classroom Course'), code=f'GC-{course_id[-6:]}', difficulty=Subject.Difficulty.MEDIUM, target_grade='')
                record, created = GoogleCourse.objects.update_or_create(google_connection=self.connection, google_course_id=course_id, defaults={'name': course.get('name', ''), 'section': course.get('section', ''), 'description': course.get('description', ''), 'room': course.get('room', ''), 'course_state': course.get('courseState', ''), 'course_created_at': _parse_google_datetime(course.get('creationTime')), 'course_updated_at': _parse_google_datetime(course.get('updateTime')), 'rise_subject': subject, 'last_synced_at': timezone.now(), 'is_active': course.get('courseState', 'ACTIVE') != 'DELETED'})
                summary['courses_created' if created else 'courses_updated'] += 1
                for work in self.service.get_coursework(course_id): self._sync_work(record, work, summary)
                for material in self.service.get_course_materials(course_id): self._sync_material(record, material, summary)
            except (KeyError, ClassroomApiError, Exception) as exc:
                summary['errors'].append({'course_id': course.get('id'), 'message': 'Course sync failed.'})
        self.connection.last_synced_at = timezone.now(); self.connection.save(update_fields=['last_synced_at', 'updated_at'])
        return summary

    def _sync_work(self, course, work, summary):
        work_id = work['id']; due = _due(work); snapshot = {'title': work.get('title', ''), 'description': work.get('description', ''), 'deadline': due.isoformat(), 'state': work.get('state', '')}
        record, created = GoogleCoursework.objects.update_or_create(google_course=course, google_coursework_id=work_id, defaults={'title': work.get('title', ''), 'description': work.get('description', ''), 'state': work.get('state', ''), 'work_type': work.get('workType', ''), 'due_date': due.date(), 'due_time': due.time(), 'alternate_link': work.get('alternateLink', ''), 'creation_time': _parse_google_datetime(work.get('creationTime')), 'update_time': _parse_google_datetime(work.get('updateTime')), 'max_points': work.get('maxPoints'), 'source_snapshot': snapshot, 'last_synced_at': timezone.now()})
        task = record.rise_task
        if not task:
            task = Task.objects.create(student=self.connection.user, subject=course.rise_subject, title=work.get('title', ''), description=work.get('description', ''), deadline=due, estimated_minutes=60, priority=Task.Priority.MEDIUM, source=Task.Source.GOOGLE_CLASSROOM)
            record.rise_task = task; record.save(update_fields=['rise_task', 'updated_at']); summary['tasks_created'] += 1
        elif task.source == Task.Source.GOOGLE_CLASSROOM:
            task.title = work.get('title', ''); task.description = work.get('description', ''); task.deadline = due; task.save(update_fields=['title', 'description', 'deadline', 'updated_at']); summary['tasks_updated'] += 1
        for submission in self.service.get_student_submissions(course.google_course_id, work_id): self._sync_submission(record, submission)

    def _sync_submission(self, work, submission):
        record, _ = GoogleSubmission.objects.update_or_create(google_coursework=work, google_submission_id=submission['id'], defaults={'state': submission.get('state', ''), 'assigned_grade': submission.get('assignedGrade'), 'draft_grade': submission.get('draftGrade'), 'late': submission.get('late', False), 'submission_time': _parse_google_datetime(submission.get('submissionHistory', [{}])[-1].get('stateHistory', {}).get('stateTimestamp')) if submission.get('submissionHistory') else None, 'update_time': _parse_google_datetime(submission.get('updateTime')), 'last_synced_at': timezone.now()})
        if work.rise_task and work.rise_task.source == Task.Source.GOOGLE_CLASSROOM and record.state == 'RETURNED' and work.rise_task.status != Task.Status.COMPLETED:
            work.rise_task.status = Task.Status.COMPLETED; work.rise_task.save(update_fields=['status', 'completed_at', 'updated_at'])

    def _sync_material(self, course, item, summary):
        material_type, source_url, mime_type = _material_details(item); record, created = GoogleMaterial.objects.update_or_create(google_course=course, google_material_id=item['id'], defaults={'title': item.get('title', 'Classroom material'), 'material_type': material_type, 'alternate_link': item.get('alternateLink', ''), 'mime_type': mime_type, 'source_url': source_url, 'last_synced_at': timezone.now()})
        resource, resource_created = Resource.objects.update_or_create(student=self.connection.user, title=item.get('title', 'Classroom material'), defaults={'subject': course.rise_subject, 'description': source_url, 'file': '', 'resource_type': material_type, 'source': Resource.Source.GOOGLE_CLASSROOM, 'is_ai_ready': False})
        if record.rise_resource_id != resource.id: record.rise_resource = resource; record.save(update_fields=['rise_resource', 'updated_at'])
        summary['resources_created' if resource_created else 'resources_updated'] += 1
