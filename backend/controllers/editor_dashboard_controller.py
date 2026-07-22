"""
============================================================
ClipConnect - Editor Dashboard Controller
============================================================
Handles:
  get_editor_dashboard()    GET  /api/users/me/editor-dashboard
  update_availability()     PUT  /api/users/me/availability
============================================================
"""

from datetime import datetime, timezone
from flask import request, current_app
from database import db
from models.user_model import User, UserRole
from models.editor_profile_model import EditorProfile, AvailabilityStatus
from utils.response_helper import success_response, error_response


# ── Internal helpers ─────────────────────────────────────────────

def _require_editor(current_user: dict):
    user = User.query.get(current_user['user_id'])
    if not user or not user.is_active:
        return None, None, error_response('User not found.', 404)
    if user.role != UserRole.EDITOR:
        return None, None, error_response('Only editors can access the editor dashboard.', 403)
    profile = EditorProfile.query.filter_by(user_id=user.id).first()
    if not profile:
        profile = EditorProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
    return user, profile, None


def _greeting(name: str) -> str:
    h = datetime.now().hour
    g = 'Good morning' if h < 12 else 'Good afternoon' if h < 17 else 'Good evening'
    return f"{g}, {name.split()[0]}! 👋"


def _calc_completion(p: EditorProfile) -> dict:
    """
    Calculate profile completion % and missing items list.
    Returns { pct: int, score: int, total: int, missing: [str] }
    """
    checks = [
        ('profile_photo',  bool(p.profile_photo),           'Profile Photo'),
        ('cover_banner',   bool(p.cover_banner),            'Cover Banner'),
        ('username',       bool(p.username),                '@Username'),
        ('tagline',        bool(p.tagline),                 'Tagline'),
        ('bio',            bool(p.bio and len(p.bio) > 30), 'Bio (min 30 chars)'),
        ('category',       bool(p.category),                'Specialization Category'),
        ('experience',     bool(p.experience_years),        'Years of Experience'),
        ('skills',         bool(p.skills and len(p.skills) >= 3), 'At least 3 Skills'),
        ('software',       bool(p.software_used and len(p.software_used) >= 1), 'Software Used'),
        ('languages',      bool(p.languages),               'Languages'),
        ('location',       bool(p.city and p.country),      'City & Country'),
        ('pricing',        bool(p.hourly_rate or p.fixed_price_from), 'Pricing'),
        ('availability',   True,                             ''),   # Always set
        ('portfolio',      bool(
            (p.portfolio_videos and len(p.portfolio_videos) >= 1) or
            (p.portfolio_images and len(p.portfolio_images) >= 1)
        ),                                                   'Portfolio (images or videos)'),
        ('resume',         bool(p.resume_file),             'Resume / CV'),
        ('social',         bool(p.website_url or p.instagram_url or p.linkedin_url or p.youtube_url), 'Social Link'),
    ]

    score   = sum(1 for _, done, _ in checks if done)
    total   = len(checks)
    pct     = round((score / total) * 100)
    missing = [label for _, done, label in checks if not done and label]

    return {'pct': pct, 'score': score, 'total': total, 'missing': missing[:5]}


def _format_currency(val) -> str:
    if not val:
        return '₹0'
    return '₹' + f'{float(val):,.0f}'


# ── 1. Editor Dashboard ──────────────────────────────────────────

