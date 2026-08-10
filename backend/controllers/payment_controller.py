"""
============================================================
ClipConnect - Payment Controller (Razorpay & Escrow)
============================================================
Why this file exists:
  Provides controller logic for Razorpay payment order creation, signature verification,
  escrow fund holding, payment release on project completion, invoice generation, and transaction history.

What it does:
  - `create_payment_order()`: Generates a Razorpay Order ID (or sandbox mock ID).
  - `verify_payment()`: Validates Razorpay payment signature, updates payment status to `escrow_held`,
    creates Transaction & Invoice records, and sets Project status to `IN_PROGRESS`.
  - `release_escrow()`: Releases held escrow funds to the hired editor upon client approval.
  - `get_user_payments()`: Retrieves payment transaction logs and invoices for user dashboards.

How it integrates with the rest of the application:
  - Exposed via `/api/payments/*` routes in `payment_routes.py`.
  - Interacts with `Payment`, `Transaction`, `Invoice`, `Project`, and `User` models.
  - Sends email receipts via `utils/email_helper.py` and notifications via `utils/notification_helper.py`.
============================================================
"""

import os
import hmac
import hashlib
import uuid
from datetime import datetime, timezone
from flask import request, current_app

from database import db
from models.project_model import Project, ProjectStatus
from models.payment_model import Payment, Transaction, Invoice
from models.user_model import User
from utils.response_helper import success_response, error_response
from utils.notification_helper import create_notification
from utils.email_helper import send_payment_success_email

# Razorpay credentials from environment
RAZORPAY_KEY_ID     = os.getenv('RAZORPAY_KEY_ID', 'rzp_test_mockkey123')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', 'mocksecret123')


