"""
============================================================
ClipConnect - Client Profile Model
============================================================
Table: client_profiles
Relationship: One-to-One with users (client role only)

Stores:
  - Favorite editors list (JSON array of user_ids)
  - Client avatar, phone, company, bio, location
  - Notification preferences
  - Notification history (JSON)
============================================================
"""

from datetime import datetime, timezone
from database import db


class ClientProfile(db.Model):
    __tablename__ = 'client_profiles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        unique=True, nullable=False, index=True
    )

    # ── Identity ──────────────────────────────────────────
    profile_photo = db.Column(db.String(500), nullable=True)
    phone         = db.Column(db.String(20),  nullable=True)
    company       = db.Column(db.String(150), nullable=True)
    bio           = db.Column(db.Text,        nullable=True)
    city          = db.Column(db.String(100), nullable=True)
    country       = db.Column(db.String(100), nullable=True)
    website       = db.Column(db.String(500), nullable=True)

    # ── Favorites: list of editor user_ids ────────────────
    # e.g. [2, 7, 15]
    favorite_editors = db.Column(db.JSON, nullable=True, default=list)

    # ── Notifications ─────────────────────────────────────
    # List of { id, type, title, message, read, created_at }
    notifications = db.Column(db.JSON, nullable=True, default=list)

    # Notification preferences
    notif_email    = db.Column(db.Boolean, default=True)
    notif_projects = db.Column(db.Boolean, default=True)
    notif_messages = db.Column(db.Boolean, default=True)

    # ── Timestamps ────────────────────────────────────────
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # ── Relationship ──────────────────────────────────────
    user = db.relationship(
        'User',
        backref=db.backref('client_profile', uselist=False, lazy='joined'),
        lazy='joined'
    )

    def __init__(self, user_id, **kwargs):
        self.user_id = user_id
        self.favorite_editors = []
        self.notifications    = []
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

    def to_dict(self):
        return {
            'id':               self.id,
            'user_id':          self.user_id,
            'profile_photo':    self.profile_photo,
            'phone':            self.phone,
            'company':          self.company,
            'bio':              self.bio,
            'city':             self.city,
            'country':          self.country,
            'website':          self.website,
            'favorite_editors': self.favorite_editors or [],
            'notif_email':      self.notif_email,
            'notif_projects':   self.notif_projects,
            'notif_messages':   self.notif_messages,
            'created_at':       self.created_at.isoformat() if self.created_at else None,
            'updated_at':       self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_unread_count(self):
        notifs = self.notifications or []
        return sum(1 for n in notifs if not n.get('read', False))

    def __repr__(self):
        return f"<ClientProfile user_id={self.user_id}>"
