"""
============================================================
ClipConnect - Notification Helper
============================================================
Utility module to easily create and dispatch user notifications.
============================================================
"""

from database import db
from models.notification_model import Notification

def create_notification(user_id: int, title: str, message: str, type_str: str = 'general', related_project_id: int = None):
    """
    Creates and commits a new Notification record for a user.
    """
    try:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type_str,
            related_project_id=related_project_id
        )
        db.session.add(notif)
        db.session.commit()
        return notif
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Failed to create notification for user {user_id}: {str(e)}")
        return None
