"""
============================================================
ClipConnect - Authentication Controller
============================================================
Purpose:
    Handles all business logic for user authentication:
        - register_user(): Create a new user account
        - login_user(): Authenticate and return JWT
        - get_current_user(): Return logged-in user's profile

Architecture (MVC Pattern):
    Route (URL) --> Controller (Logic) --> Model (Database) --> Response

Why separate from routes?
    Routes only define URL patterns and HTTP methods.
    Controllers contain the actual logic.
    This makes code testable, reusable, and clean.

Flow for Register:
    1. Parse JSON body from request
    2. Validate all fields (utils/validators.py)
    3. Check if email already exists in DB
    4. Hash password with bcrypt
    5. Create User object and save to DB
    6. Return success response with user data

Flow for Login:
    1. Parse JSON body
    2. Validate fields
    3. Find user by email
    4. Verify password with bcrypt
    5. Generate JWT token
    6. Return token + user data
============================================================
"""

import bcrypt
from flask import request, current_app

from database import db
from models.user_model import User, UserRole
from utils.validators import validate_registration_data, validate_login_data
from utils.response_helper import success_response, error_response
from utils.jwt_helper import generate_token


# ============================================================
# Controller: Register User
# ============================================================

def register_user():
    """
    POST /api/auth/register
    =======================
    Registers a new user (client or editor) in ClipConnect.

    Request Body (JSON):
        {
            "full_name": "John Doe",
            "email": "john@example.com",
            "password": "Secret@123",
            "role": "client"          // or "editor"
        }

    Success Response (201):
        {
            "success": true,
            "message": "Account created successfully! Welcome to ClipConnect.",
            "data": {
                "user": { ...user fields (no password)... }
            }
        }

    Error Responses:
        422: Validation failed (field errors returned)
        409: Email already registered
        500: Database error
    """
    # Step 1: Parse incoming JSON request body
    data = request.get_json(silent=True)

    # Step 2: Validate all input fields
    validation_errors = validate_registration_data(data)
    if validation_errors:
        return error_response(
            message="Validation failed. Please fix the errors below.",
            status_code=422,
            errors=validation_errors
        )

    # Step 3: Normalize inputs
    full_name = data['full_name'].strip()
    email = data['email'].strip().lower()   # Always store email as lowercase
    password = data['password']
    role_str = data['role'].strip().lower()

    # Step 4: Check if email is already registered (must be unique)
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return error_response(
            message="This email address is already registered. Please login or use a different email.",
            status_code=409,   # 409 Conflict
            errors={"email": "Email already exists"}
        )

    # Step 5: Hash the password using bcrypt
    # bcrypt.hashpw() takes bytes, returns bytes
    # We decode to string for PostgreSQL VARCHAR storage
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)     # 12 rounds = strong but reasonable speed
    hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    # Step 6: Map role string to UserRole enum
    try:
        user_role = UserRole(role_str)
    except ValueError:
        return error_response(
            message="Invalid role specified.",
            status_code=400,
            errors={"role": f"Role must be 'client' or 'editor', got '{role_str}'"}
        )

    # Step 7: Create the User object (NOT yet saved to DB)
    new_user = User(
        full_name=full_name,
        email=email,
        password=hashed_password,
        role=user_role
    )

    # Step 8: Save to database (inside a try/except for safety)
    try:
        db.session.add(new_user)
        db.session.commit()

        current_app.logger.info(f"New user registered: {email} (role: {role_str})")

    except Exception as db_error:
        db.session.rollback()   # Undo any partial changes
        current_app.logger.error(f"Database error during registration: {str(db_error)}")
        return error_response(
            message="Registration failed due to a server error. Please try again.",
            status_code=500
        )

    # Step 9: Return success response (never include password in response!)
    return success_response(
        data={
            "user": new_user.to_dict()   # to_dict() excludes password by default
        },
        message=f"Welcome to ClipConnect, {full_name}! Your account has been created.",
        status_code=201   # 201 Created
    )


# ============================================================
# Controller: Login User
# ============================================================

def login_user():
    """
    POST /api/auth/login
    ====================
    Authenticates a user and returns a JWT access token.

    Request Body (JSON):
        {
            "email": "john@example.com",
            "password": "Secret@123"
        }

    Success Response (200):
        {
            "success": true,
            "message": "Login successful!",
            "data": {
                "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "Bearer",
                "expires_in": 3600,
                "user": { ...user fields... }
            }
        }

    Error Responses:
        422: Validation failed
        401: Invalid credentials (wrong email or password)
        403: Account deactivated
        500: Server error
    """
    # Step 1: Parse JSON body
    data = request.get_json(silent=True)

    # Step 2: Validate login inputs
    validation_errors = validate_login_data(data)
    if validation_errors:
        return error_response(
            message="Validation failed.",
            status_code=422,
            errors=validation_errors
        )

    # Step 3: Normalize email
    email = data['email'].strip().lower()
    password = data['password']

    # Step 4: Look up user by email
    user = User.query.filter_by(email=email).first()

    # SECURITY NOTE: Use the same generic error for "email not found" and
    # "wrong password". This prevents user enumeration attacks where an
    # attacker could discover which emails are registered.
    if not user:
        return error_response(
            message="Invalid email or password. Please check your credentials.",
            status_code=401
        )

    # Step 5: Check if account is active
    if not user.is_active:
        return error_response(
            message="Your account has been deactivated. Please contact support.",
            status_code=403
        )

    # Step 6: Verify password against stored bcrypt hash
    password_bytes = password.encode('utf-8')
    stored_hash = user.password.encode('utf-8')

    password_matches = bcrypt.checkpw(password_bytes, stored_hash)

    if not password_matches:
        current_app.logger.warning(f"Failed login attempt for email: {email}")
        return error_response(
            message="Invalid email or password. Please check your credentials.",
            status_code=401
        )

    # Step 7: Generate JWT access token
    token = generate_token(
        user_id=user.id,
        email=user.email,
        role=user.role.value    # Pass string value ('client', 'editor', 'admin')
    )

    # Step 8: Get token expiry time for frontend reference
    expires_in = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES')
    expires_seconds = int(expires_in.total_seconds()) if expires_in else 3600

    current_app.logger.info(f"Successful login: {email}")

    # Step 9: Return token + user data
    return success_response(
        data={
            "token": token,
            "token_type": "Bearer",
            "expires_in": expires_seconds,   # Seconds until token expires
            "user": user.to_dict()           # Full user object (no password)
        },
        message=f"Welcome back, {user.full_name}!",
        status_code=200
    )


# ============================================================
# Controller: Get Current User Profile
# ============================================================

def get_current_user(current_user):
    """
    GET /api/auth/me
    ================
    Returns the profile of the currently authenticated user.
    Requires: @token_required decorator on the route.

    Args:
        current_user (dict): Injected by @token_required middleware
                             Contains: { user_id, email, role }

    Success Response (200):
        {
            "success": true,
            "message": "Profile fetched successfully",
            "data": {
                "user": { ...full user object... }
            }
        }
    """
    # Fetch full user object from DB using ID from JWT payload
    user = User.query.get(current_user['user_id'])

    if not user:
        return error_response(
            message="User not found. The account may have been deleted.",
            status_code=404
        )

    if not user.is_active:
        return error_response(
            message="Account is deactivated.",
            status_code=403
        )

    return success_response(
        data={"user": user.to_dict()},
        message="Profile fetched successfully."
    )
