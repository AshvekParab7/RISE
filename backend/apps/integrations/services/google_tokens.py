from datetime import timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from ..models import GoogleConnection

class GoogleAuthenticationRequired(Exception):
    pass

def credentials_for(connection: GoogleConnection):
    if not connection.is_active:
        raise GoogleAuthenticationRequired('Google authorization is required.')
    expiry = connection.token_expiry
    if expiry and expiry.tzinfo:
        expiry = expiry.astimezone(timezone.utc).replace(tzinfo=None)
    credentials = Credentials(token=connection.get_access_token(), refresh_token=connection.get_refresh_token(), token_uri='https://oauth2.googleapis.com/token', client_id=__import__('django.conf', fromlist=['settings']).settings.GOOGLE_CLIENT_ID, client_secret=__import__('django.conf', fromlist=['settings']).settings.GOOGLE_CLIENT_SECRET, scopes=connection.scopes, expiry=expiry)
    if credentials.expired or not credentials.valid:
        if not credentials.refresh_token:
            connection.is_active = False
            connection.save(update_fields=['is_active', 'updated_at'])
            raise GoogleAuthenticationRequired('Google authorization is required.')
        try:
            credentials.refresh(Request())
        except Exception as exc:
            connection.is_active = False
            connection.save(update_fields=['is_active', 'updated_at'])
            raise GoogleAuthenticationRequired('Google authorization is required.') from exc
        connection.set_tokens(credentials.token, credentials.refresh_token)
        connection.token_expiry = credentials.expiry
        connection.scopes = sorted(credentials.scopes or connection.scopes)
        connection.save(update_fields=['access_token_encrypted', 'refresh_token_encrypted', 'token_expiry', 'scopes', 'updated_at'])
    return credentials
