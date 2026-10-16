"""
Django settings.

All configurable values come from `app.core.config.settings` (pydantic-settings,
reads the top level `.env`). Keep this module free of `os.environ` lookups so
there is a single, validated source of configuration.
"""

from pathlib import Path

import django_stubs_ext
import sentry_sdk

from app.core.config import settings

# Allow generic type hints such as `admin.ModelAdmin[Item]` at runtime
django_stubs_ext.monkeypatch()

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent

SECRET_KEY = settings.SECRET_KEY
DEBUG = settings.is_development
ALLOWED_HOSTS = ["*"]  # nginx routes by server_name in front of the app

INSTALLED_APPS = [
    # Unfold must come before django.contrib.admin to override its templates
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "ninja",
    "app.users",
    "app.items",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "app.urls"
WSGI_APPLICATION = "app.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Database

_db_host = settings.DATABASE_URL.hosts()[0]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": (settings.DATABASE_URL.path or "/app").lstrip("/"),
        "USER": _db_host["username"] or "",
        "PASSWORD": _db_host["password"] or "",
        "HOST": _db_host["host"] or "",
        "PORT": str(_db_host["port"] or 5432),
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Auth

AUTH_USER_MODEL = "users.User"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
# Password reset links (single use, see app.users.tokens)
PASSWORD_RESET_TIMEOUT = settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS * 60 * 60

# Internationalization

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# URLs: API paths are declared exactly (mixed trailing slashes, same as the
# original FastAPI template), so never redirect to add a slash.
APPEND_SLASH = False

# Static and media files: Django never serves them in deployments. With object
# storage configured they live in the bucket (behind a CDN via
# AWS_S3_CUSTOM_DOMAIN); `collectstatic` uploads the admin assets there.
# Without it they stay on the local disk, which `runserver` serves in DEBUG.

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

if settings.object_storage_enabled:
    _s3_options = {
        "bucket_name": settings.AWS_STORAGE_BUCKET_NAME,
        "access_key": settings.AWS_ACCESS_KEY_ID,
        "secret_key": settings.AWS_SECRET_ACCESS_KEY,
        "region_name": settings.AWS_S3_REGION_NAME,
        "endpoint_url": settings.AWS_S3_ENDPOINT_URL,
        "custom_domain": settings.AWS_S3_CUSTOM_DOMAIN,
    }
    STORAGES = {
        # User uploads: private by default, URLs are signed unless served
        # through AWS_S3_CUSTOM_DOMAIN
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {**_s3_options, "location": "media", "file_overwrite": False},
        },
        # Admin assets: public, plain URLs so the CDN can cache them
        "staticfiles": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                **_s3_options,
                "location": "static",
                "querystring_auth": False,
            },
        },
    }
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

# Admin theme (django-unfold): https://unfoldadmin.com/docs/configuration/settings/

UNFOLD = {
    "SITE_TITLE": settings.PROJECT_NAME,
    "SITE_HEADER": settings.PROJECT_NAME,
}

# Behind the reverse proxy (TLS terminated there): trust its X-Forwarded-Proto,
# so request.is_secure() and the admin's CSRF origin check see https. The proxy
# must always set this header (nginx/host-site.conf.template does, and the
# project gateway nginx/gateway.conf passes it on).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = [settings.FRONTEND_HOST]

# CORS: only needed when the frontend runs on another origin than the API.
# On the single-domain setup (proxy routes /api to Django) it is unused.

CORS_ALLOWED_ORIGINS = [settings.FRONTEND_HOST]
CORS_ALLOW_CREDENTIALS = True

# Email (Django 6.1+ MAILERS setting)

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {
            "host": settings.SMTP_HOST or "localhost",
            "port": settings.SMTP_PORT,
            "username": settings.SMTP_USER or "",
            "password": settings.SMTP_PASSWORD or "",
            "use_tls": settings.SMTP_TLS,
            "use_ssl": settings.SMTP_SSL and not settings.SMTP_TLS,
        },
    }
}
DEFAULT_FROM_EMAIL = (
    f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
    if settings.EMAILS_FROM_EMAIL
    else "webmaster@localhost"
)

# Logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

# Sentry

if settings.SENTRY_DSN and not settings.is_development:
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)
