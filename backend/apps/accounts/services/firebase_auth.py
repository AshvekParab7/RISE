import json
import os
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class FirebaseAuthError(Exception):
    pass


@lru_cache(maxsize=1)
def _firebase_app():
    import firebase_admin
    from firebase_admin import credentials

    if firebase_admin._apps:
        return firebase_admin.get_app()
    if settings.FIREBASE_SERVICE_ACCOUNT_JSON:
        credential_path = Path(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
        if not credential_path.is_absolute():
            credential_path = Path(settings.BASE_DIR) / credential_path
        credential = credentials.Certificate(str(credential_path.resolve()))
    elif settings.FIREBASE_PROJECT_ID and settings.FIREBASE_CLIENT_EMAIL and settings.FIREBASE_PRIVATE_KEY:
        credential = credentials.Certificate({
            'type': 'service_account',
            'project_id': settings.FIREBASE_PROJECT_ID,
            'private_key': settings.FIREBASE_PRIVATE_KEY,
            'client_email': settings.FIREBASE_CLIENT_EMAIL,
            'token_uri': 'https://oauth2.googleapis.com/token',
        })
    else:
        raise ImproperlyConfigured('Firebase Admin is not configured.')
    return firebase_admin.initialize_app(credential, {'projectId': settings.FIREBASE_PROJECT_ID} if settings.FIREBASE_PROJECT_ID else None)


def verify_firebase_id_token(token):
    try:
        from firebase_admin import auth
        _firebase_app()
        return auth.verify_id_token(token, check_revoked=True)
    except Exception as exc:
        raise FirebaseAuthError from exc
