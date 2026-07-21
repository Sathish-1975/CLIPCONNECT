"""
============================================================
ClipConnect - File Upload Helper
============================================================
Purpose:
    Handles all file upload operations:
    - Validate file type and size
    - Generate unique filenames to prevent collisions
    - Save file to correct folder under uploads/
    - Return the saved filename for storing in DB
    - Delete old files when updating

Supported upload folders:
    avatars/   - profile photos  (jpg, png, webp)
    banners/   - cover banners   (jpg, png, webp)
    resumes/   - resume PDFs     (pdf)
    portfolio/images/ - portfolio pics (jpg, png, webp)

Usage:
    from utils.upload_helper import save_upload, delete_upload, get_upload_url

    filename = save_upload(file_obj, folder='avatars')
    url      = get_upload_url(filename, folder='avatars')
    delete_upload(old_filename, folder='avatars')
============================================================
"""

import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename


# ============================================================
# Config
# ============================================================

# Base uploads directory: backend/uploads/
UPLOAD_BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')

# Folder → allowed extensions + max size
UPLOAD_CONFIG = {
    'avatars': {
        'extensions': {'jpg', 'jpeg', 'png', 'webp', 'gif'},
        'max_mb': 5,
        'path': os.path.join(UPLOAD_BASE, 'avatars'),
    },
    'banners': {
        'extensions': {'jpg', 'jpeg', 'png', 'webp'},
        'max_mb': 8,
        'path': os.path.join(UPLOAD_BASE, 'banners'),
    },
    'resumes': {
        'extensions': {'pdf', 'doc', 'docx'},
        'max_mb': 10,
        'path': os.path.join(UPLOAD_BASE, 'resumes'),
    },
    'portfolio/images': {
        'extensions': {'jpg', 'jpeg', 'png', 'webp', 'gif'},
        'max_mb': 10,
        'path': os.path.join(UPLOAD_BASE, 'portfolio', 'images'),
    },
}

# URL prefix for serving uploaded files
UPLOAD_URL_PREFIX = '/uploads'


# ============================================================
# Internal Helpers
# ============================================================

def _get_extension(filename: str) -> str:
    """Return lowercase file extension without the dot."""
    return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''


def _make_unique_filename(original_filename: str) -> str:
    """
    Generate a collision-safe filename using UUID + timestamp.
    Example: 'profile.jpg' → '2024_0101_a3f7b2c1.jpg'
    """
    ext = _get_extension(original_filename)
    uid = uuid.uuid4().hex[:10]
    ts  = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{ts}_{uid}.{ext}"


def _ensure_dir(path: str):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


# ============================================================
# Public API
# ============================================================

def validate_upload(file, folder: str) -> dict:
    """
    Validate an uploaded file before saving.

    Args:
        file: werkzeug FileStorage object from request.files
        folder: one of the keys in UPLOAD_CONFIG

    Returns:
        dict: { 'valid': bool, 'error': str|None }
    """
    if folder not in UPLOAD_CONFIG:
        return {'valid': False, 'error': f"Unknown upload folder: '{folder}'"}

    config = UPLOAD_CONFIG[folder]

    # Check filename exists
    if not file or not file.filename:
        return {'valid': False, 'error': 'No file provided.'}

    # Check extension
    ext = _get_extension(file.filename)
    if ext not in config['extensions']:
        allowed = ', '.join(sorted(config['extensions']))
        return {'valid': False, 'error': f"Invalid file type. Allowed: {allowed}"}

    # Check file size (read content_length from stream if not set)
    file.stream.seek(0, 2)          # Seek to end
    size_bytes = file.stream.tell()
    file.stream.seek(0)             # Reset to start
    max_bytes = config['max_mb'] * 1024 * 1024

    if size_bytes > max_bytes:
        return {'valid': False, 'error': f"File too large. Max size: {config['max_mb']} MB"}

    if size_bytes == 0:
        return {'valid': False, 'error': 'File is empty.'}

    return {'valid': True, 'error': None}


def save_upload(file, folder: str) -> str:
    """
    Validate and save an uploaded file.

    Args:
        file: werkzeug FileStorage object
        folder: destination folder key (e.g. 'avatars')

    Returns:
        str: The saved filename (store this in the DB)

    Raises:
        ValueError: If validation fails
        IOError: If file cannot be written to disk
    """
    # Validate first
    result = validate_upload(file, folder)
    if not result['valid']:
        raise ValueError(result['error'])

    config = UPLOAD_CONFIG[folder]
    _ensure_dir(config['path'])

    # Secure + unique filename
    safe_original = secure_filename(file.filename)
    filename = _make_unique_filename(safe_original)
    filepath = os.path.join(config['path'], filename)

    # Save to disk
    file.save(filepath)

    return filename


def delete_upload(filename: str, folder: str) -> bool:
    """
    Delete an uploaded file from disk.

    Args:
        filename: The filename stored in DB
        folder: The folder key it was saved under

    Returns:
        bool: True if deleted, False if not found
    """
    if not filename or folder not in UPLOAD_CONFIG:
        return False

    config = UPLOAD_CONFIG[folder]
    filepath = os.path.join(config['path'], filename)

    if os.path.exists(filepath):
        os.remove(filepath)
        return True

    return False


def get_upload_url(filename: str, folder: str) -> str | None:
    """
    Build the public URL for a stored file.

    Args:
        filename: The filename stored in DB
        folder: The folder key (e.g. 'avatars')

    Returns:
        str: URL like '/uploads/avatars/20240101_abc123.jpg'
        None: If filename is None/empty
    """
    if not filename:
        return None

    # Normalize folder path for URL (replace backslash on Windows)
    url_folder = folder.replace('\\', '/')
    return f"{UPLOAD_URL_PREFIX}/{url_folder}/{filename}"


def get_upload_path(filename: str, folder: str) -> str | None:
    """Return the absolute filesystem path of a stored file."""
    if not filename or folder not in UPLOAD_CONFIG:
        return None
    return os.path.join(UPLOAD_CONFIG[folder]['path'], filename)
