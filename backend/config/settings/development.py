from .base import *

DEBUG = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = False
INSTALLED_APPS += ['rest_framework_simplejwt.token_blacklist']
INSTALLED_APPS += ['apps.integrations']
INSTALLED_APPS += ['apps.intelligence']
INSTALLED_APPS += ['apps.ai']
CORS_ALLOWED_ORIGINS = list(dict.fromkeys([*CORS_ALLOWED_ORIGINS, 'http://127.0.0.1:5173', 'http://localhost:5173']))
