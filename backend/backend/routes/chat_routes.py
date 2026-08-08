"""
============================================================
ClipConnect - Chat Routes Blueprint
============================================================
Why this file exists:
  Exposes REST endpoints for real-time messaging, conversation management,
  and message actions (pinning, unreading, upload attachments).

Endpoints:
  GET   /api/chat/conversations        -> Get user's active conversations
  GET   /api/chat/messages/<user_id>   -> Get message history with user
  POST  /api/chat/messages             -> Send chat message
  PATCH /api/chat/messages/<id>/pin    -> Toggle pin status on a message
============================================================
"""

from flask import Blueprint
from middleware.auth_middleware import token_required as jwt_required
from controllers.chat_controller import (
    get_conversations,
    get_chat_history,
    send_chat_message,
    toggle_pin_message
)

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/conversations', methods=['GET'])
@jwt_required
def conversations_route(current_user):
    return get_conversations(current_user)

@chat_bp.route('/messages/<int:other_user_id>', methods=['GET'])
@jwt_required
def chat_history_route(current_user, other_user_id):
    return get_chat_history(current_user, other_user_id)

@chat_bp.route('/messages', methods=['POST'])
@jwt_required
def send_message_route(current_user):
    return send_chat_message(current_user)

@chat_bp.route('/messages/<int:message_id>/pin', methods=['PATCH'])
@jwt_required
def pin_message_route(current_user, message_id):
    return toggle_pin_message(current_user, message_id)
