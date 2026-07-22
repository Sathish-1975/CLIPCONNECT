"""
============================================================
ClipConnect - Project Model
============================================================
Why this file exists:
  Defines the database schema for client project postings.
  Allows clients to post video editing jobs, save drafts,
  specify budget, deadline, required skills, and sample files.

How it works:
  - Linked to User (Client) via user_id foreign key.
  - Supports 'fixed' and 'hourly' budget types.
  - Supports 'draft', 'published', 'in_progress', 'closed', 'deleted' statuses.
  - JSON columns for reference_links, sample_files, required_skills, preferred_software.

Connections:
  - User model (client_id)
  - EditorCategory enum (for category matching)
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
    PUBLIC  = 'public'
    PRIVATE = 'private'


class ProjectStatus(enum.Enum):
    DRAFT       = 'draft'
    PUBLISHED   = 'published'
    IN_PROGRESS = 'in_progress'
    CLOSED      = 'closed'
    DELETED     = 'deleted'


class Project(db.Model):
    __tablename__ = 'projects'

    id                 = db.Column(db.Integer, primary_key=True)
    client_id          = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    title              = db.Column(db.String(255), nullable=False)
    category           = db.Column(db.Enum(EditorCategory, native_enum=False), nullable=False, default=EditorCategory.YOUTUBE)
    description        = db.Column(db.Text, nullable=False)
    
    reference_links    = db.Column(db.JSON, nullable=True, default=list)  # List of URLs
    sample_files       = db.Column(db.JSON, nullable=True, default=list)  # List of file dicts {filename, url, size}
    
    budget             = db.Column(db.Numeric(10, 2), nullable=False)
    budget_type        = db.Column(db.Enum(BudgetType, native_enum=False), nullable=False, default=BudgetType.FIXED)
    deadline           = db.Column(db.DateTime(timezone=True), nullable=True)
    
    required_skills    = db.Column(db.JSON, nullable=True, default=list)  # List of strings
    preferred_software = db.Column(db.JSON, nullable=True, default=list)  # List of strings
    
    visibility         = db.Column(db.Enum(ProjectVisibility, native_enum=False), nullable=False, default=ProjectVisibility.PUBLIC)
    editors_required   = db.Column(db.Integer, nullable=False, default=1)
    status             = db.Column(db.Enum(ProjectStatus, native_enum=False), nullable=False, default=ProjectStatus.PUBLISHED)
    
    created_at         = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at         = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    client = db.relationship('User', backref=db.backref('posted_projects', lazy='dynamic', cascade='all, delete-orphan'))

    def to_dict(self, include_client=True):
        data = {
            'id':                 self.id,
            'client_id':          self.client_id,
            'title':              self.title,
            'category':           self.category.value if self.category else None,
            'description':        self.description,
            'reference_links':    self.reference_links or [],
            'sample_files':       self.sample_files or [],
            'budget':             float(self.budget) if self.budget is not None else 0.0,
            'budget_type':        self.budget_type.value if self.budget_type else 'fixed',
            'deadline':           self.deadline.isoformat() if self.deadline else None,
            'required_skills':    self.required_skills or [],
            'preferred_software': self.preferred_software or [],
            'visibility':         self.visibility.value if self.visibility else 'public',
            'editors_required':   self.editors_required,
            'status':             self.status.value if self.status else 'published',
            'created_at':         self.created_at.isoformat() if self.created_at else None,
            'updated_at':         self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_client and self.client:
            data['client'] = {
                'id':         self.client.id,
                'full_name':  self.client.full_name,
                'avatar_url': getattr(self.client.client_profile, 'company_logo', None) if hasattr(self.client, 'client_profile') else None
            }
        return data
