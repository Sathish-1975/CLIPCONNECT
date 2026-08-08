"""
============================================================
ClipConnect - Simplified API Routes
============================================================
Blueprint: api_bp
URL Prefix: /api

Provides simplified REST API endpoints as requested:

Public:
    GET  /api/editors              → list all editors
    GET  /api/editors/{id}         → get single editor by ID
    GET  /api/categories           → get all editor categories
    GET  /api/search               → search editors
    GET  /api/filter               → filter editors

Protected (JWT required):
    POST   /api/editor/profile     → create editor profile
    PUT    /api/editor/profile     → update editor profile
    DELETE /api/editor/profile     → delete editor profile

    POST   /api/hire               → submit hire request
    PUT    /api/hire/accept        → accept hire invitation
    PUT    /api/hire/reject        → reject hire invitation

    POST   /api/reviews            → create a review
    GET    /api/reviews/<id>       → get reviews for an editor

    POST   /api/favorites          → add favorite editor
    GET    /api/favorites           → list favorites
    DELETE /api/favorites/<id>     → remove favorite editor

    GET    /api/notifications      → (handled by notification_bp)
    PUT    /api/notifications/read → mark all notifications read

    POST   /api/uploads            → general file upload
============================================================
"""

from flask import Blueprint, request
from middleware.auth_middleware import token_required, editor_required
import controllers.user_controller as user_ctrl
import controllers.search_controller as search_ctrl
import controllers.hire_controller as hire_ctrl
import controllers.review_controller as review_ctrl
import controllers.client_controller as client_ctrl

api_bp = Blueprint('api', __name__)


# ============================================================
# Public Editor Endpoints
# ============================================================

@api_bp.route('/editors', methods=['GET'])
def list_editors():
    """GET /api/editors — List all editors with filters and pagination."""
    return user_ctrl.list_editors()


@api_bp.route('/editors/<int:editor_id>', methods=['GET'])
def get_editor(editor_id):
    """GET /api/editors/{id} — Get single editor by ID."""
    return user_ctrl.get_editor_public(editor_id)


# ============================================================
# Categories Endpoint
# ============================================================

@api_bp.route('/categories', methods=['GET'])
def get_categories():
    """GET /api/categories — Get all available editor categories."""
    from models.editor_profile_model import EditorCategory
    from utils.response_helper import success_response
    
    categories = [
        {
            'value': cat.value,
            'label': cat.value.replace('_', ' ').title()
        }
        for cat in EditorCategory
    ]
    
    return success_response(
        data=categories,
        message="Categories retrieved successfully"
    )


# ============================================================
# Search Endpoint
# ============================================================

@api_bp.route('/search', methods=['GET'])
def search_editors():
    """GET /api/search — Search editors by query string."""
    return search_ctrl.suggest_search()


# ============================================================
# Filter Endpoint
# ============================================================

@api_bp.route('/filter', methods=['GET'])
def filter_editors():
    """GET /api/filter — Filter editors with advanced parameters."""
    # This uses the same controller as list_editors since filtering is built in
    return user_ctrl.list_editors()


# ============================================================
# Protected Editor Profile Endpoints (Editor Only)
# ============================================================

@api_bp.route('/editor/profile', methods=['POST'])
@editor_required
def create_editor_profile(current_user):
    """POST /api/editor/profile — Create editor profile (editors only)."""
    return user_ctrl.setup_editor_profile(current_user)


@api_bp.route('/editor/profile', methods=['PUT'])
@editor_required
def update_editor_profile(current_user):
    """PUT /api/editor/profile — Update editor profile (editors only)."""
    return user_ctrl.update_my_profile(current_user)


@api_bp.route('/editor/profile', methods=['DELETE'])
@editor_required
def delete_editor_profile(current_user):
    """DELETE /api/editor/profile — Delete editor profile (editors only)."""
    from models.editor_profile_model import EditorProfile
    from models.user_model import User, UserRole
    from utils.response_helper import success_response, error_response
    from database import db
    
    user = User.query.get(current_user['user_id'])
    if not user or not user.is_active:
        return error_response(message='User not found or inactive.', status_code=404)
    
    profile = EditorProfile.query.filter_by(user_id=user.id).first()
    if not profile:
        return error_response(message='Editor profile not found.', status_code=404)
    
    try:
        # Delete the profile
        db.session.delete(profile)
        
        # Change user role back to client
        user.role = UserRole.CLIENT
        
        db.session.commit()
        
        return success_response(
            message="Editor profile deleted successfully"
        )
    except Exception as e:
        db.session.rollback()
        return error_response(
            message=f"Failed to delete profile: {str(e)}",
            status_code=500
        )


