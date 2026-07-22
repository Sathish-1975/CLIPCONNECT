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
============================================================
"""

from flask import Blueprint
from middleware.auth_middleware import token_required, editor_required
import controllers.user_controller as user_ctrl
import controllers.search_controller as search_ctrl

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
