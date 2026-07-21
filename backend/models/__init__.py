"""
============================================================
ClipConnect - Models Package Initialization
============================================================
Purpose:
    Imports all SQLAlchemy models so they are registered
    with the database before db.create_all() is called.

Why important?
    SQLAlchemy needs to "see" all model classes before it can
    create the corresponding database tables. By importing them
    all here, we guarantee they are registered.

Usage:
    from models import User
    from models import db  # if needed
============================================================
"""

# Import all models to register them with SQLAlchemy
from models.user_model import User

# Export models for easy access
__all__ = ['User']
