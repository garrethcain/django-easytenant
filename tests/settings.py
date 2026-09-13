SECRET_KEY = "test-secret-key-for-easytenant-not-for-production"

DEBUG = True

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.messages",
    "easytenant",
    "tests.testapp",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "easytenant.middleware.TenantMiddleware",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
    "tenant_trial": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
    "tenant_enterprise": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

DATABASE_ROUTERS = ["easytenant.routers.TenantRouter"]

EASY_TENANT = {
    "CONFIG_MODE": "local",
    "ID_EXTRACTOR": "easytenant.extractors.JWTTenantExtractor",
    "ENCRYPTION_KEY": None,
}

ROOT_URLCONF = "tests.urls"

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
