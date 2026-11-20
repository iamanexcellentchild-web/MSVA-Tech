"""
Django settings for the MS. Virtual Academy project.

Secrets and environment-specific values are read from a `.env` file
(see `.env.example`).
"""

import os
import sys
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# `manage.py test` must never touch the live Neon database or Cloudinary, even if .env points at them.
TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"
if TESTING:
    os.environ.pop("DATABASE_URL", None)
    os.environ.pop("CLOUDINARY_URL", None)


def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-dev-only-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
# Render sets this to the service's own address (e.g. msva.onrender.com).
if os.getenv("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(os.getenv("RENDER_EXTERNAL_HOSTNAME"))
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Third party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    *(["cloudinary_storage", "cloudinary"] if os.getenv("CLOUDINARY_URL") else []),
    # Local
    "core",
    "accounts",
]

MIDDLEWARE = [
    "msva.health.HealthCheckMiddleware",  # must stay first
    "msva.health.NoCacheHTMLMiddleware",
    "django.middleware.security.SecurityMiddleware",
    # Serves the collected static files in production (no separate web server needed).
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Authenticates site visitors from the JWT stored in HttpOnly cookies.
    "accounts.middleware.JWTCookieMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "msva.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "msva.wsgi.application"

# SQLite locally; set DATABASE_URL (e.g. a free Neon/Supabase Postgres URL) in production.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    # Uploads go to Cloudinary when CLOUDINARY_URL is set (Render's free disk is wiped on restart).
    "default": {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage" if os.getenv("CLOUDINARY_URL")
                else "django.core.files.storage.FileSystemStorage"},
    # Compressed, cache-busted files in production (needs `collectstatic`); plain files while developing.
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage" if DEBUG
                    else "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"

# --------------------------------------------------------------------------
# Django REST Framework + Simple JWT
# --------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "accounts.authentication.CookieJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_THROTTLE_RATES": {"advisor": "30/min"},
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "15"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# Cookie settings for the JWTs used by the server-rendered pages.
JWT_AUTH_COOKIE = "msva_access"
JWT_REFRESH_COOKIE = "msva_refresh"
JWT_COOKIE_SECURE = env_bool("JWT_COOKIE_SECURE", not DEBUG)
JWT_COOKIE_SAMESITE = "Lax"

# --------------------------------------------------------------------------
# Google OAuth 2.0
# --------------------------------------------------------------------------
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
# Leave blank to derive it from the request (http(s)://<host>/accounts/google/callback/).
GOOGLE_OAUTH_REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "")

# --------------------------------------------------------------------------
# Email (Gmail SMTP - free, ~500 emails/day)
# Requires 2-Step Verification on the Gmail account and an App Password:
# https://myaccount.google.com/apppasswords
# Without EMAIL_HOST_USER/PASSWORD, emails are printed to the console instead.
# --------------------------------------------------------------------------
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "").replace(" ", "")
# Brevo (HTTPS API) is used when BREVO_API_KEY is set: it works on Render's free plan,
# which blocks SMTP. Otherwise Gmail SMTP if configured, else emails print to the console.
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
if BREVO_API_KEY:
    EMAIL_BACKEND = "msva.email_backends.BrevoEmailBackend"
elif EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = True
EMAIL_TIMEOUT = 15
# Send emails in a background thread so visitors never wait on the mail service (off in tests).
EMAIL_ASYNC = env_bool("EMAIL_ASYNC", not TESTING)
# Where contact-form messages are delivered.
CONTACT_INBOX = os.getenv("CONTACT_INBOX", "ms.virtualacademy247@gmail.com")
DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    f"MS. Virtual Academy <{EMAIL_HOST_USER or 'no-reply@msvirtualacademy.com'}>",
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"core": {"handlers": ["console"], "level": "INFO"}},
}

# --------------------------------------------------------------------------
# Site-wide content (used by the `site` context processor)
# --------------------------------------------------------------------------
ACADEMY = {
    "name": "MS. Virtual Academy",
    "apply_url": "https://forms.gle/azDiGAWGsCEDHruN8",
    # Embedded version of the same Google Form, shown on /apply/.
    "apply_form_embed_url": "https://docs.google.com/forms/d/e/1FAIpQLSf_6Q0BIAtUAtGuOIs8ZufMRroPc8RDvTcyNK4Jz0nzWSqFwA/viewform?embedded=true",
    "email": "ms.virtualacademy247@gmail.com",
    "email_display": "info@msvirtualacademy.com",
    "socials": [
        {"label": "Youtube", "icon": "fa-brands fa-youtube",
         "url": "https://youtube.com/@msvirtualacademy247?si=xYjolPlBsMMeFbMT"},
        {"label": "Instagram", "icon": "fa-brands fa-instagram",
         "url": "https://www.instagram.com/ms.virtualacademy?igsh=MXRud3M0Mmg2eXVhcg=="},
        {"label": "LinkedIn", "icon": "fa-brands fa-linkedin-in",
         "url": "https://www.linkedin.com/company/ms-virtual-academy/"},
        {"label": "X (Twitter)", "icon": "fa-brands fa-x-twitter",
         "url": "https://www.x.com/MSVirtualAcad"},
    ],
}

# Forms posted from any allowed domain (custom domain, Netlify address) pass the CSRF origin check.
CSRF_TRUSTED_ORIGINS += [f"https://{h.lstrip('.')}" for h in ALLOWED_HOSTS
                         if h not in ("localhost", "127.0.0.1", "*") and f"https://{h.lstrip('.')}" not in CSRF_TRUSTED_ORIGINS]
CSRF_FAILURE_VIEW = "core.views.csrf_failure"

if not DEBUG:
    if SECRET_KEY.startswith("django-insecure"):
        raise RuntimeError("Set DJANGO_SECRET_KEY before running with DJANGO_DEBUG=False.")
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_HSTS_SECONDS", "3600"))
    SECURE_CONTENT_TYPE_NOSNIFF = True
