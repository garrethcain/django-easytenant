"""Settings for the django-easytenant monolith example.

This example demonstrates a single Django deployment with:
  - A 'default' database for TenantConfig and auth tables.
  - Two tenant databases ('tenant_trial', 'tenant_enterprise').
  - A custom User model using TenantUserMixin.
  - JWT-based tenant extraction via django-easyjwt.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "example-only-not-for-production"
DEBUG = True
ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "easytenant",
    "blog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "easytenant.middleware.TenantMiddleware",
]

ROOT_URLCONF = "example_project.urls"

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

WSGI_APPLICATION = "example_project.wsgi.application"

# --- Database configuration ------------------------------------------------
# In production these would be separate PostgreSQL instances.
# For the example we use SQLite to keep it self-contained.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db_default.sqlite3",
    },
    "tenant_trial": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db_trial.sqlite3",
    },
    "tenant_enterprise": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db_enterprise.sqlite3",
    },
}

DATABASE_ROUTERS = ["easytenant.routers.TenantRouter"]

# --- easytenant configuration ------------------------------------------------

EASY_TENANT = {
    # Extract tenant_id from JWT tokens (default).
    # If using django-easyjwt, the claim name matches.
    "ID_EXTRACTOR": "easytenant.extractors.JWTTenantExtractor",
    "ID_JWT_CLAIM": "tenant_id",
    "CONFIG_MODE": "local",
    # Fernet key for encrypting passwords in TenantConfig.
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    "ENCRYPTION_KEY": os.environ.get(
        "EASYTENANT_ENCRYPTION_KEY",
        "Y2hhbmdlLW1lLXByb2R1Y3Rpb24ta2V5LTMyLWJ5dGVzIQ==",
    ),
    # Secret for the /tenants/reload/ HTTP endpoint.
    "RELOAD_SECRET": "example-reload-secret",
    # JWT verification defaults to HS256 with SECRET_KEY (same as django-easyjwt).
    # Override only if you've customized these in your JWT configuration.
}

# --- Django auth ------------------------------------------------------------

AUTH_USER_MODEL = "blog.User"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
