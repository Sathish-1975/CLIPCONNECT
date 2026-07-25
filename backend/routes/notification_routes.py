"""
============================================================
ClipConnect - Notification Routes
============================================================
Routes:
  GET   /api/notifications          -> Get user notifications
  PATCH /api/notifications/<id>/read -> Mark single notification read
  PATCH /api/notifications/read-all  -> Mark all notifications read
============================================================
"""

from flask import Blueprint
from middleware.auth_middleware import token_required
import controllers.notification_controller as notif_ctrl

notification_bp = Blueprint('notification_bp', __name__)

@notification_bp.route('', methods=['GET'])
@token_required
def get_notifications(current_user):
    """GET /api/notifications — List notifications."""
    return notif_ctrl.get_user_notifications(current_user)

@notification_bp.route('/<int:notif_id>/read', methods=['PATCH'])
@token_required
def mark_notification_read(current_user, notif_id):
    """PATCH /api/notifications/<id>/read — Mark notification read."""
    return notif_ctrl.mark_notification_read(current_user, notif_id)

@notification_bp.route('/read-all', methods=['PATCH'])
@token_required
def mark_all_read(current_user):
    """PATCH /api/notifications/read-all — Mark all notifications read."""
    return notif_ctrl.mark_all_read(current_user)
