"""
============================================================
ClipConnect - User / Editor Profile Routes
============================================================
Blueprint: user_bp
URL Prefix: /api/users

Public:
    GET  /api/users/editors              → list editors
    GET  /api/users/editors/<user_id>    → single editor public profile

Protected (JWT required):
    POST   /api/users/me/profile                 → create profile
    GET    /api/users/me/profile                 → get own profile
    PUT    /api/users/me/profile                 → update profile
    POST   /api/users/me/avatar                  → upload photo
    POST   /api/users/me/banner                  → upload banner
    POST   /api/users/me/resume                  → upload resume
    POST   /api/users/me/portfolio/image         → add portfolio image
    POST   /api/users/me/portfolio/video         → add portfolio video
    DELETE /api/users/me/portfolio/image/<index> → remove image
    DELETE /api/users/me/portfolio/video/<index> → remove video

Static:
    GET /uploads/<path>                  → serve uploaded files
============================================================
"""

from flask import Blueprint, send_from_directory
from middleware.auth_middleware import token_required
import controllers.user_controller as user_ctrl
from utils.upload_helper import UPLOAD_BASE

user_bp = Blueprint('users', __name__)


# ============================================================
# Serve Uploaded Files
# ============================================================

@user_bp.route('/uploads/<path:filepath>', methods=['GET'])
def serve_upload(filepath):
    """Serve any uploaded file by path, e.g. /uploads/avatars/file.jpg"""
    return send_from_directory(UPLOAD_BASE, filepath)


# ============================================================
# Public Routes
# ============================================================

@user_bp.route('/editors', methods=['GET'])
def editors_list():
    """GET /api/users/editors — Browse editors with filters + pagination."""
    return user_ctrl.list_editors()


@user_bp.route('/editors/<int:user_id>', methods=['GET'])
def editor_public(user_id):
    """GET /api/users/editors/<user_id> — Public editor profile."""
    return user_ctrl.get_editor_public(user_id)


# ============================================================
# Profile Management
# ============================================================

@user_bp.route('/me/profile', methods=['POST'])
@token_required
def create_profile(current_user):
    """POST — Create / initialise editor profile."""
    return user_ctrl.setup_editor_profile(current_user)


@user_bp.route('/me/profile', methods=['GET'])
@token_required
def my_profile(current_user):
    """GET — Fetch own profile (private view, all fields)."""
    return user_ctrl.get_my_profile(current_user)


@user_bp.route('/me/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """PUT — Partial update profile text/enum/array fields."""
    return user_ctrl.update_my_profile(current_user)


# ============================================================
# File Uploads
# ============================================================

@user_bp.route('/me/avatar', methods=['POST'])
@token_required
def avatar_upload(current_user):
    """POST — Upload / replace profile photo. Field: 'avatar'."""
    return user_ctrl.upload_avatar(current_user)


@user_bp.route('/me/banner', methods=['POST'])
@token_required
def banner_upload(current_user):
    """POST — Upload / replace cover banner. Field: 'banner'."""
    return user_ctrl.upload_banner(current_user)


@user_bp.route('/me/resume', methods=['POST'])
@token_required
def resume_upload(current_user):
    """POST — Upload / replace resume file. Field: 'resume'."""
    return user_ctrl.upload_resume(current_user)


# ============================================================
# Portfolio
# ============================================================

@user_bp.route('/me/portfolio/image', methods=['POST'])
@token_required
def portfolio_image_add(current_user):
    """POST — Upload portfolio image. Field: 'image'."""
    return user_ctrl.upload_portfolio_image(current_user)


@user_bp.route('/me/portfolio/video', methods=['POST'])
@token_required
def portfolio_video_add(current_user):
    """POST — Add portfolio video link. Body: { url, title, description }."""
    return user_ctrl.add_portfolio_video(current_user)


@user_bp.route('/me/portfolio/image/<int:index>', methods=['DELETE'])
@token_required
def portfolio_image_remove(current_user, index):
    """DELETE — Remove portfolio image by list index."""
    return user_ctrl.delete_portfolio_image(current_user, index)


@user_bp.route('/me/portfolio/video/<int:index>', methods=['DELETE'])
@token_required
def portfolio_video_remove(current_user, index):
    """DELETE — Remove portfolio video by list index."""
    return user_ctrl.delete_portfolio_video(current_user, index)


# ============================================================
# Client Dashboard Routes
# ============================================================

import controllers.client_controller as client_ctrl


@user_bp.route('/me/dashboard', methods=['GET'])
@token_required
def client_dashboard(current_user):
    """GET /api/users/me/dashboard — Full client dashboard data."""
    return client_ctrl.get_client_dashboard(current_user)


@user_bp.route('/me/account', methods=['PUT'])
@token_required
def account_settings(current_user):
    """PUT /api/users/me/account — Update name, email, password, profile fields."""
    return client_ctrl.update_account_settings(current_user)


@user_bp.route('/me/client-avatar', methods=['POST'])
@token_required
def client_avatar_upload(current_user):
    """POST /api/users/me/client-avatar — Upload client profile photo."""
    return client_ctrl.upload_client_avatar(current_user)


# ── Favorites ──────────────────────────────────────────────────

@user_bp.route('/me/favorites', methods=['GET'])
@token_required
def favorites_list(current_user):
    """GET — List all favorite editors with full snippets."""
    return client_ctrl.get_favorites(current_user)


@user_bp.route('/me/favorites/<int:editor_id>', methods=['POST'])
@token_required
def favorite_add(current_user, editor_id):
    """POST — Add an editor to favorites."""
    return client_ctrl.add_favorite(current_user, editor_id)


@user_bp.route('/me/favorites/<int:editor_id>', methods=['DELETE'])
@token_required
def favorite_remove(current_user, editor_id):
    """DELETE — Remove an editor from favorites."""
    return client_ctrl.remove_favorite(current_user, editor_id)


# ── Notifications ───────────────────────────────────────────────

@user_bp.route('/me/notifications', methods=['GET'])
@token_required
def notifications_list(current_user):
    """GET — All notifications (newest first) + unread count."""
    return client_ctrl.get_notifications(current_user)


@user_bp.route('/me/notifications/<notif_id>', methods=['PATCH'])
@token_required
def notification_read(current_user, notif_id):
    """PATCH — Mark a single notification as read."""
    return client_ctrl.mark_notification_read(current_user, notif_id)


@user_bp.route('/me/notifications/read-all', methods=['POST'])
@token_required
def notifications_read_all(current_user):
    """POST — Mark all notifications as read."""
    return client_ctrl.mark_all_notifications_read(current_user)


@user_bp.route('/me/notifications/prefs', methods=['PUT'])
@token_required
def notification_prefs(current_user):
    """PUT — Update notification preferences."""
    return client_ctrl.update_notification_prefs(current_user)


# ============================================================
# Editor Dashboard Routes
# ============================================================

import controllers.editor_dashboard_controller as editor_dash_ctrl


@user_bp.route('/me/editor-dashboard', methods=['GET'])
@token_required
def editor_dashboard(current_user):
    """GET /api/users/me/editor-dashboard — Full editor dashboard data."""
    return editor_dash_ctrl.get_editor_dashboard(current_user)


@user_bp.route('/me/availability', methods=['PUT'])
@token_required
def update_availability(current_user):
    """PUT /api/users/me/availability — Toggle availability status."""
    return editor_dash_ctrl.update_availability(current_user)


