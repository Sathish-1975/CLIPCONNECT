"""
============================================================
ClipConnect - Analytics & Video Interaction Models
============================================================
Why this file exists:
  Defines database schemas for tracking editor profile views, video portfolio views,
  and portfolio item likes.

What it does:
  - `ProfileView`: Logs profile visits for editor analytics dashboard.
  - `PortfolioView`: Logs portfolio video plays, view counts, and engagement metrics.
  - `PortfolioLike`: Allows clients/visitors to like portfolio items.

How it integrates with the rest of the application:
  - Registered in `models/__init__.py` for DB table initialization.
  - Consumed by `user_controller.py` and `editor_dashboard_controller.py` to calculate
    total profile views, video view counts, and engagement rates.
============================================================
"""

from datetime import datetime, timezone
from database import db


class ProfileView(db.Model):
    __tablename__ = 'profile_views'

    id        = db.Column(db.Integer, primary_key=True)
    editor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    viewer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)

    ip_address = db.Column(db.String(45), nullable=True)
    viewed_at  = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    editor = db.relationship('User', foreign_keys=[editor_id], backref=db.backref('views_received', lazy='dynamic'))
    viewer = db.relationship('User', foreign_keys=[viewer_id], backref=db.backref('views_made', lazy='dynamic'))

    def to_dict(self):
        return {
            'id':         self.id,
            'editor_id': self.editor_id,
            'viewer_id': self.viewer_id,
            'viewed_at': self.viewed_at.isoformat() if self.viewed_at else None,
        }


class PortfolioView(db.Model):
    __tablename__ = 'portfolio_views'

    id              = db.Column(db.Integer, primary_key=True)
    editor_id       = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    viewer_id       = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    portfolio_index = db.Column(db.Integer, nullable=False, default=0)  # Index of video in portfolio list

    ip_address      = db.Column(db.String(45), nullable=True)
    viewed_at       = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            'id':              self.id,
            'editor_id':       self.editor_id,
            'viewer_id':       self.viewer_id,
            'portfolio_index': self.portfolio_index,
            'viewed_at':       self.viewed_at.isoformat() if self.viewed_at else None,
        }


class PortfolioLike(db.Model):
    __tablename__ = 'portfolio_likes'

    id              = db.Column(db.Integer, primary_key=True)
    editor_id       = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    portfolio_index = db.Column(db.Integer, nullable=False, default=0)

    created_at      = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'editor_id', 'portfolio_index', name='uq_user_portfolio_like'),
    )

    def to_dict(self):
        return {
            'id':              self.id,
            'editor_id':       self.editor_id,
            'user_id':         self.user_id,
            'portfolio_index': self.portfolio_index,
            'created_at':      self.created_at.isoformat() if self.created_at else None,
        }
