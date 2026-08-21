from unittest.mock import patch

from django.test import override_settings
from django.test import TestCase
from rest_framework.test import APITestCase

from .models import User
from .services.firebase_auth import FirebaseAuthError


class FirebaseLoginTests(APITestCase):
    def test_valid_token_creates_user_and_returns_rise_jwt(self):
        claims = {'uid': 'firebase-new', 'email': 'firebase@example.com', 'name': 'Firebase Student'}
        with patch('apps.accounts.views.verify_firebase_id_token', return_value=claims):
            response = self.client.post('/api/auth/firebase/', {'id_token': 'firebase-token'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        user = User.objects.get(email='firebase@example.com')
        self.assertEqual(user.firebase_uid, 'firebase-new')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        self.assertEqual(self.client.get('/api/auth/me/').data['email'], 'firebase@example.com')

    def test_invalid_token_is_rejected(self):
        with patch('apps.accounts.views.verify_firebase_id_token', side_effect=FirebaseAuthError):
            response = self.client.post('/api/auth/firebase/', {'id_token': 'invalid'}, format='json')
        self.assertEqual(response.status_code, 401)

    @override_settings(FIREBASE_PROJECT_ID='rise-24726', FIREBASE_SERVICE_ACCOUNT_JSON='')
    @patch('google.oauth2.id_token.verify_firebase_token')
    def test_valid_token_uses_project_verification_without_service_account(self, verify_token):
        verify_token.return_value = {'sub': 'google-sub', 'email': 'google@example.com', 'name': 'Google Student'}
        response = self.client.post('/api/auth/firebase/', {'id_token': 'firebase-token'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.get(email='google@example.com').firebase_uid, 'google-sub')
        verify_token.assert_called_once()

    def test_existing_email_is_linked_without_duplicate_user(self):
        user = User.objects.create_user('existing@example.com', 'Password123!')
        claims = {'uid': 'firebase-existing', 'email': 'existing@example.com', 'name': 'Existing Student'}
        with patch('apps.accounts.views.verify_firebase_id_token', return_value=claims):
            response = self.client.post('/api/auth/firebase/', {'id_token': 'firebase-token'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email='existing@example.com').count(), 1)
        user.refresh_from_db()
        self.assertEqual(user.firebase_uid, 'firebase-existing')

    def test_firebase_uid_email_collision_is_rejected(self):
        User.objects.create_user('one@example.com', 'Password123!', firebase_uid='firebase-shared')
        claims = {'uid': 'firebase-shared', 'email': 'two@example.com', 'name': 'Two'}
        with patch('apps.accounts.views.verify_firebase_id_token', return_value=claims):
            response = self.client.post('/api/auth/firebase/', {'id_token': 'firebase-token'}, format='json')
        self.assertEqual(response.status_code, 409)
