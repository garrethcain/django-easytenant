SECRET_KEY = "test-secret-key-for-easyshard-not-for-production"

DEBUG = True

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.messages",
    "easyshard",
    "tests.testapp",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "easyshard.middleware.ShardMiddleware",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
    "shard_trial": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
    "shard_enterprise": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

DATABASE_ROUTERS = ["easyshard.routers.ShardRouter"]

EASY_SHARD = {
    "CONFIG_MODE": "local",
    "ID_EXTRACTOR": "easyshard.extractors.JWTShardExtractor",
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
