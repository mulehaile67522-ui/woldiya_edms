from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ──────────────────────────────────────────────────────────
SECRET_KEY  = os.environ.get('SECRET_KEY', 'django-insecure-woldiya-edms-change-in-production')
DEBUG       = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS_ENV = os.environ.get('ALLOWED_HOSTS', '')
ALLOWED_HOSTS = ALLOWED_HOSTS_ENV.split(',') if ALLOWED_HOSTS_ENV else ['*']

# ── Apps ──────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'documents',
]

# ── Middleware ────────────────────────────────────────────────────────
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

ROOT_URLCONF = 'edms_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'documents.context_processors.notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'edms_project.wsgi.application'

# ── Database ──────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=not DEBUG,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME':    BASE_DIR / 'db.sqlite3',
        }
    }

# ── Auth ──────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL           = '/login/'
LOGIN_REDIRECT_URL  = '/'
LOGOUT_REDIRECT_URL = '/login/'

# ── Localisation ──────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Africa/Addis_Ababa'
USE_I18N      = True
USE_TZ        = True

# ── Static & Media ────────────────────────────────────────────────────
STATIC_URL       = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT      = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── File uploads ──────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD          = 'django.db.models.BigAutoField'
DATA_UPLOAD_MAX_MEMORY_SIZE  = 20 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE  = 20 * 1024 * 1024

# ── Messages → Bootstrap tags ─────────────────────────────────────────
from django.contrib.messages import constants as mc
MESSAGE_TAGS = {
    mc.DEBUG:   'secondary',
    mc.INFO:    'info',
    mc.SUCCESS: 'success',
    mc.WARNING: 'warning',
    mc.ERROR:   'danger',
}

# ── CSRF trusted origins (Railway) ───────────────────────────────────
CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',
    'https://*.up.railway.app',
]

# ── Production security ───────────────────────────────────────────────
if not DEBUG:
    SECURE_HSTS_SECONDS            = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_SSL_REDIRECT            = True
    SESSION_COOKIE_SECURE          = True
    CSRF_COOKIE_SECURE             = True
