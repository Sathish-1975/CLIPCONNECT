"""
============================================================
ClipConnect - Revision Request Model
============================================================
Why this file exists:
  Defines the database schema for revision requests made by clients on projects.

What it does:
  - Tracks client feedback, revision comments, and reference files.
  - Tracks editor responses, updated work file uploads, and completion status.
  - Supports revision statuses: 'pending', 'in_progress', 'completed'.
  - Maintains complete revision history per project.

How it integrates with the rest of the application:
  - Imported in `models/__init__.py` for database table initialization (`revision_requests`).
  - Linked to `Project` and `User` models via ForeignKeys.
  - Handled by project controllers and endpoints for revision management.
============================================================
"""

from datetime import datetime, timezone
from database import db


class RevisionRequest(db.Model):
    __tablename__ = 'revision_requests'

    id         = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    client_id  = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    editor_id  = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    title              = db.Column(db.String(255), nullable=False, default="Revision Request")
    comments           = db.Column(db.Text, nullable=False)
    reference_files    = db.Column(db.JSON, nullable=True, default=list)  # List of {filename, url, type}
    updated_work_files = db.Column(db.JSON, nullable=True, default=list)  # List of {filename, url, type}
    editor_notes       = db.Column(db.Text, nullable=True)

    status             = db.Column(db.String(50), nullable=False, default='pending')  # pending, in_progress, completed

    created_at         = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at         = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    project = db.relationship('Project', backref=db.backref('revisions', lazy='dynamic', cascade='all, delete-orphan'))
    client  = db.relationship('User', foreign_keys=[client_id], backref=db.backref('revisions_requested', lazy='dynamic'))
    editor  = db.relationship('User', foreign_keys=[editor_id], backref=db.backref('revisions_assigned', lazy='dynamic'))

    def to_dict(self):
        return {
            'id':                 self.id,
            'project_id':         self.project_id,
            'client_id':          self.client_id,
            'editor_id':          self.editor_id,
            'title':              self.title,
            'comments':           self.comments,
            'reference_files':    self.reference_files or [],
            'updated_work_files': self.updated_work_files or [],
            'editor_notes':       self.editor_notes,
            'status':             self.status,
            'created_at':         self.created_at.isoformat() if self.created_at else None,
            'updated_at':         self.updated_at.isoformat() if self.updated_at else None,
        }
