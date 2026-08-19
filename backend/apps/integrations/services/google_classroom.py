from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .google_tokens import GoogleAuthenticationRequired, credentials_for

class ClassroomApiError(Exception):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)

class GoogleClassroomService:
    def __init__(self, connection, client_builder=build):
        self.connection = connection
        try:
            credentials = credentials_for(connection)
            self.client = client_builder('classroom', 'v1', credentials=credentials, cache_discovery=False)
        except GoogleAuthenticationRequired:
            raise

    def _collect(self, request_factory, key):
        items = []
        page_token = None
        while True:
            request = request_factory(page_token)
            try:
                payload = request.execute()
            except HttpError as exc:
                status = getattr(exc.resp, 'status', 500)
                raise ClassroomApiError(status, 'Google Classroom request failed.') from exc
            items.extend(payload.get(key, []))
            page_token = payload.get('nextPageToken')
            if not page_token:
                return items

    def get_courses(self):
        return self._collect(lambda token: self.client.courses().list(studentId='me', pageSize=100, **({'pageToken': token} if token else {})), 'courses')

    def get_course(self, course_id):
        try:
            return self.client.courses().get(id=course_id).execute()
        except HttpError as exc:
            raise ClassroomApiError(getattr(exc.resp, 'status', 500), 'Google Classroom course could not be loaded.') from exc

    def get_coursework(self, course_id):
        return self._collect(lambda token: self.client.courses().courseWork().list(courseId=course_id, courseWorkStates=['PUBLISHED'], pageSize=100, **({'pageToken': token} if token else {})), 'courseWork')

    def get_course_materials(self, course_id):
        return self._collect(lambda token: self.client.courses().courseWorkMaterials().list(courseId=course_id, courseWorkMaterialStates=['PUBLISHED'], pageSize=100, **({'pageToken': token} if token else {})), 'courseWorkMaterial')

    def get_student_submissions(self, course_id, coursework_id):
        return self._collect(lambda token: self.client.courses().courseWork().studentSubmissions().list(courseId=course_id, courseWorkId=coursework_id, userId='me', pageSize=100, **({'pageToken': token} if token else {})), 'studentSubmissions')
