from datetime import datetime

from database import db

class Proposal(db.Model):
    __tablename__ = 'proposals'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    editor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    # New fields
    cover_letter = db.Column(db.Text, nullable=True)
    proposed_price = db.Column(db.Numeric(10, 2), nullable=True)
    estimated_delivery_time = db.Column(db.DateTime(timezone=True), nullable=True)  # Expected delivery datetime
    portfolio_links = db.Column(db.JSON, nullable=True, default=list)  # List of URLs
    client_questions = db.Column(db.JSON, nullable=True, default=list)  # List of strings
    status = db.Column(db.String(50), nullable=False, default='pending')  # pending, accepted, rejected, shortlisted, withdrawn
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.utcnow(), nullable=False)
    # Relationships
    project = db.relationship('Project', backref=db.backref('proposals', lazy='dynamic'))
    editor = db.relationship('User', backref=db.backref('proposals', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'editor_id': self.editor_id,
            'cover_letter': self.cover_letter,
            'proposed_price': float(self.proposed_price) if self.proposed_price is not None else None,
            'estimated_delivery_time': self.estimated_delivery_time.isoformat() if self.estimated_delivery_time else None,
            'portfolio_links': self.portfolio_links or [],
            'client_questions': self.client_questions or [],
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
