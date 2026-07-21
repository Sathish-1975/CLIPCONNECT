"""
============================================================
ClipConnect - Models Package Initialization
============================================================
Registers ALL SQLAlchemy models so db.create_all() creates
every table. Import order matters for FK resolution.
============================================================
"""

# Week 1
from models.user_model import User

# Week 2
from models.editor_profile_model import EditorProfile, EditorCategory, AvailabilityStatus

# Export for easy external access
__all__ = [
    'User',
    'EditorProfile',
    'EditorCategory',
    'AvailabilityStatus',
]