# ============================================================
# Hire Endpoints
# ============================================================

@api_bp.route('/hire', methods=['POST'])
@token_required
def submit_hire(current_user):
    """POST /api/hire — Client sends hire invitation to editor."""
    return hire_ctrl.submit_hire_request(current_user)


@api_bp.route('/hire/accept', methods=['PUT'])
@token_required
def accept_hire(current_user):
    """PUT /api/hire/accept — Editor accepts a hire invitation."""
    return hire_ctrl.accept_hire(current_user)


@api_bp.route('/hire/reject', methods=['PUT'])
@token_required
def reject_hire(current_user):
    """PUT /api/hire/reject — Editor rejects a hire invitation."""
    return hire_ctrl.reject_hire(current_user)


# ============================================================
# Review Endpoints
# ============================================================

@api_bp.route('/reviews', methods=['POST'])
@token_required
def create_review(current_user):
    """POST /api/reviews — Client submits a review for an editor."""
    return review_ctrl.create_review(current_user)


@api_bp.route('/reviews/<int:editor_id>', methods=['GET'])
def get_editor_reviews(editor_id):
    """GET /api/reviews/{editor_id} — Get all reviews for an editor."""
    return review_ctrl.get_editor_reviews(editor_id)


# ============================================================
# Favorites Endpoints (simplified aliases)
# ============================================================

@api_bp.route('/favorites', methods=['GET'])
@token_required
def list_favorites(current_user):
    """GET /api/favorites — List favorite editors."""
    return client_ctrl.get_favorites(current_user)


@api_bp.route('/favorites', methods=['POST'])
@token_required
def add_favorite(current_user):
    """POST /api/favorites — Add editor to favorites. Body: { editor_id }."""
    data = request.get_json(silent=True) or {}
    editor_id = data.get('editor_id')
    if not editor_id:
        from utils.response_helper import error_response
        return error_response(message="editor_id is required.", status_code=422)
    return client_ctrl.add_favorite(current_user, int(editor_id))


@api_bp.route('/favorites/<int:editor_id>', methods=['DELETE'])
@token_required
def remove_favorite(current_user, editor_id):
    """DELETE /api/favorites/{editor_id} — Remove editor from favorites."""
    return client_ctrl.remove_favorite(current_user, editor_id)


# ============================================================
# Notifications Alias
# ============================================================

@api_bp.route('/notifications/read', methods=['PUT'])
@token_required
def mark_notifications_read(current_user):
    """PUT /api/notifications/read — Mark all notifications as read."""
    import controllers.notification_controller as notif_ctrl
    return notif_ctrl.mark_all_read(current_user)


# ============================================================
# General Uploads Endpoint
# ============================================================

@api_bp.route('/uploads', methods=['POST'])
@token_required
def general_upload(current_user):
    """
    POST /api/uploads — Upload a file.
    Form data:
      - file: the file to upload (required)
      - folder: destination folder (optional, default: 'general')
                allowed: avatars, banners, resumes, portfolio/images, project_samples, general
    """
    from utils.upload_helper import save_upload, get_upload_url, UPLOAD_CONFIG, UPLOAD_BASE
    from utils.response_helper import success_response, error_response
    import os

    file = request.files.get('file')
    if not file:
        return error_response(message="No file uploaded. Send a 'file' field.", status_code=400)

    folder = (request.form.get('folder') or 'general').strip().lower()

    # Allow 'general' and 'project_samples' as extra folders
    allowed_extras = {'general', 'project_samples'}
    if folder not in UPLOAD_CONFIG and folder not in allowed_extras:
        valid_folders = list(UPLOAD_CONFIG.keys()) + list(allowed_extras)
        return error_response(
            message=f"Invalid folder. Must be one of: {', '.join(valid_folders)}",
            status_code=422
        )

    # For extra folders, configure on-the-fly
    if folder in allowed_extras and folder not in UPLOAD_CONFIG:
        UPLOAD_CONFIG[folder] = {
            'extensions': {'jpg', 'jpeg', 'png', 'webp', 'gif', 'pdf', 'doc', 'docx', 'mp4', 'mov', 'zip'},
            'max_mb': 50,
            'path': os.path.join(UPLOAD_BASE, folder),
        }

    try:
        filename = save_upload(file, folder)
        url = get_upload_url(filename, folder)
        return success_response(
            data={
                'filename': filename,
                'url': url,
                'folder': folder,
            },
            message="File uploaded successfully.",
            status_code=201
        )
    except ValueError as ve:
        return error_response(message=str(ve), status_code=422)
    except Exception as e:
        return error_response(message=f"Upload failed: {str(e)}", status_code=500)
