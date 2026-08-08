"""
============================================================
ClipConnect - User Settings Model
============================================================
Why this file exists:
  Defines the database schema for user preferences including UI theme,
  language, privacy visibility, and notification settings.

What it does:
  - Stores dark/light theme mode preference (`theme`).
  - Stores user language setting (`language`).
  - Stores email notification, project alert, and marketing preferences.
  - Stores privacy preferences (`is_profile_public`).

How it integrates with the rest of the application:
  - Registered in `models/__init__.py` for DB table initialization.
  - Consumed by `user_controller.py` and user settings API endpoints (`PUT /api/users/me/settings`).
============================================================
"""

from datetime import datetime, timezone
from database import db


class UserSettings(db.Model):
    __tablename__ = 'user_settings'

    id       = db.Column(db.Integer, primary_key=True)
    user_id  = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    theme               = db.Column(db.String(20), nullable=False, default='dark')   # dark, light
    language            = db.Column(db.String(10), nullable=False, default='en')     # en, hi, etc.
    
    email_notifications = db.Column(db.Boolean, nullable=False, default=True)
    project_alerts      = db.Column(db.Boolean, nullable=False, default=True)
    message_alerts      = db.Column(db.Boolean, nullable=False, default=True)
    marketing_emails    = db.Column(db.Boolean, nullable=False, default=False)
    
    is_profile_public   = db.Column(db.Boolean, nullable=False, default=True)

    created_at          = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at          = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship
    user = db.relationship('User', backref=db.backref('settings', uselist=False, cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id':                  self.id,
            'user_id':             self.user_id,
            'theme':               self.theme,
            'language':            self.language,
            'email_notifications': self.email_notifications,
            'project_alerts':      self.project_alerts,
            'message_alerts':      self.message_alerts,
            'marketing_emails':    self.marketing_emails,
            'is_profile_public':   self.is_profile_public,
            'updated_at':          self.updated_at.isoformat() if self.updated_at else None,
        }
