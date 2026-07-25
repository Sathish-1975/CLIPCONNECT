"""
============================================================
ClipConnect - Admin Routes
============================================================
Why this file exists:
  Exposes REST API endpoints for the Admin Control Panel including platform metrics,
  user moderation, project oversight, and financial ledgers.

Routes:
  GET   /api/admin/dashboard          -> Overall platform analytics & stats
  GET   /api/admin/users              -> List all users (clients & editors)
  PATCH /api/admin/users/<id>/status  -> Modifies user status (verify/suspend/delete)
  GET   /api/admin/projects           -> All platform projects
  GET   /api/admin/payments           -> All financial transaction logs

How it integrates with the rest of the application:
  - Registered under prefix `/api/admin` in `routes/__init__.py`.
  - Protected with `@token_required` and Admin role checks.
============================================================
"""

from flask import Blueprint
from middleware.auth_middleware import token_required
import controllers.admin_controller as admin_ctrl

admin_bp = Blueprint('admin_bp', __name__)


@admin_bp.route('/dashboard', methods=['GET'])
@token_required
def get_dashboard_stats(current_user):
    """GET /api/admin/dashboard — Overview statistics."""
    return admin_ctrl.get_admin_dashboard_stats(current_user)


@admin_bp.route('/users', methods=['GET'])
@token_required
def list_users(current_user):
    """GET /api/admin/users — List platform users."""
    return admin_ctrl.list_all_users(current_user)


@admin_bp.route('/users/<int:user_id>/status', methods=['PATCH'])
@token_required
def update_user_status(current_user, user_id):
    """PATCH /api/admin/users/<user_id>/status — User moderation."""
    return admin_ctrl.update_user_status(current_user, user_id)


@admin_bp.route('/projects', methods=['GET'])
@token_required
def list_projects(current_user):
    """GET /api/admin/projects — List all projects."""
    return admin_ctrl.list_all_projects(current_user)


@admin_bp.route('/payments', methods=['GET'])
@token_required
def list_payments(current_user):
    """GET /api/admin/payments — List all financial transactions."""
    return admin_ctrl.list_all_payments(current_user)
