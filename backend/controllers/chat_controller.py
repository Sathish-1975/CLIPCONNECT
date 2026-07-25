"""
============================================================
ClipConnect - Chat Controller
============================================================
Why this file exists:
  Provides controller logic for one-to-one messaging, conversation listing, message attachments,
  read receipts, and message pinning.

What it does:
  - `get_conversations()`: Fetches recent active chat partners with unread message badges.
  - `get_chat_history()`: Fetches full paginated message history between two users.
  - `send_message()`: REST endpoint to send chat messages with optional attachments or replies.
  - `mark_messages_read()`: Marks incoming messages from a user as read.
  - `toggle_pin()`: Toggles pinned state on a chat message.

How it integrates with the rest of the application:
  - Exposed via `/api/chat/*` in `chat_routes.py`.
  - Works alongside WebSocket handlers in `socket_events.py` for real-time delivery.
  - Interacts with `Message`, `MessageAttachment`, `User`, and `Project` models.
============================================================
"""

from flask import request, current_app
from database import db
from models.user_model import User
from models.message_model import Message, MessageAttachment
from utils.response_helper import success_response, error_response
from utils.notification_helper import create_notification


def get_conversations(current_user: dict):
    """
    GET /api/chat/conversations
    Returns recent unique chat contacts for current user with unread counts.
    """
    user_id = current_user['user_id']

    # Query distinct sender/receiver combinations
    sent_receivers = db.session.query(Message.receiver_id).filter_by(sender_id=user_id).distinct()
    rec_senders    = db.session.query(Message.sender_id).filter_by(receiver_id=user_id).distinct()

    contact_ids = set([r[0] for r in sent_receivers] + [s[0] for s in rec_senders])
    contacts = []

    for cid in contact_ids:
        contact_user = User.query.get(cid)
        if not contact_user or not contact_user.is_active:
            continue

        last_msg = Message.query.filter(
            ((Message.sender_id == user_id) & (Message.receiver_id == cid)) |
            ((Message.sender_id == cid) & (Message.receiver_id == user_id))
        ).order_by(Message.created_at.desc()).first()

        unread_count = Message.query.filter_by(sender_id=cid, receiver_id=user_id, is_read=False).count()

        contacts.append({
            'contact_id':   contact_user.id,
            'full_name':    contact_user.full_name,
            'role':         contact_user.role.value,
            'unread_count': unread_count,
            'last_message': last_msg.to_dict() if last_msg else None,
        })

    # Sort contacts by last message timestamp descending
    contacts.sort(key=lambda x: x['last_message']['created_at'] if x['last_message'] else '', reverse=True)

    return success_response(data={'conversations': contacts}, message=f"Fetched {len(contacts)} chat conversations.")


def get_chat_history(current_user: dict, other_user_id: int):
    """
    GET /api/chat/messages/<other_user_id>
    Fetches full message history between current user and other_user_id.
    """
    user_id = current_user['user_id']
    other_user = User.query.get(other_user_id)
    if not other_user:
        return error_response(message="User not found.", status_code=404)

    page     = max(1, request.args.get('page', 1, type=int))
    per_page = min(100, max(1, request.args.get('per_page', 50, type=int)))

    messages = Message.query.filter(
        ((Message.sender_id == user_id) & (Message.receiver_id == other_user_id)) |
        ((Message.sender_id == other_user_id) & (Message.receiver_id == user_id))
    ).order_by(Message.created_at.asc()).all()

    msg_data = [m.to_dict() for m in messages]

    # Auto-mark unread incoming messages as read
    Message.query.filter_by(sender_id=other_user_id, receiver_id=user_id, is_read=False).update({Message.is_read: True})
    db.session.commit()

    return success_response(
        data={
            'contact': {
                'id':        other_user.id,
                'full_name': other_user.full_name,
                'role':      other_user.role.value,
            },
            'messages': msg_data,
            'total':    len(msg_data),
        },
        message="Chat history loaded."
    )


def send_chat_message(current_user: dict):
    """
    POST /api/chat/messages
    Body: { receiver_id, content, project_id (optional), reply_to_id (optional), message_type, attachments (optional) }
    """
    user_id = current_user['user_id']
    data    = request.get_json(silent=True) or {}

    receiver_id = data.get('receiver_id')
    content     = (data.get('content') or '').strip()
    msg_type    = data.get('message_type', 'text')
    project_id  = data.get('project_id')
    reply_to_id = data.get('reply_to_id')
    attachments = data.get('attachments') or []

    if not receiver_id:
        return error_response(message="receiver_id is required.", status_code=422)

    receiver = User.query.get(receiver_id)
    if not receiver or not receiver.is_active:
        return error_response(message="Recipient user not found.", status_code=404)

    if not content and not attachments:
        return error_response(message="Message content or attachments required.", status_code=422)

    msg = Message(
        sender_id=user_id,
        receiver_id=receiver_id,
        project_id=project_id,
        reply_to_id=reply_to_id,
        content=content,
        message_type=msg_type
    )

    try:
        db.session.add(msg)
        db.session.flush()

        # Save attachments if any
        for att in attachments:
            attachment_obj = MessageAttachment(
                message_id=msg.id,
                file_url=att.get('file_url', ''),
                file_type=att.get('file_type', 'file'),
                file_name=att.get('file_name', 'attachment'),
                file_size=att.get('file_size', 0)
            )
            db.session.add(attachment_obj)

        db.session.commit()

        # Send notification to recipient
        sender = User.query.get(user_id)
        sender_name = sender.full_name if sender else 'Someone'
        create_notification(
            user_id=receiver_id,
            title=f"💬 New Message from {sender_name}",
            message=content[:80] if content else "Sent you an attachment",
            type_str="general",
            related_project_id=project_id
        )

        return success_response(
            data={'message': msg.to_dict()},
            message="Message sent successfully.",
            status_code=201
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Send chat message error: {e}")
        return error_response(message=f"Failed to send message: {str(e)}", status_code=500)


def toggle_pin_message(current_user: dict, message_id: int):
    """
    PATCH /api/chat/messages/<message_id>/pin
    Toggles pinned status on a message.
    """
    msg = Message.query.get(message_id)
    if not msg:
        return error_response(message="Message not found.", status_code=404)

    user_id = current_user['user_id']
    if msg.sender_id != user_id and msg.receiver_id != user_id:
        return error_response(message="Access denied.", status_code=403)

    msg.is_pinned = not msg.is_pinned
    db.session.commit()

    return success_response(data={'message': msg.to_dict()}, message=f"Message {'pinned' if msg.is_pinned else 'unpinned'}.")
