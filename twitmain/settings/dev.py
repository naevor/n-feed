import os

from . import base
from .base import *  # noqa: F403

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "unsafe-dev-secret-key-for-local-development-only-change-me"
)
DEBUG = base.env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = base.env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

DATABASES = base.build_database_config(default_engine="sqlite", postgres_host="localhost")
CACHES = base.build_cache_config(default_redis_url="")

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
