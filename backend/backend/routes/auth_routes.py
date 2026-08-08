"""
============================================================
ClipConnect - Authentication Routes
============================================================
Purpose:
    Defines all URL routes related to user authentication.
    Uses Flask Blueprint for modular route organization.

Endpoints:
    POST /api/auth/register    --> Register a new user
    POST /api/auth/login       --> Login and get JWT token
    GET  /api/auth/me          --> Get current user profile (protected)
    GET  /api/auth/health      --> Health check for auth service

Blueprint Name: 'auth'
URL Prefix (set in routes/__init__.py): /api/auth

Why Blueprint?
    Blueprints group related routes together.
    Prevents all routes from living in one giant file.
    Makes it easy to add versioning (/api/v2/auth) later.
============================================================
"""

from flask import Blueprint

from controllers.auth_controller import (
    register_user,
    login_user,
    get_current_user
)
from middleware.auth_middleware import token_required


# Create the authentication Blueprint
# Name 'auth' is used internally by Flask for url_for() etc.
auth_bp = Blueprint('auth', __name__)


# ============================================================
# Route: Health Check
# ============================================================

@auth_bp.route('/health', methods=['GET'])
def auth_health():
    """
    GET /api/auth/health
    ====================
    Simple health check to verify the auth service is running.
    Useful for deployment monitoring and debugging.

    Response:
        { "status": "ok", "service": "auth" }
    """
    from utils.response_helper import success_response
    return success_response(
        data={"service": "auth", "status": "ok"},
        message="Auth service is running."
    )


# ============================================================
# Route: Register
# ============================================================

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    POST /api/auth/register
    =======================
    Register a new user account.

    Body: { full_name, email, password, role }

    Delegates to: controllers/auth_controller.py > register_user()
    """
    return register_user()


# ============================================================
# Route: Login
# ============================================================

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /api/auth/login
    ====================
    Authenticate user and return JWT token.

    Body: { email, password }

    Delegates to: controllers/auth_controller.py > login_user()
    """
    return login_user()


# ============================================================
# Route: Get Current User (Protected)
# ============================================================

@auth_bp.route('/me', methods=['GET'])
@token_required
def me(current_user):
    """
    GET /api/auth/me
    ================
    Returns the profile of the currently authenticated user.

    Headers Required:
        Authorization: Bearer <jwt_token>

    The @token_required decorator:
        - Validates the JWT token
        - Extracts user info from token payload
        - Passes it as current_user to this function

    Delegates to: controllers/auth_controller.py > get_current_user()
    """
    return get_current_user(current_user)
