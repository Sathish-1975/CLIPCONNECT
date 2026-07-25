"""
============================================================
ClipConnect - Notification Controller
============================================================
Handles fetching and updating user notifications.
============================================================
"""

from database import db
from models.notification_model import Notification
from utils.response_helper import success_response, error_response

def get_user_notifications(current_user: dict):
    """
    GET /api/notifications
    Get all notifications for current user with unread count.
    """
    user_id = current_user['user_id']
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(50).all()
    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()

    notifs_data = [n.to_dict() for n in notifications]
    return success_response(data={
        'notifications': notifs_data,
        'unread_count': unread_count
    }, message=f"Fetched {len(notifs_data)} notifications.")


def mark_notification_read(current_user: dict, notif_id: int):
    """
    PATCH /api/notifications/<id>/read
    Mark a single notification as read.
    """
    notif = Notification.query.get(notif_id)
    if not notif or notif.user_id != current_user['user_id']:
        return error_response(message="Notification not found.", status_code=404)

    notif.is_read = True
    try:
        db.session.commit()
        return success_response(data={'notification': notif.to_dict()}, message="Notification marked as read.")
    except Exception as e:
        db.session.rollback()
        return error_response(message=f"Failed to update notification: {str(e)}", status_code=500)


def mark_all_read(current_user: dict):
    """
    PATCH /api/notifications/read-all
    Mark all notifications for current user as read.
    """
    user_id = current_user['user_id']
    try:
        Notification.query.filter_by(user_id=user_id, is_read=False).update({Notification.is_read: True})
        db.session.commit()
        return success_response(message="All notifications marked as read.")
    except Exception as e:
        db.session.rollback()
        return error_response(message=f"Failed to update notifications: {str(e)}", status_code=500)
