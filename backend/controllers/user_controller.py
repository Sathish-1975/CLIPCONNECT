"""
============================================================
ClipConnect - User / Editor Profile Controller
============================================================
Handles all business logic for the editor profile system:

  setup_editor_profile()    POST /api/users/me/profile
  get_my_profile()          GET  /api/users/me/profile
  update_my_profile()       PUT  /api/users/me/profile
  upload_avatar()           POST /api/users/me/avatar
  upload_banner()           POST /api/users/me/banner
  upload_resume()           POST /api/users/me/resume
  upload_portfolio_image()  POST /api/users/me/portfolio/image
  get_editor_public()       GET  /api/users/editors/<user_id>
  list_editors()            GET  /api/users/editors
  add_portfolio_video()     POST /api/users/me/portfolio/video
  delete_portfolio_video()  DELETE /api/users/me/portfolio/video/<index>
  delete_portfolio_image()  DELETE /api/users/me/portfolio/image/<index>
============================================================
"""

import json
from flask import request, current_app
from sqlalchemy import or_

from database import db
from models.user_model import User, UserRole
from models.editor_profile_model import EditorProfile, EditorCategory, AvailabilityStatus
from utils.response_helper import success_response, error_response, paginated_response
from utils.upload_helper import save_upload, delete_upload, get_upload_url


# ============================================================
# Helper: Fetch profile or 404
# ============================================================

def _get_profile_or_none(user_id: int):
    return EditorProfile.query.filter_by(user_id=user_id).first()


def _require_editor(current_user: dict):
    """Return (user, profile, error_response). error_response is None if ok."""
    if current_user.get('role') != 'editor':
        return None, None, error_response(
            message='Only editors can manage an editor profile.',
            status_code=403
        )
    user = User.query.get(current_user['user_id'])
    if not user or not user.is_active:
        return None, None, error_response(message='User not found or inactive.', status_code=404)
    profile = _get_profile_or_none(user.id)
    return user, profile, None


# ============================================================
# 1. Setup / Create Profile  — POST /api/users/me/profile
# ============================================================

def setup_editor_profile(current_user: dict):
    """
    Creates the EditorProfile row for this editor.
    Idempotent: if profile already exists, returns it unchanged.
    Called automatically after editor registration or manually by the editor.
    """
    user, profile, err = _require_editor(current_user)
    if err:
        return err

    if profile:
        return success_response(
            data={'profile': profile.to_dict(public=False)},
            message='Profile already exists.',
            status_code=200
        )

    # Create blank profile
    new_profile = EditorProfile(user_id=user.id)
    try:
        db.session.add(new_profile)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Profile create error: {e}')
        return error_response(message='Could not create profile. Please try again.', status_code=500)

    return success_response(
        data={'profile': new_profile.to_dict(public=False)},
        message='Editor profile created! Complete your profile to start getting hired.',
        status_code=201
    )


# ============================================================
# 2. Get My Profile  — GET /api/users/me/profile
# ============================================================

def get_my_profile(current_user: dict):
    """Returns the authenticated editor's own full profile (private view)."""
    user, profile, err = _require_editor(current_user)
    if err:
        return err

    if not profile:
        return error_response(
            message="Profile not set up yet. Call POST /api/users/me/profile first.",
            status_code=404
        )

    return success_response(
        data={'profile': profile.to_dict(public=False)},
        message='Profile fetched successfully.'
    )


# ============================================================
# 3. Update Profile  — PUT /api/users/me/profile
# ============================================================

