import os
from .base import *

DEBUG = False
INSTALLED_APPS += ['rest_framework_simplejwt.token_blacklist']
INSTALLED_APPS += ['apps.integrations']
INSTALLED_APPS += ['apps.intelligence']
INSTALLED_APPS += ['apps.ai']
if SECRET_KEY == 'development-only-change-me':
    raise RuntimeError('DJANGO_SECRET_KEY must be set in production')
if not os.getenv('DATABASE_NAME'):
    raise RuntimeError('DATABASE_NAME must be set in production')
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
