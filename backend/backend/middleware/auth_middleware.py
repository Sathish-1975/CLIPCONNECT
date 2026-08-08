"""
============================================================
ClipConnect - Authentication Middleware
============================================================
Purpose:
    Provides route-protection decorators using JWT.
    Any route decorated with @token_required will:
        1. Check for a valid Authorization header
        2. Decode and verify the JWT token
        3. Attach the current user's data to the request
        4. Reject the request with 401/403 if invalid

How Python decorators work here:
    @token_required wraps the route function.
    Before the real function runs, the wrapper validates the token.
    If valid, it passes current_user data as a keyword argument.

Usage:
    from middleware.auth_middleware import token_required

    @app.route('/api/protected')
    @token_required
    def protected_route(current_user):
        return jsonify({"user": current_user['email']})
============================================================
"""

import jwt
from functools import wraps
from flask import request

from utils.jwt_helper import extract_token_from_header, decode_token
from utils.response_helper import error_response


def token_required(f):
    """
    Decorator: Protects a route by requiring a valid JWT token.
    
    How to use:
        @blueprint.route('/profile', methods=['GET'])
        @token_required
        def get_profile(current_user):
            # current_user contains: { user_id, email, role }
            return success_response(data=current_user)
    
    Responses:
        401: Token missing or malformed
        401: Token has expired
        401: Token is invalid/tampered
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Step 1: Extract token from "Authorization: Bearer <token>" header
        token = extract_token_from_header(request)

        if not token:
            return error_response(
                message="Authentication token is missing. Please login.",
                status_code=401
            )

        # Step 2: Decode and verify the token
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return error_response(
                message="Your session has expired. Please login again.",
                status_code=401
            )
        except jwt.InvalidTokenError as e:
            return error_response(
                message=f"Invalid authentication token: {str(e)}",
                status_code=401
            )
        except Exception as e:
            return error_response(
                message="Token verification failed. Please login again.",
                status_code=401
            )

        # Step 3: Attach current_user info to the function call
        current_user = {
            'user_id': payload.get('user_id'),
            'email': payload.get('email'),
            'role': payload.get('role')
        }

        # Pass current_user as first positional argument to the route function
        return f(current_user, *args, **kwargs)

    return decorated


def admin_required(f):
    """
    Decorator: Requires the user to be both authenticated AND have 'admin' role.
    
    Stacks on top of token_required:
        The route gets: current_user with role='admin'
    
    Responses:
        401: No valid token
        403: Token valid but role is not 'admin'
    
    Usage:
        @blueprint.route('/admin/users', methods=['GET'])
        @admin_required
        def list_all_users(current_user):
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Step 1: Extract and validate token (same as token_required)
        token = extract_token_from_header(request)

        if not token:
            return error_response(
                message="Authentication token is missing. Please login.",
                status_code=401
            )

        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return error_response(
                message="Your session has expired. Please login again.",
                status_code=401
            )
        except jwt.InvalidTokenError:
            return error_response(
                message="Invalid authentication token.",
                status_code=401
            )

        # Step 2: Check admin role
        if payload.get('role') != 'admin':
            return error_response(
                message="Access denied. Admin privileges required.",
                status_code=403
            )

        current_user = {
            'user_id': payload.get('user_id'),
            'email': payload.get('email'),
            'role': payload.get('role')
        }

        return f(current_user, *args, **kwargs)

    return decorated


def editor_required(f):
    """
    Decorator: Requires the user to be authenticated AND have 'editor' role.
    
    Usage:
        @blueprint.route('/gigs/create', methods=['POST'])
        @editor_required
        def create_gig(current_user):
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = extract_token_from_header(request)

        if not token:
            return error_response(
                message="Authentication token is missing. Please login.",
                status_code=401
            )

        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return error_response(message="Session expired. Please login again.", status_code=401)
        except jwt.InvalidTokenError:
            return error_response(message="Invalid token.", status_code=401)

        if payload.get('role') != 'editor':
            return error_response(
                message="Access denied. Editor role required.",
                status_code=403
            )

        current_user = {
            'user_id': payload.get('user_id'),
            'email': payload.get('email'),
            'role': payload.get('role')
        }

        return f(current_user, *args, **kwargs)

    return decorated
