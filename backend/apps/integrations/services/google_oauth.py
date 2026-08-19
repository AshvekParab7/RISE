import secrets
import logging
from datetime import datetime, timezone
from hmac import compare_digest
from urllib.parse import urlencode
import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseBadRequest
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from apps.accounts.models import User
from ..models import GoogleConnection

logger = logging.getLogger(__name__)

AUTH_ENDPOINT = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_ENDPOINT = 'https://oauth2.googleapis.com/token'
CLASSROOM_SCOPES = ('https://www.googleapis.com/auth/classroom.courses.readonly', 'https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly')
CALENDAR_SCOPES = ('https://www.googleapis.com/auth/calendar.readonly',)


def _configured():
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise ImproperlyConfigured('Google OAuth credentials are not configured.')


def client_config():
    _configured()
    return {'web': {'client_id': settings.GOOGLE_CLIENT_ID, 'client_secret': settings.GOOGLE_CLIENT_SECRET, 'auth_uri': AUTH_ENDPOINT, 'token_uri': TOKEN_ENDPOINT, 'redirect_uris': [settings.GOOGLE_REDIRECT_URI]}}


def build_flow(state=None, scopes=None):
    flow = Flow.from_client_config(client_config(), scopes=scopes or settings.GOOGLE_OAUTH_SCOPES, state=state)
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    return flow


def authorization_url(request, additional_scopes=()):
    state = secrets.token_urlsafe(32)
    scopes = sorted(set(settings.GOOGLE_OAUTH_SCOPES).union(additional_scopes))
    request.session['google_oauth_state'] = state
    request.session['google_oauth_user_id'] = str(request.user.id) if request.user.is_authenticated else ''
    request.session['google_oauth_scopes'] = scopes
    flow = build_flow(state, scopes=scopes)
    url, _ = flow.authorization_url(access_type='offline', include_granted_scopes='true', prompt='consent')
    request.session['google_oauth_code_verifier'] = getattr(flow, 'code_verifier', '')
    request.session.save()
    logger.warning('Google OAuth state generated: state_present=%s state_length=%s session_key_present=%s', bool(state), len(state), bool(request.session.session_key))
    return url


def exchange_callback(request):
    expected = request.session.get('google_oauth_state')
    received = request.GET.get('state')
    matches = bool(expected and received and compare_digest(expected, received))
    logger.warning('Google OAuth callback input: code_present=%s state_present=%s state_valid=%s session_key_present=%s', bool(request.GET.get('code')), bool(received), matches, bool(request.session.session_key))
    user_id = request.session.pop('google_oauth_user_id', None)
    code_verifier = request.session.pop('google_oauth_code_verifier', None)
    request.session.pop('google_oauth_state', None)
    if not matches:
        return HttpResponseBadRequest('Invalid OAuth state.')
    if request.GET.get('error'):
        return HttpResponseBadRequest('Google authorization was not completed.')
    code = request.GET.get('code')
    if not code:
        return HttpResponseBadRequest('Missing Google authorization code.')
    try:
        flow = build_flow(state=expected, scopes=request.session.pop('google_oauth_scopes', settings.GOOGLE_OAUTH_SCOPES))
        if code_verifier:
            flow.code_verifier = code_verifier
        flow.fetch_token(code=code)
        logger.warning('Google OAuth callback token_exchange=success code_verifier_present=%s', bool(code_verifier))
    except Exception as exc:
        safe_message = str(exc).replace(settings.GOOGLE_CLIENT_ID, '[client_id]').replace(settings.GOOGLE_CLIENT_SECRET, '[client_secret]')[:240]
        response = getattr(exc, 'response', None)
        response_status = getattr(response, 'status_code', None)
        logger.warning('Google OAuth callback token exchange failed: error_type=%s message=%s http_status=%s code_verifier_present=%s', type(exc).__name__, safe_message, response_status, bool(code_verifier))
        return HttpResponseBadRequest('Google authorization could not be completed.')
    try:
        credentials = flow.credentials
        claims = id_token.verify_oauth2_token(credentials.id_token, Request(), settings.GOOGLE_CLIENT_ID)
        logger.warning('Google OAuth callback id_token_validation=success')
    except Exception as exc:
        logger.warning('Google OAuth callback identity validation failed: error_type=%s', type(exc).__name__)
        return HttpResponseBadRequest('Google authorization could not be completed.')
    if claims.get('iss') not in ('accounts.google.com', 'https://accounts.google.com') or not claims.get('sub') or not claims.get('email') or claims.get('email_verified') is False:
        return HttpResponseBadRequest('Invalid Google identity.')
    connection = GoogleConnection.objects.filter(google_user_id=claims['sub']).select_related('user').first()
    initiating_user = User.objects.filter(id=user_id).first() if user_id else None
    if initiating_user and connection and connection.user_id != initiating_user.id:
        return HttpResponseBadRequest('Google identity is already linked to another account.')
    user = initiating_user or (connection.user if connection else User.objects.filter(email__iexact=claims['email']).first())
    if not user:
        user = User.objects.create_user(email=claims['email'], first_name=claims.get('given_name', ''), last_name=claims.get('family_name', ''))
    logger.warning('Google OAuth callback user_creation=success existing_user=%s', bool(user.pk))
    connection, _ = GoogleConnection.objects.update_or_create(user=user, defaults={'google_user_id': claims['sub'], 'email': claims['email'], 'display_name': claims.get('name', ''), 'picture': claims.get('picture', ''), 'token_expiry': credentials.expiry, 'scopes': sorted(credentials.scopes or settings.GOOGLE_OAUTH_SCOPES), 'is_active': True})
    connection.set_tokens(credentials.token, credentials.refresh_token)
    connection.save(update_fields=['google_user_id', 'email', 'display_name', 'picture', 'token_expiry', 'scopes', 'access_token_encrypted', 'refresh_token_encrypted', 'is_active', 'updated_at'])
    return connection


def revoke(connection):
    token = connection.get_refresh_token() or connection.get_access_token()
    if token:
        try:
            requests.post('https://oauth2.googleapis.com/revoke', params={'token': token}, timeout=5)
        except requests.RequestException:
            pass
    connection.clear_credentials()
    connection.save(update_fields=['access_token_encrypted', 'refresh_token_encrypted', 'is_active', 'updated_at'])
