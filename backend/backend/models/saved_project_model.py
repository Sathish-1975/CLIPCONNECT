from datetime import datetime
from database import db

class SavedProject(db.Model):
    __tablename__ = 'saved_projects'
    __table_args__ = (
        db.UniqueConstraint('editor_id', 'project_id', name='uq_editor_saved_project'),
    )

    id = db.Column(db.Integer, primary_key=True)
    editor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.utcnow(), nullable=False)

    # Relationships
    project = db.relationship('Project', backref=db.backref('saved_by', lazy='dynamic', cascade='all, delete-orphan'))
    editor = db.relationship('User', backref=db.backref('saved_projects', lazy='dynamic', cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'editor_id': self.editor_id,
            'project_id': self.project_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'project': self.project.to_dict() if self.project else None
        }