def get_editor_dashboard(current_user: dict):
    """
    GET /api/users/me/editor-dashboard
    Single endpoint that powers the entire editor dashboard.

    Returns:
      welcome_message, user info, profile snippet,
      completion %, stats, availability, analytics,
      reviews (empty until Week 3), requests (empty until Week 3)
    """
    user, profile, err = _require_editor(current_user)
    if err:
        return err

    completion = _calc_completion(profile)

    # ── Stats (zeroed until orders are built in Week 3) ──
    stats = {
        'incoming_requests':  0,
        'active_projects':    0,
        'completed_projects': profile.completed_projects or 0,
        'monthly_earnings':   0.0,
        'pending_payments':   0.0,
        'total_earnings':     float(profile.total_earnings) if profile.total_earnings else 0.0,
        'total_reviews':      profile.total_reviews or 0,
        'avg_rating':         float(profile.avg_rating) if profile.avg_rating else 0.0,
    }

    # ── Analytics ──
    analytics = {
        'profile_views':      0,    # Will track in Week 3
        'response_rate':      100,  # % responses within 24h
        'acceptance_rate':    100,  # % of requests accepted
        'on_time_delivery':   100,  # % delivered on time
        'repeat_clients':     0,    # Clients who returned
        'profile_completion': completion['pct'],
        # Simulated 6-month earnings chart data (all zero until orders)
        'earnings_chart': [
            {'month': 'Feb', 'earnings': 0},
            {'month': 'Mar', 'earnings': 0},
            {'month': 'Apr', 'earnings': 0},
            {'month': 'May', 'earnings': 0},
            {'month': 'Jun', 'earnings': 0},
            {'month': 'Jul', 'earnings': 0},
        ],
    }

    # ── Recent requests (empty until Week 3) ──
    recent_requests = []

    # ── Recent reviews (empty until Week 3) ──
    recent_reviews = []

    return success_response(
        data={
            'welcome_message': _greeting(user.full_name),
            'user': {
                'id':           user.id,
                'full_name':    user.full_name,
                'email':        user.email,
                'member_since': user.created_at.isoformat() if user.created_at else None,
            },
            'profile': {
                'username':            profile.username,
                'tagline':             profile.tagline,
                'bio':                 profile.bio,
                'profile_photo':       profile.profile_photo,
                'cover_banner':        profile.cover_banner,
                'category':            profile.category.value if profile.category else None,
                'experience_years':    profile.experience_years,
                'skills':              profile.skills or [],
                'software_used':       profile.software_used or [],
                'city':                profile.city,
                'country':             profile.country,
                'hourly_rate':         float(profile.hourly_rate) if profile.hourly_rate else None,
                'fixed_price_from':    float(profile.fixed_price_from) if profile.fixed_price_from else None,
                'availability_status': profile.availability_status.value if profile.availability_status else 'available',
                'response_time':       profile.response_time,
                'is_verified':         profile.is_verified,
                'is_featured':         profile.is_featured,
                'avg_rating':          float(profile.avg_rating) if profile.avg_rating else 0.0,
                'total_reviews':       profile.total_reviews,
                'completed_projects':  profile.completed_projects,
                'portfolio_images':    len(profile.portfolio_images or []),
                'portfolio_videos':    len(profile.portfolio_videos or []),
                'has_resume':          bool(profile.resume_file),
                'social_links': {
                    'website':   profile.website_url,
                    'youtube':   profile.youtube_url,
                    'instagram': profile.instagram_url,
                    'linkedin':  profile.linkedin_url,
                    'twitter':   profile.twitter_url,
                    'behance':   profile.behance_url,
                },
            },
            'completion':       completion,
            'stats':            stats,
            'analytics':        analytics,
            'recent_requests':  recent_requests,
            'recent_reviews':   recent_reviews,
        },
        message='Editor dashboard loaded.'
    )


# ── 2. Update Availability ────────────────────────────────────────

def update_availability(current_user: dict):
    """
    PUT /api/users/me/availability
    Body: { "availability_status": "available" | "busy" | "on_vacation" }

    Quickly toggles the editor's availability from the dashboard header.
    """
    user, profile, err = _require_editor(current_user)
    if err:
        return err

    data   = request.get_json(silent=True) or {}
    status = (data.get('availability_status') or '').strip().lower()

    if not status:
        return error_response('availability_status is required.', 422)

    try:
        new_status = AvailabilityStatus(status)
    except ValueError:
        valid = [e.value for e in AvailabilityStatus]
        return error_response(f"Invalid status. Must be one of: {', '.join(valid)}", 422)

    old_status = profile.availability_status.value if profile.availability_status else 'available'
    profile.availability_status = new_status

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Availability update error: {e}')
        return error_response('Could not update availability.', 500)

    labels = {'available': 'Available for Work', 'busy': 'Busy', 'on_vacation': 'On Vacation'}

    return success_response(
        data={
            'availability_status': new_status.value,
            'label':               labels.get(new_status.value, new_status.value),
            'previous_status':     old_status,
        },
        message=f'Status updated to: {labels.get(new_status.value, new_status.value)}'
    )
