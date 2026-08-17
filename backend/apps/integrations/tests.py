from datetime import datetime, timezone
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse
from django.test import override_settings
from rest_framework.test import APITestCase
from apps.accounts.models import User
from .models import GoogleConnection

class GoogleOAuthTests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user('google-a@example.com', 'Password123!')
        self.user_b = User.objects.create_user('google-b@example.com', 'Password123!')
        self.client.force_authenticate(self.user_a)

    def test_status_is_safe_and_isolated(self):
        connection = GoogleConnection.objects.create(user=self.user_a, google_user_id='google-a', email='a@gmail.com', display_name='A', scopes=['openid'])
        connection.set_tokens('access-secret', 'refresh-secret'); connection.save()
        response = self.client.get('/api/integrations/google/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['connected'])
        self.assertNotIn('access_token', response.data)
        self.assertNotIn('refresh_token', response.data)
        self.client.force_authenticate(self.user_b)
        self.assertFalse(self.client.get('/api/integrations/google/').data['connected'])

    @override_settings(GOOGLE_CLIENT_ID='client-id', GOOGLE_CLIENT_SECRET='client-secret')
    @patch('apps.integrations.services.google_oauth.build_flow')
    def test_unauthenticated_basic_start_is_allowed(self, build_flow):
        self.client.force_authenticate(None)
        flow = Mock(); flow.code_verifier = 'test-verifier'; flow.authorization_url.return_value = ('https://accounts.google.com/o/oauth2/v2/auth?state=test', None); build_flow.return_value = flow
        response = self.client.get('/api/integrations/google/start/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.client.session.get('google_oauth_state'))

    def test_unauthenticated_incremental_start_is_rejected(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/integrations/google/start/?integration=classroom').status_code, 401)

    @override_settings(GOOGLE_CLIENT_ID='client-id', GOOGLE_CLIENT_SECRET='client-secret')
    @patch('apps.integrations.services.google_oauth.build_flow')
    def test_start_generates_state_and_url(self, build_flow):
        flow = Mock(); flow.code_verifier = 'test-verifier'; flow.authorization_url.return_value = ('https://accounts.google.com/o/oauth2/v2/auth?state=test', None); build_flow.return_value = flow
        response = self.client.get('/api/integrations/google/start/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.client.session.get('google_oauth_state'))
        self.assertEqual(response.data['authorization_url'], 'https://accounts.google.com/o/oauth2/v2/auth?state=test')

    def test_invalid_state_and_missing_code_are_rejected(self):
        session = self.client.session
        session['google_oauth_state'] = 'expected'
        session['google_oauth_user_id'] = str(self.user_a.id)
        session.save()
        self.assertEqual(self.client.get('/api/integrations/google/callback/?state=wrong&code=abc').status_code, 400)
        session = self.client.session
        session['google_oauth_state'] = 'expected'
        session['google_oauth_user_id'] = str(self.user_a.id)
        session.save()
        self.assertEqual(self.client.get('/api/integrations/google/callback/?state=expected').status_code, 400)

    @override_settings(GOOGLE_CLIENT_ID='client-id', GOOGLE_CLIENT_SECRET='client-secret', GOOGLE_SUCCESS_REDIRECT_URI='http://localhost:5173/')
    @patch('apps.integrations.services.google_oauth.id_token.verify_oauth2_token')
    @patch('apps.integrations.services.google_oauth.build_flow')
    def test_basic_google_login_creates_user_and_rise_jwt(self, build_flow, verify_token):
        flow = Mock(); flow.credentials.token = 'google-access'; flow.credentials.refresh_token = 'google-refresh'; flow.credentials.expiry = datetime.now(timezone.utc); flow.credentials.scopes = ['openid', 'email']; flow.credentials.id_token = 'id-token'; build_flow.return_value = flow
        verify_token.return_value = {'iss': 'https://accounts.google.com', 'sub': 'google-new', 'email': 'new@gmail.com', 'email_verified': True, 'given_name': 'New', 'family_name': 'Student', 'name': 'New Student', 'picture': ''}
        self.client.force_authenticate(None)
        session = self.client.session; session['google_oauth_state'] = 'login-state'; session['google_oauth_user_id'] = ''; session['google_oauth_scopes'] = ['openid', 'profile', 'email']; session.save()
        response = self.client.get('/api/integrations/google/callback/?state=login-state&code=abc')
        self.assertEqual(response.status_code, 302)
        fragment = parse_qs(urlparse(response['Location']).fragment)
        self.assertIn('rise_access', fragment)
        self.assertNotIn('google-access', response['Location'])
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {fragment['rise_access'][0]}")
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 200)
        user = User.objects.get(email='new@gmail.com')
        self.assertEqual(GoogleConnection.objects.get(google_user_id='google-new').user_id, user.id)

    @override_settings(GOOGLE_CLIENT_ID='client-id', GOOGLE_CLIENT_SECRET='client-secret')
    @patch('apps.integrations.services.google_oauth.id_token.verify_oauth2_token')
    @patch('apps.integrations.services.google_oauth.build_flow')
    def test_repeated_basic_google_login_reuses_user(self, build_flow, verify_token):
        flow = Mock(); flow.credentials.token = 'google-access'; flow.credentials.refresh_token = 'google-refresh'; flow.credentials.expiry = datetime.now(timezone.utc); flow.credentials.scopes = ['openid', 'email']; flow.credentials.id_token = 'id-token'; build_flow.return_value = flow
        verify_token.return_value = {'iss': 'https://accounts.google.com', 'sub': 'google-repeat', 'email': 'repeat@gmail.com', 'email_verified': True, 'name': 'Repeat Student'}
        self.client.force_authenticate(None)
        for state in ('first-state', 'second-state'):
            session = self.client.session; session['google_oauth_state'] = state; session['google_oauth_user_id'] = ''; session['google_oauth_scopes'] = ['openid', 'profile', 'email']; session.save()
            response = self.client.get(f'/api/integrations/google/callback/?state={state}&code=abc')
            self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.filter(email='repeat@gmail.com').count(), 1)
        self.assertEqual(GoogleConnection.objects.filter(google_user_id='google-repeat').count(), 1)

    def test_google_denial_is_handled_without_provider_error(self):
        session = self.client.session; session['google_oauth_state'] = 'denied-state'; session['google_oauth_user_id'] = ''; session.save()
        response = self.client.get('/api/integrations/google/callback/?state=denied-state&error=access_denied')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'Google authorization was not completed.')

    @override_settings(GOOGLE_CLIENT_ID='client-id', GOOGLE_CLIENT_SECRET='client-secret', GOOGLE_SUCCESS_REDIRECT_URI='http://localhost:5173/integrations')
    @patch('apps.integrations.services.google_oauth.id_token.verify_oauth2_token')
    @patch('apps.integrations.services.google_oauth.build_flow')
    def test_callback_stores_tokens_without_serializing_them(self, build_flow, verify_token):
        flow = Mock(); flow.credentials.token = 'access-secret'; flow.credentials.refresh_token = 'refresh-secret'; flow.credentials.expiry = datetime.now(timezone.utc); flow.credentials.scopes = ['openid', 'email']; flow.credentials.id_token = 'id-token'; build_flow.return_value = flow
        verify_token.return_value = {'iss': 'https://accounts.google.com', 'sub': 'google-a', 'email': 'a@gmail.com', 'name': 'A', 'picture': ''}
        session = self.client.session; session['google_oauth_state'] = 'expected'; session['google_oauth_user_id'] = str(self.user_a.id); session.save()
        response = self.client.get('/api/integrations/google/callback/?state=expected&code=abc')
        self.assertEqual(response.status_code, 302)
        connection = GoogleConnection.objects.get(user=self.user_a)
        self.assertEqual(connection.get_refresh_token(), 'refresh-secret')
        self.assertNotIn('access_token', response.headers)
        self.assertIn('rise_access=', response['Location'])

    @patch('apps.integrations.services.google_oauth.requests.post')
    def test_disconnect_clears_credentials(self, revoke_post):
        connection = GoogleConnection.objects.create(user=self.user_a, google_user_id='google-a', email='a@gmail.com')
        connection.set_tokens('access-secret', 'refresh-secret'); connection.save()
        response = self.client.delete('/api/integrations/google/')
        self.assertEqual(response.status_code, 204)
        connection.refresh_from_db()
        self.assertFalse(connection.is_active)
        self.assertEqual(connection.access_token_encrypted, '')
        self.assertEqual(connection.refresh_token_encrypted, '')

from .classroom_tests import *
from .calendar_tests import *
