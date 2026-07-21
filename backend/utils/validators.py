"""
============================================================
ClipConnect - Input Validators
============================================================
Purpose:
    Provides reusable validation functions for all API inputs.
    Prevents invalid/malicious data from reaching the database.

Why validation matters:
    - Prevents SQL injection at the application level
    - Ensures data integrity (no empty names, invalid emails)
    - Gives clear error messages back to the user
    - Reduces database errors from bad data

Usage:
    from utils.validators import validate_registration_data, validate_login_data

    errors = validate_registration_data(request.get_json())
    if errors:
        return error_response("Validation failed", 422, errors)
============================================================
"""

import re
from models.user_model import UserRole


# ============================================================
# Constants
# ============================================================

# Minimum / maximum field lengths
MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 150
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
MAX_EMAIL_LENGTH = 255

# Email regex pattern (RFC 5322 simplified)
EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
)

# Valid roles for registration
VALID_ROLES = [role.value for role in UserRole]  # ['client', 'editor', 'admin']


# ============================================================
# Validation Functions
# ============================================================

def validate_registration_data(data):
    """
    Validates all fields for the user registration endpoint.
    
    Args:
        data (dict): Parsed JSON body from the request
    
    Returns:
        dict: A dictionary of field -> error message pairs.
              Empty dict {} means validation PASSED.
    
    Validates:
        - full_name: Required, 2-150 chars, no numbers
        - email: Required, valid format, max 255 chars
        - password: Required, min 8 chars, complexity check
        - role: Required, must be 'client' or 'editor'
    """
    errors = {}

    # Handle case where no JSON body was sent
    if not data:
        return {"general": "Request body is required (send JSON)"}

    # --- Validate full_name ---
    full_name = data.get('full_name', '')
    if not full_name:
        errors['full_name'] = 'Full name is required'
    elif not isinstance(full_name, str):
        errors['full_name'] = 'Full name must be a string'
    elif len(full_name.strip()) < MIN_NAME_LENGTH:
        errors['full_name'] = f'Full name must be at least {MIN_NAME_LENGTH} characters'
    elif len(full_name.strip()) > MAX_NAME_LENGTH:
        errors['full_name'] = f'Full name cannot exceed {MAX_NAME_LENGTH} characters'
    elif re.search(r'\d', full_name):
        errors['full_name'] = 'Full name should not contain numbers'

    # --- Validate email ---
    email = data.get('email', '')
    if not email:
        errors['email'] = 'Email address is required'
    elif not isinstance(email, str):
        errors['email'] = 'Email must be a string'
    elif len(email) > MAX_EMAIL_LENGTH:
        errors['email'] = f'Email cannot exceed {MAX_EMAIL_LENGTH} characters'
    elif not EMAIL_PATTERN.match(email.strip()):
        errors['email'] = 'Please enter a valid email address'

    # --- Validate password ---
    password = data.get('password', '')
    if not password:
        errors['password'] = 'Password is required'
    elif not isinstance(password, str):
        errors['password'] = 'Password must be a string'
    elif len(password) < MIN_PASSWORD_LENGTH:
        errors['password'] = f'Password must be at least {MIN_PASSWORD_LENGTH} characters'
    elif len(password) > MAX_PASSWORD_LENGTH:
        errors['password'] = f'Password cannot exceed {MAX_PASSWORD_LENGTH} characters'
    else:
        # Password strength checks
        pwd_errors = _check_password_strength(password)
        if pwd_errors:
            errors['password'] = pwd_errors

    # --- Validate role ---
    role = data.get('role', '')
    if not role:
        errors['role'] = 'Role is required'
    elif role.lower() not in ['client', 'editor']:
        # Only allow client and editor for self-registration
        # Admin accounts are created separately
        errors['role'] = 'Role must be either "client" or "editor"'

    return errors


def validate_login_data(data):
    """
    Validates all fields for the user login endpoint.
    
    Args:
        data (dict): Parsed JSON body from the request
    
    Returns:
        dict: Field -> error message pairs. Empty = valid.
    """
    errors = {}

    if not data:
        return {"general": "Request body is required (send JSON)"}

    # --- Validate email ---
    email = data.get('email', '')
    if not email:
        errors['email'] = 'Email address is required'
    elif not isinstance(email, str):
        errors['email'] = 'Email must be a string'
    elif not EMAIL_PATTERN.match(email.strip()):
        errors['email'] = 'Please enter a valid email address'

    # --- Validate password ---
    password = data.get('password', '')
    if not password:
        errors['password'] = 'Password is required'
    elif not isinstance(password, str):
        errors['password'] = 'Password must be a string'

    return errors


# ============================================================
# Helper Functions
# ============================================================

def _check_password_strength(password):
    """
    Internal helper: checks password for complexity requirements.
    
    Args:
        password (str): Password to check
    
    Returns:
        str|None: Error message if weak, None if strong enough
    """
    has_uppercase = bool(re.search(r'[A-Z]', password))
    has_lowercase = bool(re.search(r'[a-z]', password))
    has_digit = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~/]', password))

    missing = []
    if not has_uppercase:
        missing.append('one uppercase letter')
    if not has_lowercase:
        missing.append('one lowercase letter')
    if not has_digit:
        missing.append('one number')
    if not has_special:
        missing.append('one special character (!@#$...)')

    if missing:
        return f'Password must contain at least: {", ".join(missing)}'

    return None  # Password is strong


def sanitize_string(value, max_length=None):
    """
    Strips whitespace and optionally truncates a string.
    
    Args:
        value (str): Input string
        max_length (int|None): If set, truncates to this length
    
    Returns:
        str: Cleaned string
    """
    if not value or not isinstance(value, str):
        return ''
    cleaned = value.strip()
    if max_length:
        cleaned = cleaned[:max_length]
    return cleaned
