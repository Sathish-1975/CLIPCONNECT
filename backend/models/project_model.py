"""
============================================================
ClipConnect - Project Model
============================================================
Why this file exists:
  Defines the primary database schema for client project postings,
  tracking job details, requirements, statuses, revision history,
  timeline events, and file deliverables.

What it does:
  - Supports budget types (fixed / hourly), visibility (public / invite_only),
    and priorities (low, medium, high).
  - Supports comprehensive project lifecycle statuses:
    draft, published, pending, waiting_for_editor, accepted, in_progress,
    under_review, revision_requested, completed, closed, cancelled, deleted.
  - Tracks reference links, sample files, project deliverables, and timeline history.
  - Links to Client (client_id) and hired Editor (hired_editor_id).

How it integrates with the rest of the application:
  - Registered in `models/__init__.py` for DB table management.
  - Used extensively by `project_controller.py`, `hire_controller.py`,
    `review_controller.py`, and `revision_controller.py`.
============================================================
"""

from datetime import datetime, timezone
import enum
from database import db
from models.editor_profile_model import EditorCategory


class BudgetType(enum.Enum):
    FIXED  = 'fixed'
    HOURLY = 'hourly'


class ProjectVisibility(enum.Enum):
    PUBLIC      = 'public'
    INVITE_ONLY = 'invite_only'
    PRIVATE     = 'private'


class ProjectPriority(enum.Enum):
    LOW    = 'low'
    MEDIUM = 'medium'
    HIGH   = 'high'


class ProjectStatus(enum.Enum):
    DRAFT               = 'draft'
    PUBLISHED           = 'published'
    PENDING             = 'pending'
    WAITING_FOR_EDITOR  = 'waiting_for_editor'
    ACCEPTED            = 'accepted'
    IN_PROGRESS         = 'in_progress'
    UNDER_REVIEW        = 'under_review'
    REVISION_REQUESTED  = 'revision_requested'
    COMPLETED           = 'completed'
    CLOSED              = 'closed'
    CANCELLED           = 'cancelled'
    DELETED             = 'deleted'


class Project(db.Model):
    __tablename__ = 'projects'

    id                 = db.Column(db.Integer, primary_key=True)
    client_id          = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    title              = db.Column(db.String(255), nullable=False)
    category           = db.Column(db.Enum(EditorCategory, native_enum=False), nullable=False, default=EditorCategory.YOUTUBE)
    description        = db.Column(db.Text, nullable=False)

    reference_links    = db.Column(db.JSON, nullable=True, default=list)  # List of URLs
    sample_files       = db.Column(db.JSON, nullable=True, default=list)  # List of file dicts {filename, url, size}
    project_files      = db.Column(db.JSON, nullable=True, default=list)  # List of deliverable file dicts {filename, url, uploaded_by, created_at}
    timeline           = db.Column(db.JSON, nullable=True, default=list)  # List of timeline events [{status, title, timestamp, note}]

    budget             = db.Column(db.Numeric(10, 2), nullable=False)
    budget_type        = db.Column(db.Enum(BudgetType, native_enum=False), nullable=False, default=BudgetType.FIXED)
    deadline           = db.Column(db.DateTime(timezone=True), nullable=True)

    required_skills     = db.Column(db.JSON, nullable=True, default=list)  # List of strings
    preferred_software  = db.Column(db.JSON, nullable=True, default=list)  # List of strings
    experience_required = db.Column(db.String(100), nullable=True, default='Intermediate')

    priority           = db.Column(db.Enum(ProjectPriority, native_enum=False), nullable=False, default=ProjectPriority.MEDIUM)
    visibility         = db.Column(db.Enum(ProjectVisibility, native_enum=False), nullable=False, default=ProjectVisibility.PUBLIC)
    editors_required   = db.Column(db.Integer, nullable=False, default=1)
    hired_editor_id    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True, comment='Editor hired for this project')
    status             = db.Column(db.Enum(ProjectStatus, native_enum=False), nullable=False, default=ProjectStatus.PUBLISHED)
    payment_status     = db.Column(db.String(50), nullable=False, default='pending') # pending, processing, paid, failed

    created_at         = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at         = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    client       = db.relationship('User', foreign_keys=[client_id], backref=db.backref('posted_projects', lazy='dynamic', cascade='all, delete-orphan'))
    hired_editor = db.relationship('User', foreign_keys=[hired_editor_id], backref=db.backref('hired_projects', lazy='dynamic'))

    def add_timeline_event(self, status_str: str, title: str, note: str = ""):
        """Helper to append an event to the project's timeline."""
        events = list(self.timeline or [])
        events.append({
            'status': status_str,
            'title': title,
            'note': note,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        self.timeline = events

    def to_dict(self, include_client=True):
        data = {
            'id':                  self.id,
            'client_id':           self.client_id,
            'hired_editor_id':     self.hired_editor_id,
            'title':               self.title,
            'category':            self.category.value if self.category else None,
            'description':         self.description,
            'reference_links':     self.reference_links or [],
            'sample_files':        self.sample_files or [],
            'project_files':       self.project_files or [],
            'timeline':            self.timeline or [],
            'budget':              float(self.budget) if self.budget is not None else 0.0,
            'budget_type':         self.budget_type.value if self.budget_type else 'fixed',
            'deadline':            self.deadline.isoformat() if self.deadline else None,
            'required_skills':     self.required_skills or [],
            'preferred_software':  self.preferred_software or [],
            'experience_required': self.experience_required or 'Intermediate',
            'priority':            self.priority.value if self.priority else 'medium',
            'visibility':          self.visibility.value if self.visibility else 'public',
            'editors_required':    self.editors_required,
            'status':              self.status.value if self.status else 'published',
            'payment_status':      self.payment_status,
            'created_at':          self.created_at.isoformat() if self.created_at else None,
            'updated_at':          self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_client and self.client:
            data['client'] = {
                'id':         self.client.id,
                'full_name':  self.client.full_name,
                'avatar_url': getattr(self.client.client_profile, 'profile_photo', None) if hasattr(self.client, 'client_profile') else None
            }
        if self.hired_editor:
            data['hired_editor'] = {
                'id':        self.hired_editor.id,
                'full_name': self.hired_editor.full_name,
            }
        return data

