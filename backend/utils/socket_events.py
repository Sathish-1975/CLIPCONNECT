"""
============================================================
ClipConnect - WebSocket Event Handlers (Flask-SocketIO)
============================================================
Why this file exists:
  Manages real-time WebSockets for instant chat messages, typing status,
  online/offline user presence, and read receipts.

Key Events:
  - `connect`: Validates JWT token, joins user-specific room `user_<id>`, marks user online.
  - `disconnect`: Marks user offline, notifies contacts.
  - `send_message`: Relays new message payload to receiver's room instantly.
  - `typing_start` / `typing_stop`: Relays live typing status to target recipient.
  - `mark_read`: Emits read status event to sender.
============================================================
"""

import logging
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room
from utils.jwt_helper import decode_token

logger = logging.getLogger(__name__)
socketio = SocketIO(cors_allowed_origins="*")

# Store connected user sockets: { user_id: set(sid1, sid2, ...) }
user_sockets = {}

def init_socketio(app):
    """Binds SocketIO to the Flask app."""
    socketio.init_app(app)
    logger.info("[OK] Flask-SocketIO initialized.")
    return socketio


@socketio.on('connect')
def handle_connect(auth=None):
    """
    Client connection handler.
    Expects JWT token in auth dict: { 'token': '<jwt_token>' }
    """
    token = None
    if auth and isinstance(auth, dict):
        token = auth.get('token')
    elif request.args.get('token'):
        token = request.args.get('token')

    if not token:
        logger.warning("[SOCKET] Connection refused: missing token.")
        return False  # Reject connection

    payload, err_msg, status_code = decode_token(token)
    if not payload:
        logger.warning(f"[SOCKET] Connection refused: invalid token ({err_msg}).")
        return False

    user_id = payload.get('user_id')
    sid = request.sid

    if user_id not in user_sockets:
        user_sockets[user_id] = set()
    user_sockets[user_id].add(sid)

    # Join private room for this user
    room_name = f"user_{user_id}"
    join_room(room_name)

    logger.info(f"[SOCKET] User {user_id} connected (SID: {sid}, Room: {room_name})")

    # Broadcast online status
    emit('user_online', {'user_id': user_id, 'status': 'online'}, broadcast=True)


@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnect handler."""
    sid = request.sid
    disconnected_user = None

    for uid, sids in list(user_sockets.items()):
        if sid in sids:
            sids.remove(sid)
            if not sids:
                del user_sockets[uid]
                disconnected_user = uid
            break

    if disconnected_user:
        logger.info(f"[SOCKET] User {disconnected_user} went offline.")
        emit('user_offline', {'user_id': disconnected_user, 'status': 'offline'}, broadcast=True)


@socketio.on('typing_start')
def handle_typing_start(data):
    """Relays typing indicator to receiver."""
    receiver_id = data.get('receiver_id')
    sender_id = data.get('sender_id')

    if receiver_id:
        emit('user_typing', {
            'sender_id': sender_id,
            'is_typing': True
        }, room=f"user_{receiver_id}")


@socketio.on('typing_stop')
def handle_typing_stop(data):
    """Relays stopped typing indicator to receiver."""
    receiver_id = data.get('receiver_id')
    sender_id = data.get('sender_id')

    if receiver_id:
        emit('user_typing', {
            'sender_id': sender_id,
            'is_typing': False
        }, room=f"user_{receiver_id}")


@socketio.on('send_chat_message')
def handle_socket_message(data):
    """
    Direct Socket message relay.
    Data format: { receiver_id, sender_id, message }
    """
    receiver_id = data.get('receiver_id')
    message_payload = data.get('message')

    if receiver_id and message_payload:
        # Emit to recipient's room
        emit('receive_chat_message', message_payload, room=f"user_{receiver_id}")
