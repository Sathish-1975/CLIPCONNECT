"""
============================================================
ClipConnect - JWT (JSON Web Token) Helper
============================================================
Purpose:
    Provides utility functions for creating and verifying JWT tokens.
    JWT tokens are how we implement stateless authentication.

How JWT Authentication Works:
    1. User logs in with email + password
    2. Server verifies credentials
    3. Server generates a signed JWT token containing user info
    4. Client stores token (localStorage)
    5. Client sends token in every request header: Authorization: Bearer <token>
    6. Server verifies the token signature and extracts user info
    7. If valid, the request is processed; otherwise 401 Unauthorized

Token Structure:
    Header:  { "alg": "HS256", "typ": "JWT" }
    Payload: { "user_id": 1, "email": "...", "role": "client", "exp": ... }
    Signature: HMAC-SHA256(header.payload, SECRET_KEY)

Usage:
    from utils.jwt_helper import generate_token, decode_token

    token = generate_token(user_id=1, email="a@b.com", role="client")
    payload = decode_token(token)
============================================================
"""

import jwt
from datetime import datetime, timezone, timedelta
from flask import current_app


def generate_token(user_id, email, role, expires_in=None):
    """
    Generate a signed JWT access token for an authenticated user.
    
    Args:
        user_id (int): The user's database ID
        email (str): The user's email address
        role (str): The user's role ('client', 'editor', 'admin')
        expires_in (timedelta|None): Custom expiry, defaults to config setting
    
    Returns:
        str: Encoded JWT token string
    
    Example:
        token = generate_token(1, "john@example.com", "client")
        # Returns: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    """
    # Use config expiry or provided one
    if expires_in is None:
        expires_in = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', timedelta(hours=1))

    # Token payload (what's stored inside the token)
    payload = {
        # Standard JWT Claims
        'iat': datetime.now(timezone.utc),                      # Issued At
        'exp': datetime.now(timezone.utc) + expires_in,         # Expiration
        
        # Custom ClipConnect Claims
        'sub': str(user_id),    # Subject (user ID as string)
        'user_id': user_id,     # Easy access to user ID
        'email': email,         # User email (for display)
        'role': role,           # Role for frontend routing decisions
    }

    # Sign the token with the secret key
    secret_key = current_app.config.get('JWT_SECRET_KEY')
    token = jwt.encode(payload, secret_key, algorithm='HS256')

    return token


def decode_token(token):
    """
    Decode and verify a JWT token.
    
    Args:
        token (str): JWT token string from Authorization header
    
    Returns:
        dict: Decoded payload if token is valid
    
    Raises:
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid/tampered
    
    Example:
        payload = decode_token(token)
        user_id = payload['user_id']
        role = payload['role']
    """
    secret_key = current_app.config.get('JWT_SECRET_KEY')
    
    # Decode and verify in one step
    payload = jwt.decode(
        token,
        secret_key,
        algorithms=['HS256'],
        options={'verify_exp': True}  # Always verify expiration
    )
    
    return payload


def extract_token_from_header(request):
    """
    Extract JWT token from the Authorization header.
    
    Expected header format: "Authorization: Bearer <token>"
    
    Args:
        request: Flask request object
    
    Returns:
        str|None: The token string, or None if not found/malformed
    
    Example:
        token = extract_token_from_header(request)
        if not token:
            return error_response("Token missing", 401)
    """
    auth_header = request.headers.get('Authorization', '')

    if not auth_header:
        # Fallback to query param (e.g. for GET downloads via href)
        return request.args.get('token')

    parts = auth_header.split()

    # Must be "Bearer <token>" - exactly 2 parts
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return request.args.get('token')

    return parts[1]


def get_token_expiry_seconds(expires_in=None):
    """
    Returns token expiry time in seconds.
    Useful for frontend to know when to refresh the token.
    
    Args:
        expires_in (timedelta|None): Custom expiry
    
    Returns:
        int: Number of seconds until expiry
    """
    if expires_in is None:
        expires_in = timedelta(hours=1)
    return int(expires_in.total_seconds())