def update_my_profile(current_user: dict):
    """
    Updates one or many fields of the editor's profile.
    Only fields present in the request body are updated (partial update).

    Updatable text fields:
        username, tagline, bio, category, experience_years,
        skills, software_used, languages, city, country,
        hourly_rate, fixed_price_from, fixed_price_to,
        availability_status, response_time,
        website_url, youtube_url, instagram_url,
        linkedin_url, twitter_url, behance_url

    NOTE: Media files (avatar, banner, resume) are updated via
    their own dedicated upload endpoints.
    """
    user, profile, err = _require_editor(current_user)
    if err:
        return err

    # Auto-create profile if it doesn't exist
    if not profile:
        profile = EditorProfile(user_id=user.id)
        db.session.add(profile)

    data = request.get_json(silent=True) or {}

    # --- Text/Scalar fields ---
    scalar_fields = [
        'tagline', 'bio', 'experience_years',
        'city', 'country', 'response_time',
        'website_url', 'youtube_url', 'instagram_url',
        'linkedin_url', 'twitter_url', 'behance_url',
    ]
    for field in scalar_fields:
        if field in data:
            val = data[field]
            if isinstance(val, str):
                val = val.strip() or None
            setattr(profile, field, val)

    # --- Username (unique, validated) ---
    if 'username' in data:
        new_username = (data['username'] or '').strip().lower().lstrip('@')
        if new_username:
            # Check uniqueness (exclude own row)
            clash = EditorProfile.query.filter(
                EditorProfile.username == new_username,
                EditorProfile.user_id != user.id
            ).first()
            if clash:
                return error_response(
                    message='This username is already taken. Try another one.',
                    status_code=409,
                    errors={'username': 'Username already in use'}
                )
            if len(new_username) < 3:
                return error_response(
                    message='Username must be at least 3 characters.',
                    status_code=422,
                    errors={'username': 'Too short'}
                )
            profile.username = new_username
        else:
            profile.username = None

    # --- Numeric fields ---
    numeric_fields = ['hourly_rate', 'fixed_price_from', 'fixed_price_to']
    for field in numeric_fields:
        if field in data:
            val = data[field]
            if val is None or val == '':
                setattr(profile, field, None)
            else:
                try:
                    setattr(profile, field, float(val))
                except (TypeError, ValueError):
                    return error_response(
                        message=f"'{field}' must be a number.",
                        status_code=422,
                        errors={field: 'Must be a numeric value'}
                    )

    # --- JSON arrays ---
    array_fields = ['skills', 'software_used', 'languages']
    for field in array_fields:
        if field in data:
            val = data[field]
            if isinstance(val, list):
                # Sanitize: keep non-empty strings, max 30 items
                cleaned = [str(item).strip() for item in val if str(item).strip()][:30]
                setattr(profile, field, cleaned)
            elif val is None:
                setattr(profile, field, [])

    # --- Category enum ---
    if 'category' in data:
        cat_val = (data['category'] or '').strip().lower()
        try:
            profile.category = EditorCategory(cat_val)
        except ValueError:
            valid = [e.value for e in EditorCategory]
            return error_response(
                message=f"Invalid category. Must be one of: {', '.join(valid)}",
                status_code=422,
                errors={'category': 'Invalid category value'}
            )

    # --- Availability enum ---
    if 'availability_status' in data:
        av_val = (data['availability_status'] or '').strip().lower()
        try:
            profile.availability_status = AvailabilityStatus(av_val)
        except ValueError:
            valid = [e.value for e in AvailabilityStatus]
            return error_response(
                message=f"Invalid availability. Must be one of: {', '.join(valid)}",
                status_code=422
            )

    # --- Commit ---
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Profile update error: {e}')
        return error_response(message='Could not save profile. Please try again.', status_code=500)

    return success_response(
        data={'profile': profile.to_dict(public=False)},
        message='Profile updated successfully.'
    )


# ============================================================
# 4. Upload Avatar  — POST /api/users/me/avatar
# ============================================================

def upload_avatar(current_user: dict):
    """
    Upload / replace the editor's profile photo.
    Expects multipart/form-data with field 'avatar'.
    """
    user, profile, err = _require_editor(current_user)
    if err:
        return err
    if not profile:
        profile = EditorProfile(user_id=user.id)
        db.session.add(profile)

    file = request.files.get('avatar')
    if not file:
        return error_response(message="No file provided. Send field named 'avatar'.", status_code=400)

    try:
        # Delete old avatar
        if profile.profile_photo:
            delete_upload(profile.profile_photo, 'avatars')

        filename = save_upload(file, 'avatars')
        profile.profile_photo = filename
        db.session.commit()
    except ValueError as ve:
        return error_response(message=str(ve), status_code=422)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Avatar upload error: {e}')
        return error_response(message='Upload failed. Please try again.', status_code=500)

    return success_response(
        data={
            'filename': filename,
            'url': get_upload_url(filename, 'avatars')
        },
        message='Profile photo uploaded successfully.'
    )


# ============================================================
# 5. Upload Banner  — POST /api/users/me/banner
# ============================================================

def upload_banner(current_user: dict):
    """Upload / replace the editor's cover banner image."""
    user, profile, err = _require_editor(current_user)
    if err:
        return err
    if not profile:
        profile = EditorProfile(user_id=user.id)
        db.session.add(profile)

    file = request.files.get('banner')
    if not file:
        return error_response(message="No file provided. Send field named 'banner'.", status_code=400)

    try:
        if profile.cover_banner:
            delete_upload(profile.cover_banner, 'banners')
        filename = save_upload(file, 'banners')
        profile.cover_banner = filename
        db.session.commit()
    except ValueError as ve:
        return error_response(message=str(ve), status_code=422)
    except Exception as e:
        db.session.rollback()
        return error_response(message='Banner upload failed.', status_code=500)

    return success_response(
        data={'filename': filename, 'url': get_upload_url(filename, 'banners')},
        message='Cover banner uploaded successfully.'
    )


