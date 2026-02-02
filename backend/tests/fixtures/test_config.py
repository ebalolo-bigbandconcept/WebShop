"""Test configuration for WebShop backend."""

import tempfile

from dotenv import load_dotenv

load_dotenv()


class TestConfig:
    """Configuration for running tests."""

    # Use in-memory SQLite for fast tests
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Testing mode
    TESTING = True

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
