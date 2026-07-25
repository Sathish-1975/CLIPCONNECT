"""
============================================================
ClipConnect - Payment, Transaction & Invoice Models
============================================================
Why this file exists:
  Defines database schemas for Razorpay payment integration, escrow fund holding,
  transaction history logs, and billing invoices.

What it does:
  - `Payment`: Stores payment orders, Razorpay transaction IDs, signatures, amounts,
    and escrow statuses ('created', 'escrow_held', 'released', 'refunded', 'failed').
  - `Transaction`: Logs ledger entries for deposits, escrow releases to editors, payouts, and refunds.
  - `Invoice`: Generates unique invoice numbers, billing amounts, and downloadable receipt records.

How it integrates with the rest of the application:
  - Registered in `models/__init__.py` for database table creation.
  - Consumed by `payment_controller.py` during checkout verification and fund release.
  - Displayed on Client & Editor Dashboard financial panels.
============================================================
"""

from datetime import datetime, timezone
import uuid
from database import db


class Payment(db.Model):
    __tablename__ = 'payments'

    id                  = db.Column(db.Integer, primary_key=True)
    project_id          = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    client_id           = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    editor_id           = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    razorpay_order_id   = db.Column(db.String(255), nullable=True, unique=True, index=True)
    razorpay_payment_id = db.Column(db.String(255), nullable=True, index=True)
    razorpay_signature  = db.Column(db.String(500), nullable=True)

    amount              = db.Column(db.Numeric(10, 2), nullable=False)
    currency            = db.Column(db.String(10), nullable=False, default='INR')
    status              = db.Column(db.String(50), nullable=False, default='created') # created, escrow_held, released, refunded, failed

    created_at          = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at          = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    project      = db.relationship('Project', backref=db.backref('payments', lazy='dynamic'))
    client       = db.relationship('User', foreign_keys=[client_id], backref=db.backref('payments_made', lazy='dynamic'))
    editor       = db.relationship('User', foreign_keys=[editor_id], backref=db.backref('payments_received', lazy='dynamic'))
    transactions = db.relationship('Transaction', backref='payment', lazy='select', cascade='all, delete-orphan')
    invoice      = db.relationship('Invoice', backref='payment', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':                  self.id,
            'project_id':          self.project_id,
            'client_id':           self.client_id,
            'editor_id':           self.editor_id,
            'razorpay_order_id':   self.razorpay_order_id,
            'razorpay_payment_id': self.razorpay_payment_id,
            'amount':              float(self.amount) if self.amount is not None else 0.0,
            'currency':            self.currency,
            'status':              self.status,
            'created_at':          self.created_at.isoformat() if self.created_at else None,
            'updated_at':          self.updated_at.isoformat() if self.updated_at else None,
            'project_title':       self.project.title if self.project else None,
            'client_name':         self.client.full_name if self.client else None,
            'editor_name':         self.editor.full_name if self.editor else None,
        }


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id          = db.Column(db.Integer, primary_key=True)
    payment_id  = db.Column(db.Integer, db.ForeignKey('payments.id', ondelete='CASCADE'), nullable=False, index=True)

    type        = db.Column(db.String(50), nullable=False) # deposit, release, payout, refund
    amount      = db.Column(db.Numeric(10, 2), nullable=False)
    status      = db.Column(db.String(50), nullable=False, default='success') # pending, success, failed
    notes       = db.Column(db.Text, nullable=True)

    created_at  = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            'id':         self.id,
            'payment_id': self.payment_id,
            'type':       self.type,
            'amount':     float(self.amount) if self.amount is not None else 0.0,
            'status':     self.status,
            'notes':      self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Invoice(db.Model):
    __tablename__ = 'invoices'

    id             = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(100), nullable=False, unique=True, default=lambda: f"INV-{uuid.uuid4().hex[:8].upper()}")
    payment_id     = db.Column(db.Integer, db.ForeignKey('payments.id', ondelete='CASCADE'), nullable=False, index=True)
    client_id      = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    editor_id      = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    amount         = db.Column(db.Numeric(10, 2), nullable=False)
    pdf_url        = db.Column(db.String(500), nullable=True)

    created_at     = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    client = db.relationship('User', foreign_keys=[client_id], backref=db.backref('invoices_client', lazy='dynamic'))
    editor = db.relationship('User', foreign_keys=[editor_id], backref=db.backref('invoices_editor', lazy='dynamic'))

    def to_dict(self):
        return {
            'id':             self.id,
            'invoice_number': self.invoice_number,
            'payment_id':     self.payment_id,
            'client_id':      self.client_id,
            'editor_id':      self.editor_id,
            'amount':         float(self.amount) if self.amount is not None else 0.0,
            'pdf_url':        self.pdf_url,
            'created_at':     self.created_at.isoformat() if self.created_at else None,
        }
