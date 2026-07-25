"""
============================================================
ClipConnect - Email Log Model
============================================================
Why this file exists:
  Defines the database schema for recording outgoing transactional email logs.

What it does:
  - Stores recipient email address, email subject, template name, delivery status ('sent', 'failed'),
    and error message if delivery fails.

How it integrates with the rest of the application:
  - Registered in `models/__init__.py` for DB table management (`email_logs`).
  - Consumed by `email_helper.py` whenever system emails are dispatched (registration, password reset, hire requests, etc.).
============================================================
"""

from datetime import datetime, timezone
from database import db


class EmailLog(db.Model):
    __tablename__ = 'email_logs'

    id              = db.Column(db.Integer, primary_key=True)
    recipient_email = db.Column(db.String(255), nullable=False, index=True)
    subject         = db.Column(db.String(255), nullable=False)
    template_name   = db.Column(db.String(100), nullable=False, default='general')
    status          = db.Column(db.String(50), nullable=False, default='sent')  # sent, failed
    error_message   = db.Column(db.Text, nullable=True)

    sent_at         = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def to_dict(self):
        return {
            'id':              self.id,
            'recipient_email': self.recipient_email,
            'subject':         self.subject,
            'template_name':   self.template_name,
            'status':          self.status,
            'error_message':   self.error_message,
            'sent_at':         self.sent_at.isoformat() if self.sent_at else None,
        }
