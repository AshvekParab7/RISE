import base64
import hashlib
import uuid
from django.conf import settings
from django.db import models
from cryptography.fernet import Fernet


def _fernet():
    configured = settings.GOOGLE_TOKEN_ENCRYPTION_KEY.encode()
    key = configured if configured else base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
    return Fernet(key)


def encrypt_token(value):
    return _fernet().encrypt(value.encode()).decode() if value else ''


def decrypt_token(value):
    return _fernet().decrypt(value.encode()).decode() if value else ''


class GoogleConnection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='google_connection')
    google_user_id = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    display_name = models.CharField(max_length=255, blank=True)
    picture = models.URLField(blank=True)
    access_token_encrypted = models.TextField(blank=True)
    refresh_token_encrypted = models.TextField(blank=True)
    token_expiry = models.DateTimeField(null=True, blank=True)
    scopes = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('-updated_at',)

    def set_tokens(self, access_token='', refresh_token=''):
        if access_token:
            self.access_token_encrypted = encrypt_token(access_token)
        if refresh_token:
            self.refresh_token_encrypted = encrypt_token(refresh_token)

    def get_access_token(self):
        return decrypt_token(self.access_token_encrypted)

    def get_refresh_token(self):
        return decrypt_token(self.refresh_token_encrypted)

    def clear_credentials(self):
        self.access_token_encrypted = ''
        self.refresh_token_encrypted = ''
        self.is_active = False

    def __str__(self):
        return f'{self.user.email} · {self.email or self.google_user_id}'

from .models_classroom import GoogleCourse, GoogleCoursework, GoogleMaterial, GoogleSubmission
from .models_calendar import GoogleCalendar, GoogleCalendarEvent
