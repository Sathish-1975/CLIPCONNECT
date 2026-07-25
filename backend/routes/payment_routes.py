"""
============================================================
ClipConnect - Payment Routes
============================================================
Why this file exists:
  Exposes REST API endpoints for Razorpay order initialization, payment verification,
  escrow fund release, and financial transaction history.

Routes:
  POST /api/payments/create-order  -> Initialize Razorpay payment order
  POST /api/payments/verify        -> Verify payment signature & deposit into Escrow
  POST /api/payments/release       -> Release escrow funds to editor
  GET  /api/payments/history       -> Fetch user payment transactions & invoices

How it integrates with the rest of the application:
  - Registered under prefix `/api/payments` in `routes/__init__.py`.
  - Protected with JWT `@token_required` middleware.
============================================================
"""

from flask import Blueprint
from middleware.auth_middleware import token_required
import controllers.payment_controller as pay_ctrl

payment_bp = Blueprint('payment_bp', __name__)


@payment_bp.route('/create-order', methods=['POST'])
@token_required
def create_order(current_user):
    """POST /api/payments/create-order — Initialize payment order."""
    return pay_ctrl.create_payment_order(current_user)


@payment_bp.route('/verify', methods=['POST'])
@token_required
def verify_payment(current_user):
    """POST /api/payments/verify — Verify signature & hold in Escrow."""
    return pay_ctrl.verify_payment(current_user)


@payment_bp.route('/release', methods=['POST'])
@token_required
def release_payment(current_user):
    """POST /api/payments/release — Release escrow funds to editor."""
    return pay_ctrl.release_payment(current_user)


@payment_bp.route('/history', methods=['GET'])
@token_required
def payment_history(current_user):
    """GET /api/payments/history — Get transaction history and invoices."""
    return pay_ctrl.get_payment_history(current_user)