# ============================================================
# 6. Upload Resume  — POST /api/users/me/resume
# ============================================================

def upload_resume(current_user: dict):
    """Upload / replace the editor's resume (PDF or DOC)."""
    user, profile, err = _require_editor(current_user)
    if err:
        return err
    if not profile:
        profile = EditorProfile(user_id=user.id)
        db.session.add(profile)

    file = request.files.get('resume')
    if not file:
        return error_response(message="No file provided. Send field named 'resume'.", status_code=400)

    try:
        if profile.resume_file:
            delete_upload(profile.resume_file, 'resumes')
        filename = save_upload(file, 'resumes')
        profile.resume_file = filename
        db.session.commit()
    except ValueError as ve:
        return error_response(message=str(ve), status_code=422)
    except Exception as e:
        db.session.rollback()
        return error_response(message='Resume upload failed.', status_code=500)

    return success_response(
        data={'filename': filename, 'url': get_upload_url(filename, 'resumes')},
        message='Resume uploaded successfully.'
    )


# ============================================================
# 7. Upload Portfolio Image  — POST /api/users/me/portfolio/image
# ============================================================

def upload_portfolio_image(current_user: dict):
    """
    Upload a portfolio image and add it to the portfolio_images list.
    Accepts: multipart/form-data with 'image' file + optional 'title', 'description'.
    Max 20 portfolio images.
    """
    user, profile, err = _require_editor(current_user)
    if err:
        return err
    if not profile:
        profile = EditorProfile(user_id=user.id)
        db.session.add(profile)

    file = request.files.get('image')
    if not file:
        return error_response(message="No file provided. Send field named 'image'.", status_code=400)

    images = list(profile.portfolio_images or [])
    if len(images) >= 20:
        return error_response(message='Maximum 20 portfolio images allowed.', status_code=422)

    try:
        filename = save_upload(file, 'portfolio/images')
    except ValueError as ve:
        return error_response(message=str(ve), status_code=422)
    except Exception as e:
        return error_response(message='Upload failed.', status_code=500)

    title       = (request.form.get('title') or '').strip() or None
    description = (request.form.get('description') or '').strip() or None

    image_entry = {
        'filename':    filename,
        'url':         get_upload_url(filename, 'portfolio/images'),
        'title':       title,
        'description': description,
    }
    images.append(image_entry)
    profile.portfolio_images = images

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response(message='Could not save portfolio image.', status_code=500)

    return success_response(
        data={'image': image_entry, 'total': len(images)},
        message='Portfolio image uploaded.',
        status_code=201
    )


# ============================================================
# 8. Add Portfolio Video  — POST /api/users/me/portfolio/video
# ============================================================

def add_portfolio_video(current_user: dict):
    """
    Add a YouTube/Vimeo/Drive video link to the portfolio.
    Body: { url, title, thumbnail (optional), description (optional) }
    Max 10 videos.
    """
    user, profile, err = _require_editor(current_user)
    if err:
        return err
    if not profile:
        profile = EditorProfile(user_id=user.id)
        db.session.add(profile)

    data = request.get_json(silent=True) or {}
    url = (data.get('url') or '').strip()
    if not url:
        return error_response(message='Video URL is required.', status_code=422)

    videos = list(profile.portfolio_videos or [])
    if len(videos) >= 10:
        return error_response(message='Maximum 10 portfolio videos allowed.', status_code=422)

    video_entry = {
        'url':         url,
        'title':       (data.get('title') or '').strip() or None,
        'thumbnail':   (data.get('thumbnail') or '').strip() or None,
        'description': (data.get('description') or '').strip() or None,
    }
    videos.append(video_entry)
    profile.portfolio_videos = videos

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response(message='Could not save video.', status_code=500)

    return success_response(
        data={'video': video_entry, 'total': len(videos)},
        message='Portfolio video added.',
        status_code=201
    )


# ============================================================
# 9. Delete Portfolio Video  — DELETE /api/users/me/portfolio/video/<int:index>
# ============================================================

def delete_portfolio_video(current_user: dict, index: int):
    user, profile, err = _require_editor(current_user)
    if err:
        return err
    if not profile:
        return error_response(message='Profile not found.', status_code=404)

    videos = list(profile.portfolio_videos or [])
    if index < 0 or index >= len(videos):
        return error_response(message=f'No video at index {index}.', status_code=404)

    removed = videos.pop(index)
    profile.portfolio_videos = videos

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response(message='Could not delete video.', status_code=500)

    return success_response(data={'removed': removed}, message='Portfolio video removed.')


