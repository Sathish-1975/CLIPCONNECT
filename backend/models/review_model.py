"""
============================================================
ClipConnect - Review Model
============================================================
Why this file exists:
  Defines the database schema for client-submitted reviews and ratings
  for editors upon completion of a project.

What it does:
  - Stores overall rating (1-5 ⭐) as well as category ratings:
    communication_rating, creativity_rating, delivery_rating, professionalism_rating.
  - Stores comment, recommendation flag (would recommend editor), and anonymous option.
  - Links reviewer (Client), editor (Editor), and Project via ForeignKeys.
  - Enforces unique constraint preventing multiple reviews for the same project.

How it integrates with the rest of the application:
  - Imported in `models/__init__.py` for SQLAlchemy table auto-creation.
  - Consumed by `review_controller.py` to save reviews and recalculate EditorProfile avg_rating.
  - Displayed on Editor Profile page and Client/Editor Dashboards.
============================================================
"""

from datetime import datetime, timezone
from database import db


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    editor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True)

    # Detailed Ratings (1-5)
    overall_rating         = db.Column(db.Integer, nullable=False, default=5)
    communication_rating   = db.Column(db.Integer, nullable=True, default=5)
    creativity_rating      = db.Column(db.Integer, nullable=True, default=5)
    delivery_rating        = db.Column(db.Integer, nullable=True, default=5)
    professionalism_rating = db.Column(db.Integer, nullable=True, default=5)

    comment           = db.Column(db.Text, nullable=True)
    would_recommend   = db.Column(db.Boolean, nullable=False, default=True)
    is_anonymous      = db.Column(db.Boolean, nullable=False, default=False)

    created_at        = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], backref=db.backref('reviews_given', lazy='dynamic'))
    editor   = db.relationship('User', foreign_keys=[editor_id],   backref=db.backref('reviews_received', lazy='dynamic'))
    project  = db.relationship('Project', backref=db.backref('reviews', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('reviewer_id', 'project_id', name='uq_review_per_project'),
    )

    def to_dict(self):
        reviewer_info = None
        if self.reviewer and not self.is_anonymous:
            reviewer_info = {
                'id':        self.reviewer.id,
                'full_name': self.reviewer.full_name,
            }

        return {
            'id':                     self.id,
            'reviewer_id':            self.reviewer_id if not self.is_anonymous else None,
            'editor_id':              self.editor_id,
            'project_id':             self.project_id,
            'overall_rating':         self.overall_rating,
            'communication_rating':   self.communication_rating,
            'creativity_rating':      self.creativity_rating,
            'delivery_rating':        self.delivery_rating,
            'professionalism_rating': self.professionalism_rating,
            'comment':                self.comment,
            'would_recommend':        self.would_recommend,
            'is_anonymous':           self.is_anonymous,
            'created_at':             self.created_at.isoformat() if self.created_at else None,
            'reviewer':               reviewer_info if not self.is_anonymous else {'full_name': 'Anonymous Client'},
        }

