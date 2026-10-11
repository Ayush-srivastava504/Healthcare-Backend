# Test-only settings: swaps PostgreSQL for in-memory SQLite and relaxes the
# throttle so the suite can run without any external services.
from .settings import *  # noqa: F401,F403

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
REST_FRAMEWORK = {**REST_FRAMEWORK, "DEFAULT_THROTTLE_RATES": {"auth": "1000/min"}}
LOGGING["root"]["level"] = "CRITICAL"
LOGGING["loggers"] = {"django.request": {"level": "CRITICAL"}}
