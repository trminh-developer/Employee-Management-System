"""
Django settings for TMNexora (Employee Management System).
Standardized for Local Development, Docker Containerization and Kubernetes.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file (if present)
load_dotenv(BASE_DIR / '.env')

# ==============================================================================
# CORE SECURITY & APPLICATION SETTINGS
# ==============================================================================
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    os.environ.get('SECRET_KEY', 'django-insecure-5jawlekwb9kjzye!%k$%_1lnj#m!4p^f*%)&1(en#ug3wvk#9+')
)

DEBUG = os.environ.get('DJANGO_DEBUG', os.environ.get('DEBUG', 'True')).lower() in ('true', '1', 'yes')

_allowed_hosts_str = os.environ.get('DJANGO_ALLOWED_HOSTS', os.environ.get('ALLOWED_HOSTS', ''))
if _allowed_hosts_str:
    ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts_str.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['*'] if DEBUG else ['localhost', '127.0.0.1', 'testserver']

_csrf_origins_str = os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', os.environ.get('CSRF_TRUSTED_ORIGINS', ''))
if _csrf_origins_str:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins_str.split(',') if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = []


# ==============================================================================
# APPLICATION DEFINITION
# ==============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # TMNexora Local Apps
    'apps.accounts',
    'apps.employees',
    'apps.departments',
    'apps.attendance',
    'apps.leave',
    'apps.payroll',
    'apps.performance',
    'apps.reports',
    'apps.notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'frontend' / 'templates',
            BASE_DIR / 'frontend',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ==============================================================================
# DATABASE CONFIGURATION
# ==============================================================================
_db_engine = os.environ.get('DB_ENGINE', 'django.db.backends.mysql')

if 'sqlite' in _db_engine:
    _sqlite_name = os.environ.get('DB_NAME', 'db.sqlite3')
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:' if _sqlite_name == ':memory:' else BASE_DIR / _sqlite_name,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': _db_engine,
            'NAME': os.environ.get('DB_NAME', 'ems'),
            'USER': os.environ.get('DB_USER', 'root'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
            'PORT': os.environ.get('DB_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
            }
        }
    }

AUTH_PASSWORD_VALIDATORS = []


# ==============================================================================
# INTERNATIONALIZATION
# ==============================================================================
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True


# ==============================================================================
# STATIC & MEDIA FILES
# ==============================================================================
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'frontend' / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise storage (Django 5.x STORAGES format): compresses files and adds cache-busting hashes
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}
WHITENOISE_MANIFEST_STRICT = False

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

AUTH_USER_MODEL = 'accounts.User'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'

X_FRAME_OPTIONS = 'SAMEORIGIN'

# N8N Automation Webhook
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL', 'http://localhost:5678/webhook/send-notification')

# Optional local settings override
try:
    from .local_settings import *
except ImportError:
    pass


# ==============================================================================
# LOGGING CONFIGURATION (CONTAINER-COMPLIANT STDOUT / STDERR)
# ==============================================================================
_log_level = os.environ.get('DJANGO_LOG_LEVEL', 'DEBUG' if DEBUG else 'INFO')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'level': _log_level,
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': _log_level,
            'propagate': False,
        },
    },
}
