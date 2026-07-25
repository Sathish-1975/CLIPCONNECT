"""
============================================================
ClipConnect - Message & Attachment Models
============================================================
Why this file exists:
  Defines the database schemas for real-time one-to-one messaging,
  chat attachments, and message state tracking (reading, pinning, replying).

What it does:
  - `Message`: Stores text, voice notes, emojis, typing status, pin status,
    read receipts, and reply-to threading between users.
  - `MessageAttachment`: Stores attached media files (images, videos, audio, documents, ZIPs).

How it integrates with the rest of the application:
  - Registered in `models/__init__.py` for SQLAlchemy table auto-creation.
  - Consumed by `chat_controller.py` and `socket_events.py` for WebSockets real-time chat.
  - Linked to `User` and `Project` models via ForeignKeys.
============================================================
"""

from datetime import datetime, timezone
from database import db


class Message(db.Model):
    __tablename__ = 'messages'

    id          = db.Column(db.Integer, primary_key=True)
    sender_id   = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    project_id  = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True)
    reply_to_id = db.Column(db.Integer, db.ForeignKey('messages.id', ondelete='SET NULL'), nullable=True)

    content     = db.Column(db.Text, nullable=True)
    message_type = db.Column(db.String(50), nullable=False, default='text')  # text, image, video, audio, voice_note, file

    is_read     = db.Column(db.Boolean, default=False, nullable=False)
    is_edited   = db.Column(db.Boolean, default=False, nullable=False)
    is_pinned   = db.Column(db.Boolean, default=False, nullable=False)

    created_at  = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at  = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    sender      = db.relationship('User', foreign_keys=[sender_id], backref=db.backref('sent_messages', lazy='dynamic'))
    receiver    = db.relationship('User', foreign_keys=[receiver_id], backref=db.backref('received_messages', lazy='dynamic'))
    project     = db.relationship('Project', backref=db.backref('messages', lazy='dynamic'))
    reply_to    = db.relationship('Message', remote_side=[id], backref=db.backref('replies', lazy='dynamic'))
    attachments = db.relationship('MessageAttachment', backref='message', lazy='select', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':           self.id,
            'sender_id':     self.sender_id,
            'receiver_id':   self.receiver_id,
            'project_id':    self.project_id,
            'reply_to_id':   self.reply_to_id,
            'content':       self.content,
            'message_type':  self.message_type,
            'is_read':       self.is_read,
            'is_edited':     self.is_edited,
            'is_pinned':     self.is_pinned,
            'created_at':    self.created_at.isoformat() if self.created_at else None,
            'updated_at':    self.updated_at.isoformat() if self.updated_at else None,
            'sender_name':   self.sender.full_name if self.sender else None,
            'receiver_name': self.receiver.full_name if self.receiver else None,
            'attachments':   [a.to_dict() for a in self.attachments],
            'reply_to_snippet': self.reply_to.content[:60] if self.reply_to and self.reply_to.content else None,
        }


class MessageAttachment(db.Model):
    __tablename__ = 'message_attachments'

    id         = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False, index=True)

    file_url   = db.Column(db.String(500), nullable=False)
    file_type  = db.Column(db.String(50), nullable=False)  # image, video, audio, document, zip
    file_name  = db.Column(db.String(255), nullable=False)
    file_size  = db.Column(db.Integer, nullable=True)     # bytes

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            'id':         self.id,
            'message_id': self.message_id,
            'file_url':   self.file_url,
            'file_type':  self.file_type,
            'file_name':  self.file_name,
            'file_size':  self.file_size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
