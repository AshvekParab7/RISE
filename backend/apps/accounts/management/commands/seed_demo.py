from datetime import date, datetime, time, timedelta
from pathlib import Path
from django.core.files.base import ContentFile
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import User
from apps.academics.models import CollegeClass, Exam, Semester, Subject, Syllabus, Topic
from apps.ai.models import ResourceChunk
from apps.ai.services.resource_processing import process_resource
from apps.resources.models import Resource
from apps.tasks.models import StudySession, Task

class Command(BaseCommand):
    help = 'Create or update a realistic RISE demo workspace.'

    def handle(self, *args, **options):
        user, _ = User.objects.get_or_create(email='student@rise.local', defaults={'first_name': 'Aarav', 'last_name': 'Mehta'})
        user.set_password('RiseDemo123!')
        user.first_name, user.last_name = 'Aarav', 'Mehta'; user.save()
        semester, _ = Semester.objects.update_or_create(student=user, year=2026, semester_number=5, defaults={'name': 'Semester 5', 'is_current': True, 'start_date': date(2026, 7, 1), 'end_date': date(2026, 12, 31)})
        subject_specs = [('Computer Networks', 'CN', 'HARD', 52, 91, date(2026, 8, 25)), ('Database Systems', 'DBMS', 'MEDIUM', 72, 72, date(2026, 8, 28)), ('Operating Systems', 'OS', 'MEDIUM', 58, 58, date(2026, 8, 31)), ('Python Programming', 'PY', 'EASY', 84, 34, date(2026, 9, 4)), ('Mathematics', 'MA', 'MEDIUM', 66, 47, date(2026, 9, 8))]
        subjects = {}
        for name, code, difficulty, mastery, priority, exam_date in subject_specs:
            subject, _ = Subject.objects.update_or_create(semester=semester, name=name, defaults={'code': code, 'difficulty': difficulty, 'mastery_percentage': mastery, 'priority_score': priority, 'exam_date': exam_date, 'target_grade': 'A', 'color': '#9733EE'})
            subjects[code] = subject
        for code, units in {'CN': [100, 85, 60, 20, 0], 'DBMS': [100, 90, 76, 54, 40], 'OS': [100, 80, 62, 30, 12], 'PY': [100, 100, 92, 84, 70], 'MA': [92, 80, 65, 50, 35]}.items():
            for index, mastery in enumerate(units, 1):
                status = Topic.Status.MASTERED if mastery >= 80 else Topic.Status.IN_PROGRESS if mastery else Topic.Status.NOT_STARTED
                Topic.objects.update_or_create(subject=subjects[code], unit_name=f'Unit {index}', name=f'{subjects[code].name} Unit {index} Foundations', defaults={'order': index, 'mastery_percentage': mastery, 'status': status})
        for code, title, day, start, end in [('CN', 'Computer Networks Exam', 25, time(9), time(11)), ('DBMS', 'Database Systems Exam', 28, time(14), time(16)), ('OS', 'Operating Systems Exam', 31, time(9), time(11))]:
            Exam.objects.update_or_create(semester=semester, subject=subjects[code], title=title, defaults={'exam_date': date(2026, 8, day), 'start_time': start, 'end_time': end, 'venue': 'Main Hall', 'source': Exam.Source.MANUAL})
        for index, code in enumerate(['CN', 'DBMS', 'OS', 'PY', 'MA']):
            CollegeClass.objects.update_or_create(semester=semester, subject=subjects[code], day_of_week=index, start_time=time(9), defaults={'end_time': time(10), 'room': f'Room {300 + index}', 'instructor': 'Professor RISE'})
        task_specs = [('CN Lab Report', 'CN', 2, Task.Priority.HIGH, Task.Source.GOOGLE_CLASSROOM), ('Normalization worksheet', 'DBMS', 45, Task.Priority.MEDIUM, Task.Source.MANUAL), ('Python Mini Project', 'PY', 240, Task.Priority.LOW, Task.Source.GOOGLE_CLASSROOM)]
        for title, code, minutes, priority, source in task_specs:
            Task.objects.update_or_create(student=user, title=title, defaults={'subject': subjects[code], 'deadline': timezone.make_aware(datetime(2026, 8, 19, 17)), 'estimated_minutes': minutes, 'priority': priority, 'source': source, 'status': Task.Status.TODO})
        demo_resource_content = {
            'CN Unit 1 Notes.pdf': 'Computer networks exchange data between hosts. The transport layer provides end-to-end communication, while congestion control regulates the sending rate to prevent overload, packet loss, and unstable queues.',
            'Transport Layer Slides.pdf': 'Reliable transport uses sequencing, acknowledgements, and retransmission. Congestion control observes network conditions and adjusts the sender window so throughput remains useful without overwhelming the network.',
            'DBMS Normalization Slides.pdf': 'Database normalization organizes related data to reduce redundancy and update anomalies. First normal form uses atomic values, second normal form removes partial dependency, and third normal form removes transitive dependency.',
        }
        for title, code in [('CN Unit 1 Notes.pdf', 'CN'), ('Transport Layer Slides.pdf', 'CN'), ('DBMS Normalization Slides.pdf', 'DBMS')]:
            resource, created = Resource.objects.get_or_create(student=user, title=title, defaults={'subject': subjects[code], 'resource_type': Resource.ResourceType.NOTE, 'source': Resource.Source.USER_UPLOAD, 'description': 'Demo study resource'})
            if created: resource.file.save(title, ContentFile(b'RISE demo resource'), save=True)
            ResourceChunk.objects.update_or_create(
                resource=resource,
                chunk_index=0,
                defaults={
                    'student': user,
                    'subject': subjects[code],
                    'text': demo_resource_content[title],
                    'embedding': [],
                },
            )
            resource.processing_status = Resource.ProcessingStatus.READY
            resource.processing_error = ''
            resource.processed_at = timezone.now()
            resource.is_ai_ready = True
            resource.save(update_fields=('processing_status', 'processing_error', 'processed_at', 'is_ai_ready', 'updated_at'))
        test_pdf_path = Path(__file__).resolve().parents[5] / 'Test_pdf' / 'Unit 2 Question Answers.pdf'
        if test_pdf_path.exists():
            test_resource, created = Resource.objects.get_or_create(
                student=user,
                title=test_pdf_path.name,
                defaults={
                    'subject': subjects['CN'],
                    'resource_type': Resource.ResourceType.DOCUMENT,
                    'source': Resource.Source.USER_UPLOAD,
                    'description': 'Local PDF upload test resource',
                },
            )
            if created or not test_resource.file:
                test_resource.subject = subjects['CN']
                test_resource.file.save(test_pdf_path.name, File(test_pdf_path.open('rb')), save=True)
                process_resource(test_resource)
        syllabus, created = Syllabus.objects.get_or_create(semester=semester, title='Semester 5 Syllabus')
        if created: syllabus.file.save('semester-5-syllabus.pdf', ContentFile(b'RISE demo syllabus'), save=True); syllabus.processing_status = Syllabus.ProcessingStatus.PROCESSED; syllabus.save()
        topic = subjects['CN'].topics.order_by('order').first()
        if not StudySession.objects.filter(student=user, subject=subjects['CN'], topic=topic, planned_minutes=45).exists():
            StudySession.objects.create(student=user, subject=subjects['CN'], topic=topic, planned_minutes=45, status=StudySession.Status.PLANNED)
        self.stdout.write(self.style.SUCCESS('Demo workspace seeded for student@rise.local / RiseDemo123!.'))
