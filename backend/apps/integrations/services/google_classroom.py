from io import BytesIO
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
import logging
from .google_tokens import GoogleAuthenticationRequired, credentials_for
from apps.resources.models import MAX_FILE_SIZE

logger = logging.getLogger(__name__)

class ClassroomApiError(Exception):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)

class GoogleClassroomService:
    def __init__(self, connection, client_builder=build):
        self.connection = connection
        self.client_builder = client_builder
        try:
            credentials = credentials_for(connection)
            self.client = client_builder('classroom', 'v1', credentials=credentials, cache_discovery=False)
            self.credentials = credentials
            self.drive_client = None
        except GoogleAuthenticationRequired:
            raise

    def _drive(self):
        if self.drive_client is None:
            self.drive_client = self.client_builder('drive', 'v3', credentials=self.credentials, cache_discovery=False)
        return self.drive_client

    def _collect(self, request_factory, key):
        items = []
        page_token = None
        while True:
            request = request_factory(page_token)
            try:
                payload = request.execute()
            except HttpError as exc:
                status = getattr(exc.resp, 'status', 500)
                logger.error('Google Classroom API failed operation=%s status=%s response=%s', key, status, getattr(exc, 'content', b'')[:1000], exc_info=True)
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

    def download_material(self, item):
        materials = item.get('materials', [])
        drive_file = next((material.get('driveFile', {}).get('driveFile', {}) for material in materials if material.get('driveFile')), None)
        if not drive_file or not drive_file.get('id'):
            return None
        return self.download_drive_file(drive_file['id'], drive_file.get('title') or item.get('title', 'Classroom material'), drive_file.get('mimeType', ''))

    def download_drive_file(self, drive_file_id, name_hint='', mime_hint=''):
        drive = self._drive()
        try:
            metadata = drive.files().get(fileId=drive_file_id, fields='id,name,mimeType,size').execute()
            mime_type = metadata.get('mimeType', mime_hint)
            name = metadata.get('name') or name_hint or 'Classroom material'
            if mime_type.startswith('application/vnd.google-apps.'):
                request = drive.files().export_media(fileId=drive_file_id, mimeType='application/pdf')
                filename = f'{Path(name).stem}.pdf'
                mime_type = 'application/pdf'
            else:
                request = drive.files().get_media(fileId=drive_file_id)
                filename = name if Path(name).suffix else f'{name}.pdf' if mime_type == 'application/pdf' else name
            content = self._read_media(request)
        except HttpError as exc:
            status = getattr(exc.resp, 'status', 500)
            raise ClassroomApiError(status, 'Google Classroom attachment could not be downloaded.') from exc
        if len(content) > MAX_FILE_SIZE:
            raise ClassroomApiError(413, 'Google Classroom attachment is too large.')
        return {'filename': filename, 'content': content, 'mime_type': mime_type, 'size': metadata.get('size')}

    @staticmethod
    def _read_media(request):
        buffer = BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        complete = False
        while not complete:
            _, complete = downloader.next_chunk()
        return buffer.getvalue()
