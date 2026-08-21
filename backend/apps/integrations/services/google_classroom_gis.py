from datetime import timedelta
import logging

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

from ..models import GoogleConnection

logger = logging.getLogger(__name__)

CLASSROOM_GIS_SCOPES = (
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
)


class ClassroomTokenError(Exception):
    def __init__(self, message, missing_scopes=()):
        self.missing_scopes = list(missing_scopes)
        super().__init__(message)


def validate_classroom_access_token(access_token):
    if not access_token:
        raise ClassroomTokenError('A Google Classroom access token is required.')
    try:
        response = requests.get(
            'https://oauth2.googleapis.com/tokeninfo',
            params={'access_token': access_token},
            timeout=10,
        )
    except requests.RequestException as exc:
        raise ClassroomTokenError('Google token validation is unavailable.') from exc
    if response.status_code != 200:
        logger.warning('GIS Classroom token validation: requested_scopes=%s granted_scopes=[] missing_scopes=%s token_valid=False audience_valid=False failure_stage=TOKENINFO', list(CLASSROOM_GIS_SCOPES), list(CLASSROOM_GIS_SCOPES))
        raise ClassroomTokenError('Google Classroom authorization is invalid or expired.')
    try:
        claims = response.json()
    except ValueError as exc:
        raise ClassroomTokenError('Google token validation returned an invalid response.') from exc
    audience_valid = claims.get('aud') == settings.GOOGLE_CLIENT_ID
    scopes = set((claims.get('scope') or '').split())
    missing_scopes = sorted(set(CLASSROOM_GIS_SCOPES) - scopes)
    logger.warning('GIS Classroom token validation: requested_scopes=%s granted_scopes=%s missing_scopes=%s token_valid=True audience_valid=%s failure_stage=%s', list(CLASSROOM_GIS_SCOPES), sorted(scopes), missing_scopes, audience_valid, 'AUDIENCE' if not audience_valid else 'SCOPE' if missing_scopes else 'NONE')
    if not audience_valid:
        raise ClassroomTokenError('Google Classroom authorization belongs to a different client.')
    if missing_scopes:
        raise ClassroomTokenError('Google Classroom permission is incomplete.', missing_scopes)
    try:
        expires_at = timezone.now() + timedelta(seconds=int(claims.get('expires_in', 0)))
    except (TypeError, ValueError):
        raise ClassroomTokenError('Google Classroom authorization has no valid expiry.')
    return {'google_user_id': claims.get('user_id', ''), 'email': claims.get('email', ''), 'scopes': sorted(scopes), 'expires_at': expires_at}


def authorize_classroom_connection(user, access_token):
    validated = validate_classroom_access_token(access_token)
    if validated['google_user_id']:
        existing = GoogleConnection.objects.filter(google_user_id=validated['google_user_id']).exclude(user=user).first()
        if existing:
            raise ClassroomTokenError('This Google Classroom account is linked to another RISE user.')
    connection, _ = GoogleConnection.objects.get_or_create(user=user, defaults={'google_user_id': ''})
    if validated['google_user_id']:
        connection.google_user_id = validated['google_user_id']
    if validated['email']:
        connection.email = validated['email']
    connection.scopes = validated['scopes']
    connection.token_expiry = validated['expires_at']
    connection.is_active = True
    connection.set_tokens(access_token, '')
    connection.save(update_fields=('google_user_id', 'email', 'scopes', 'token_expiry', 'is_active', 'access_token_encrypted', 'updated_at'))
    return connection
