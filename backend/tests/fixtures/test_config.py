"""Test configuration for WebShop backend."""

import os
import tempfile

from dotenv import load_dotenv
from sqlalchemy.pool import StaticPool

load_dotenv()


class TestConfig:
    """Configuration for running tests."""

    # Use a single in-memory SQLite connection shared by the test process.
    # This avoids filesystem-level lock contention during high-volume fixtures.
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": StaticPool,
        "connect_args": {
            "check_same_thread": False,
        }
    }

    # Testing mode
    TESTING = True

    # Faster password hashing for tests.
    BCRYPT_LOG_ROUNDS = 4

    # Disable CSRF for easier testing (we'll test CSRF separately)
    WTF_CSRF_ENABLED = False

    # Secret key for sessions
    SECRET_KEY = "test-secret-key-for-testing-only"

    # Server-side session config (use simple dict for tests)
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_FILE_DIR = tempfile.mkdtemp()

    # Disable rate limiting in tests (we'll test it separately)
    RATELIMIT_ENABLED = False

    # Cookie settings
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Disable background tasks
    PRESERVE_CONTEXT_ON_EXCEPTION = False