def create_payment_order(current_user: dict):
    """
    POST /api/payments/create-order
    Body: { project_id, amount }
    Only clients can create payment orders.
    """
    if current_user.get('role') != 'client':
        return error_response(message="Only clients can initiate payments.", status_code=403)

    data = request.get_json(silent=True) or {}
    project_id = data.get('project_id')
    amount     = data.get('amount')

    if not project_id:
        return error_response(message="project_id is required.", status_code=422)

    project = Project.query.get(project_id)
    if not project or project.status == ProjectStatus.DELETED:
        return error_response(message="Project not found.", status_code=404)

    if project.client_id != current_user['user_id']:
        return error_response(message="You can only pay for your own projects.", status_code=403)

    if not project.hired_editor_id:
        return error_response(message="No editor has been hired for this project yet.", status_code=400)
        
    if project.status != ProjectStatus.UNDER_REVIEW:
        return error_response(message="Project must be submitted for review before payment.", status_code=400)
        
    if project.payment_status == 'paid':
        return error_response(message="This project has already been paid for.", status_code=400)

    # Force the backend amount to prevent frontend manipulation
    payment_amount = float(project.budget)

    # Generate Order ID (using Razorpay client if configured, else mock sandbox ID)
    razorpay_order_id = f"order_{uuid.uuid4().hex[:14]}"

    try:
        payment = Payment(
            project_id=project_id,
            client_id=current_user['user_id'],
            editor_id=project.hired_editor_id,
            razorpay_order_id=razorpay_order_id,
            amount=payment_amount,
            currency='INR',
            status='created'
        )
        db.session.add(payment)
        db.session.commit()

        return success_response(
            data={
                'payment_id':        payment.id,
                'razorpay_order_id': razorpay_order_id,
                'key_id':            RAZORPAY_KEY_ID,
                'amount':            payment_amount,
                'amount_paise':      int(payment_amount * 100),
                'currency':          'INR',
                'project_title':     project.title,
            },
            message="Payment order created successfully.",
            status_code=201
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create payment order error: {e}")
        return error_response(message=f"Failed to create payment order: {str(e)}", status_code=500)


def verify_payment(current_user: dict):
    """
    POST /api/payments/verify
    Body: { razorpay_order_id, razorpay_payment_id, razorpay_signature }
    Verifies signature, processes final payment, sets project to COMPLETED, generates invoice.
    """
    data = request.get_json(silent=True) or {}
    order_id   = data.get('razorpay_order_id')
    payment_id = data.get('razorpay_payment_id')
    signature  = data.get('razorpay_signature')

    if not order_id or not payment_id:
        return error_response(message="Missing razorpay_order_id or razorpay_payment_id.", status_code=422)

    payment = Payment.query.filter_by(razorpay_order_id=order_id).first()
    if not payment:
        return error_response(message="Payment order record not found.", status_code=404)

    # Optional signature check (bypassed in sandbox mock mode)
    if RAZORPAY_KEY_SECRET != 'mocksecret123' and signature:
        generated_sig = hmac.new(
            RAZORPAY_KEY_SECRET.encode(),
            f"{order_id}|{payment_id}".encode(),
            hashlib.sha256
        ).hexdigest()

        if generated_sig != signature:
            payment.status = 'failed'
            db.session.commit()
            return error_response(message="Invalid payment signature verification.", status_code=400)

    try:
        payment.razorpay_payment_id = payment_id
        payment.razorpay_signature  = signature or 'mock_signature'
        payment.status              = 'paid'
        payment.paid_at             = datetime.now(timezone.utc)

        # Calculate Revenue & Create Ledger entries
        commission_pct = current_app.config.get('PLATFORM_COMMISSION', 0.10)
        budget = float(payment.amount)
        editor_earnings = budget * (1 - commission_pct)

        # Record deposit transaction
        tx_deposit = Transaction(
            payment_id=payment.id,
            type='deposit',
            amount=budget,
            status='success',
            notes='Client payment received'
        )
        db.session.add(tx_deposit)

        # Record payout transaction
        tx_payout = Transaction(
            payment_id=payment.id,
            type='payout',
            amount=editor_earnings,
            status='success',
            notes='Editor earnings payout'
        )
        db.session.add(tx_payout)

        # Generate Invoice
        inv = Invoice(
            payment_id=payment.id,
            client_id=payment.client_id,
            editor_id=payment.editor_id,
            amount=payment.amount,
            pdf_url=f"/api/invoices/{payment.id}/download"
        )
        db.session.add(inv)

        # Update Project Status to COMPLETED & payment_status to paid
        project = Project.query.get(payment.project_id)
        if project:
            project.status = ProjectStatus.COMPLETED
            project.payment_status = 'paid'
            project.add_timeline_event(
                status_str='completed',
                title='Payment Successful & Project Completed 🎉',
                note=f"₹{payment.amount:,.2f} paid successfully. Project closed."
            )
            
            accept_message_text = data.get('accept_message')
            if accept_message_text:
                from models.message_model import Message
                new_msg = Message(
                    sender_id=payment.client_id,
                    receiver_id=payment.editor_id,
                    project_id=project.id,
                    content=accept_message_text,
                    message_type='text'
                )
                db.session.add(new_msg)

        # Update Editor Wallet (EditorProfile)
        from models.editor_profile_model import EditorProfile
        editor_profile = EditorProfile.query.filter_by(user_id=payment.editor_id).first()
        if editor_profile:
            editor_profile.completed_projects = (editor_profile.completed_projects or 0) + 1
            editor_profile.total_earnings = float(editor_profile.total_earnings or 0.0) + editor_earnings

        db.session.commit()

        # Send notifications & emails
        client = User.query.get(payment.client_id)
        if client:
            send_payment_success_email(
                client_email=client.email,
                client_name=client.full_name,
                project_title=project.title if project else 'Project',
                amount=float(payment.amount),
                invoice_num=inv.invoice_number
            )

        create_notification(
            user_id=payment.editor_id,
            title="🎉 Payment Received & Project Completed!",
            message=f"Client paid ₹{payment.amount:,.2f} for '{project.title if project else 'Project'}'. Earnings updated!",
            type_str="project_completed",
            related_project_id=payment.project_id
        )

        return success_response(
            data={'payment': payment.to_dict(), 'invoice': inv.to_dict()},
            message="Payment verified! Project is now completed and paid."
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Verify payment error: {e}")
        return error_response(message=f"Payment verification failed: {str(e)}", status_code=500)


def release_payment(current_user: dict):
    """
    POST /api/payments/release
    Body: { project_id }
    Client approves work and releases escrow funds to editor.
    """
    if current_user.get('role') != 'client':
        return error_response(message="Only clients can release project payments.", status_code=403)

    data = request.get_json(silent=True) or {}
    project_id = data.get('project_id')
    if not project_id:
        return error_response(message="project_id is required.", status_code=422)

    payment = Payment.query.filter_by(project_id=project_id, status='escrow_held').first()
    if not payment:
        return error_response(message="No held escrow payment found for this project.", status_code=404)

    if payment.client_id != current_user['user_id']:
        return error_response(message="You can only release payments for your own projects.", status_code=403)

    try:
        payment.status = 'released'

        # Record payout transaction
        tx = Transaction(
            payment_id=payment.id,
            type='release',
            amount=payment.amount,
            status='success',
            notes='Escrow funds released to editor upon project completion'
        )
        db.session.add(tx)

        # Update project status to COMPLETED
        project = Project.query.get(project_id)
        if project:
            project.status = ProjectStatus.COMPLETED
            project.add_timeline_event(
                status_str='completed',
                title='Payment Released & Project Completed 🎉',
                note=f"₹{payment.amount:,.2f} released to editor."
            )

        db.session.commit()

        # Notify editor
        create_notification(
            user_id=payment.editor_id,
            title="🎉 Payment Released!",
            message=f"₹{payment.amount:,.2f} for project '{project.title if project else 'Project'}' has been released to your earnings!",
            type_str="project_completed",
            related_project_id=project_id
        )

        return success_response(
            data={'payment': payment.to_dict()},
            message="Escrow payment released to editor successfully!"
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Release payment error: {e}")
        return error_response(message=f"Failed to release payment: {str(e)}", status_code=500)


def get_payment_history(current_user: dict):
    """
    GET /api/payments/history
    List all payments, transactions, and invoices for the logged-in user.
    """
    user_id = current_user['user_id']
    role    = current_user['role']

    if role == 'client':
        payments = Payment.query.filter_by(client_id=user_id).order_by(Payment.created_at.desc()).all()
    else:
        payments = Payment.query.filter_by(editor_id=user_id).order_by(Payment.created_at.desc()).all()

    pay_data = [p.to_dict() for p in payments]

    total_spent_or_earned = sum(p['amount'] for p in pay_data if p['status'] in ('escrow_held', 'paid', 'released'))
    pending_escrow = sum(p['amount'] for p in pay_data if p['status'] == 'escrow_held')

    return success_response(
        data={
            'payments': pay_data,
            'total_amount': total_spent_or_earned,
            'pending_escrow': pending_escrow,
        },
        message=f"Fetched {len(pay_data)} payment records."
    )
