"""
============================================================
ClipConnect - Configuration Module
============================================================
Purpose:
    Centralizes all application configuration settings.
    Reads from environment variables (.env file) for security.
    Provides different configs for Development, Testing, Production.

Usage:
    from config import DevelopmentConfig
    app.config.from_object(DevelopmentConfig)
============================================================
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Base Configuration Class
    ========================
    Contains settings shared across all environments.
    Specific environment classes (Dev, Prod) inherit from this.
    """

    # --- App Identity ---
    APP_NAME = os.environ.get('APP_NAME', 'ClipConnect')
    APP_VERSION = os.environ.get('APP_VERSION', '1.0.0')

    # --- Flask Core Settings ---
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-secret-key-unsafe')
    DEBUG = False
    TESTING = False

    # --- Database Settings ---
    # SQLAlchemy database connection URL
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:password@localhost:5432/clipconnect'
    )

    # Disable modification tracking (saves memory, we don't need this signal)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection pool settings for production stability
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,     # Test connections before use
        'pool_recycle': 300,       # Recycle connections every 5 minutes
        'pool_size': 10,           # Number of connections to maintain
        'max_overflow': 20,        # Extra connections allowed beyond pool_size
    }

    # --- JWT (JSON Web Token) Settings ---
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'fallback-jwt-key-unsafe')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    )  # Default: 1 hour

    # --- CORS Settings ---
    # Origins allowed to call our API (frontend URLs)
    CORS_ORIGINS = os.environ.get(
        'CORS_ORIGINS',
        'http://localhost:5500,http://127.0.0.1:5500'
    ).split(',')

    # --- File Upload Settings (for profile images) ---
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')

    # --- JSON Settings ---
    JSON_SORT_KEYS = False         # Preserve key order in JSON responses
    JSONIFY_PRETTYPRINT_REGULAR = True  # Pretty-print JSON in development


class DevelopmentConfig(Config):
    """
    Development Configuration
    =========================
    Used during local development.
    Enables debug mode for hot-reloading and detailed error messages.
    """
    DEBUG = True
    TESTING = False

    # More verbose SQL logging in development
    SQLALCHEMY_ECHO = True  # Prints all SQL queries to console


class TestingConfig(Config):
    """
    Testing Configuration
    =====================
    Used during automated tests (pytest).
    Uses an in-memory SQLite DB so tests don't touch the real database.
    """
    DEBUG = True
    TESTING = True

    # Use SQLite in memory for tests (no PostgreSQL required for tests)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ECHO = False

    # Override JWT expiry for faster test execution
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)

    # Disable CSRF protection in tests
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """
    Production Configuration
    ========================
    Used in the live/deployed environment.
    Debug mode OFF. Uses strict security settings.
    """
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False  # Don't log SQL in production (performance)

    # Override with stricter settings in production
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)


# --- Configuration Selector ---
# Maps string names to config classes
# Used in app.py: app.config.from_object(config_map[env])
config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    """
    Returns the appropriate config class based on FLASK_ENV environment variable.
    Defaults to DevelopmentConfig if FLASK_ENV is not set.
    
    Returns:
        Config class (not instance)
    """
    env = os.environ.get('FLASK_ENV', 'development')
    return config_map.get(env, DevelopmentConfig)