# ============================================================
# 10. Delete Portfolio Image  — DELETE /api/users/me/portfolio/image/<int:index>
# ============================================================

def delete_portfolio_image(current_user: dict, index: int):
    user, profile, err = _require_editor(current_user)
    if err:
        return err
    if not profile:
        return error_response(message='Profile not found.', status_code=404)

    images = list(profile.portfolio_images or [])
    if index < 0 or index >= len(images):
        return error_response(message=f'No image at index {index}.', status_code=404)

    removed = images.pop(index)
    profile.portfolio_images = images

    # Delete file from disk
    if removed.get('filename'):
        delete_upload(removed['filename'], 'portfolio/images')

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response(message='Could not delete image.', status_code=500)

    return success_response(data={'removed': removed}, message='Portfolio image removed.')


# ============================================================
# 11. Get Editor Public Profile  — GET /api/users/editors/<user_id>
# ============================================================

def get_editor_public(user_id: int):
    """Returns an editor's full public-facing profile."""
    profile = EditorProfile.query.filter_by(user_id=user_id).first()

    if not profile:
        return error_response(
            message='Editor profile not found.',
            status_code=404
        )

    # Verify the user is actually an editor and is active
    if not profile.user or profile.user.role != UserRole.EDITOR or not profile.user.is_active:
        return error_response(message='Editor not found.', status_code=404)

    return success_response(
        data={'profile': profile.to_dict(public=True)},
        message='Editor profile fetched.'
    )


# ============================================================
# 12. List Editors  — GET /api/users/editors
# ============================================================

def list_editors():
    """
    Returns a paginated, filterable list of editor profiles.

    Query Parameters:
        page         (int)  default 1
        per_page     (int)  default 12, max 50
        category     (str)  filter by EditorCategory value
        country      (str)  filter by country
        min_rating   (float) minimum avg_rating
        max_rate     (float) max hourly_rate
        search       (str)  search username, bio, tagline, skills
        available    (bool) only show available editors
        sort         (str)  'rating' | 'projects' | 'rate_asc' | 'rate_desc' | 'newest'
    """
    # --- Pagination ---
    page     = max(1, request.args.get('page', 1, type=int))
    per_page = min(50, max(1, request.args.get('per_page', 12, type=int)))

    # --- Base query: join EditorProfile with active editors ---
    query = (
        EditorProfile.query
        .join(User, EditorProfile.user_id == User.id)
        .filter(User.role == UserRole.EDITOR, User.is_active == True)
    )

    # --- Filters ---
    category_val = request.args.get('category', '').strip().lower()
    if category_val:
        try:
            query = query.filter(EditorProfile.category == EditorCategory(category_val))
        except ValueError:
            pass  # Ignore invalid category silently

    country_val = request.args.get('country', '').strip()
    if country_val:
        query = query.filter(EditorProfile.country.ilike(f'%{country_val}%'))

    min_rating = request.args.get('min_rating', type=float)
    if min_rating is not None:
        query = query.filter(EditorProfile.avg_rating >= min_rating)

    max_rate = request.args.get('max_rate', type=float)
    if max_rate is not None:
        query = query.filter(
            or_(EditorProfile.hourly_rate == None, EditorProfile.hourly_rate <= max_rate)
        )

    available_only = request.args.get('available', '').lower() in ('true', '1', 'yes')
    if available_only:
        query = query.filter(EditorProfile.availability_status == AvailabilityStatus.AVAILABLE)

    search_q = request.args.get('search', '').strip()
    if search_q:
        like = f'%{search_q}%'
        query = query.filter(
            or_(
                EditorProfile.username.ilike(like),
                EditorProfile.tagline.ilike(like),
                EditorProfile.bio.ilike(like),
                User.full_name.ilike(like),
            )
        )

    # --- Sorting ---
    sort_by = request.args.get('sort', 'rating').strip().lower()
    if sort_by == 'projects':
        query = query.order_by(EditorProfile.completed_projects.desc())
    elif sort_by == 'rate_asc':
        query = query.order_by(EditorProfile.hourly_rate.asc().nulls_last())
    elif sort_by == 'rate_desc':
        query = query.order_by(EditorProfile.hourly_rate.desc().nulls_last())
    elif sort_by == 'newest':
        query = query.order_by(EditorProfile.created_at.desc())
    else:  # default: rating
        query = query.order_by(EditorProfile.avg_rating.desc(), EditorProfile.completed_projects.desc())

    # --- Execute paginated query ---
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    editors = [p.to_dict(public=True) for p in pagination.items]

    return paginated_response(
        items=editors,
        total=pagination.total,
        page=page,
        per_page=per_page,
        message=f'Found {pagination.total} editors.'
    )
