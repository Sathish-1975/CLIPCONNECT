"""
============================================================
ClipConnect - Client Dashboard Controller
============================================================
Handles:
  get_client_dashboard()        GET  /api/users/me/dashboard
  update_account_settings()     PUT  /api/users/me/account
  upload_client_avatar()        POST /api/users/me/client-avatar
  get_favorites()               GET  /api/users/me/favorites
  add_favorite()                POST /api/users/me/favorites/<editor_id>
  remove_favorite()             DELETE /api/users/me/favorites/<editor_id>
  get_notifications()           GET  /api/users/me/notifications
  mark_notification_read()      PATCH /api/users/me/notifications/<notif_id>
  mark_all_read()               POST  /api/users/me/notifications/read-all
  update_notification_prefs()   PUT  /api/users/me/notifications/prefs
============================================================
"""

import uuid
import bcrypt
from datetime import datetime, timezone

from flask import request, current_app
from database import db
from models.user_model import User, UserRole
from models.client_profile_model import ClientProfile
from models.editor_profile_model import EditorProfile
from models.project_model import Project, ProjectStatus
from models.proposal_model import Proposal
from utils.response_helper import success_response, error_response
from utils.upload_helper import save_upload, delete_upload, get_upload_url


# ── Internal helpers ──────────────────────────────────────────────

def _get_or_create_client_profile(user_id: int) -> ClientProfile:
    """Fetch client profile, auto-creating if it doesn't exist."""
    profile = ClientProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = ClientProfile(user_id=user_id)
        db.session.add(profile)
        db.session.flush()   # Get ID without full commit
    return profile


def _require_client(current_user: dict):
    """Return (user, profile) or raise an error response tuple."""
    user = User.query.get(current_user['user_id'])
    if not user or not user.is_active:
        return None, None, error_response('User not found.', 404)
    if user.role != UserRole.CLIENT:
        return None, None, error_response('Only clients can access the client dashboard.', 403)
    profile = _get_or_create_client_profile(user.id)
    return user, profile, None


def _make_welcome_message(user: User) -> str:
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    first = user.full_name.split()[0]
    return f"{greeting}, {first}!"


# ── 1. Dashboard Summary ─────────────────────────────────────────

def get_client_dashboard(current_user: dict):
    """
    GET /api/users/me/dashboard
    Returns everything the dashboard needs in one call:
      - User info + greeting
      - Project stats (active, completed, pending) — zero until orders exist
      - Favorite editors (with profile snippets)
      - Unread notification count
      - Recent activity feed
    """
    user, profile, err = _require_client(current_user)
    if err:
        return err

    # Fetch Real Projects for the client
    all_projects = Project.query.filter_by(client_id=user.id).order_by(Project.created_at.desc()).all()
    
    active_projects = sum(1 for p in all_projects if p.status == ProjectStatus.IN_PROGRESS)
    completed_projects = sum(1 for p in all_projects if p.status == ProjectStatus.COMPLETED)
    pending_requests = sum(1 for p in all_projects if p.status == ProjectStatus.WAITING_FOR_EDITOR)
    total_spent = sum(p.budget for p in all_projects if p.status == ProjectStatus.COMPLETED and p.budget)

    recent_projects = []
    for p in all_projects[:10]: # Return top 10 recent
        editor_name = 'Pending'
        p_status_str = p.status.value.replace('_', ' ').title()
        
        # Determine the editor name based on proposals or hired_editor
        if p.hired_editor_id:
            hired_user = User.query.get(p.hired_editor_id)
            if hired_user:
                editor_name = hired_user.full_name
        else:
            # Check proposals to see who it was sent to, or if it was declined
            prop = Proposal.query.filter_by(project_id=p.id).order_by(Proposal.created_at.desc()).first()
            if prop:
                editor = User.query.get(prop.editor_id)
                editor_name = editor.full_name if editor else 'Unknown'
                # If the proposal was rejected and project still waiting, it means declined.
                if prop.status == 'rejected' and p.status == ProjectStatus.WAITING_FOR_EDITOR:
                    p_status_str = 'Declined'
                else:
                    p_status_str = 'Pending Request'
            else:
                p_status_str = 'Draft / No Request'
                

        # Override status string based on actual project status
        if p.status == ProjectStatus.IN_PROGRESS:
            p_status_str = 'Accepted (In Progress)'
        elif p.status == ProjectStatus.COMPLETED:
            p_status_str = 'Completed'
        elif p.status == ProjectStatus.CANCELLED:
            p_status_str = 'Cancelled'
        elif p.status == ProjectStatus.ACCEPTED:
            p_status_str = 'Accepted'
        elif p.status == ProjectStatus.UNDER_REVIEW:
            p_status_str = 'Under Review'
        elif p.status == ProjectStatus.REVISION_REQUESTED:
            p_status_str = 'Revision Requested'
        
        recent_projects.append({
            'id': p.id,
            'title': p.title,
            'budget': p.budget,
            'status': p_status_str,
            'editor_name': editor_name,
            'created_at': p.created_at.isoformat() if p.created_at else None
        })

    # Favorite editors — fetch full snippets
    fav_ids = profile.favorite_editors or []
    fav_editors = []
    if fav_ids:
        profiles = EditorProfile.query.filter(
            EditorProfile.user_id.in_(fav_ids)
        ).all()
        for ep in profiles:
            if ep.user and ep.user.is_active:
                fav_editors.append({
                    'user_id':        ep.user_id,
                    'full_name':      ep.user.full_name,
                    'username':       ep.username,
                    'tagline':        ep.tagline,
                    'category':       ep.category.value if ep.category else None,
                    'profile_photo':  ep.profile_photo,
                    'avg_rating':     float(ep.avg_rating) if ep.avg_rating else 0.0,
                    'total_reviews':  ep.total_reviews,
                    'hourly_rate':    float(ep.hourly_rate) if ep.hourly_rate else None,
                    'availability':   ep.availability_status.value if ep.availability_status else 'available',
                    'completed_projects': ep.completed_projects,
                })

    # Unread notifications
    import controllers.notification_controller as notif_ctrl
    # Fetch from notification controller to maintain consistency
    unread_count = 0
    try:
        from models.notification_model import Notification
        unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    except Exception:
        pass

    # Recent activity feed (static for now — will be order events in Week 3)
    recent_activity = []

    return success_response(
        data={
            'welcome_message':     _make_welcome_message(user),
            'user': {
                'id':           user.id,
                'full_name':    user.full_name,
                'email':        user.email,
                'role':         user.role.value,
                'profile_photo': profile.profile_photo,
                'member_since': user.created_at.isoformat() if user.created_at else None,
            },
            'stats': {
                'active_projects':    active_projects,
                'completed_projects': completed_projects,
                'pending_requests':   pending_requests,
                'favorite_editors':   len(fav_ids),
                'total_spent':        total_spent,
            },
            'favorite_editors':   fav_editors,
            'recent_projects':    recent_projects,
            'unread_notifications': unread_count,
            'recent_activity':    recent_activity,
        },
        message='Dashboard loaded.'
    )


# ── 2. Account Settings ───────────────────────────────────────────

def update_account_settings(current_user: dict):
    """
    PUT /api/users/me/account
    Update name, email, password + client profile fields.
    Body (all optional):
      full_name, email, current_password, new_password,
      phone, company, bio, city, country, website,
      notif_email, notif_projects, notif_messages
    """
    user, profile, err = _require_client(current_user)
    if err:
        return err

    data = request.get_json(silent=True) or {}
    changes = []

    # ── full_name ──
    if 'full_name' in data:
        name = data['full_name'].strip()
        if len(name) < 2:
            return error_response('Full name must be at least 2 characters.', 422)
        user.full_name = name
        changes.append('name')

    # ── email ──
    if 'email' in data:
        new_email = data['email'].strip().lower()
        if new_email != user.email:
            clash = User.query.filter_by(email=new_email).first()
            if clash:
                return error_response('This email is already in use.', 409, {'email': 'Already taken'})
            user.email = new_email
            changes.append('email')

    # ── password change ──
    if 'new_password' in data and data['new_password']:
        current_pw = data.get('current_password', '')
        if not current_pw:
            return error_response('Current password is required to set a new one.', 422)
        if not bcrypt.checkpw(current_pw.encode(), user.password.encode()):
            return error_response('Current password is incorrect.', 401)
        new_pw = data['new_password']
        if len(new_pw) < 8:
            return error_response('New password must be at least 8 characters.', 422)
        user.password = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt(12)).decode()
        changes.append('password')

    # ── client profile fields ──
    profile_fields = ['phone', 'company', 'bio', 'city', 'country', 'website']
    for field in profile_fields:
        if field in data:
            val = (data[field] or '').strip() or None
            setattr(profile, field, val)

    # ── notification prefs ──
    for pref in ['notif_email', 'notif_projects', 'notif_messages']:
        if pref in data:
            setattr(profile, pref, bool(data[pref]))

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Account settings update error: {e}')
        return error_response('Could not save settings. Please try again.', 500)

    return success_response(
        data={
            'user':    {'id': user.id, 'full_name': user.full_name, 'email': user.email},
            'profile': profile.to_dict(),
            'changes': changes,
        },
        message='Account settings saved successfully.'
    )


# ── 3. Client Avatar Upload ───────────────────────────────────────

def upload_client_avatar(current_user: dict):
    """POST /api/users/me/client-avatar — upload client profile photo."""
    user, profile, err = _require_client(current_user)
    if err:
        return err

    file = request.files.get('avatar')
    if not file:
        return error_response("No file. Send field named 'avatar'.", 400)

    try:
        if profile.profile_photo:
            delete_upload(profile.profile_photo, 'avatars')
        filename = save_upload(file, 'avatars')
        profile.profile_photo = filename
        db.session.commit()
    except ValueError as ve:
        return error_response(str(ve), 422)
    except Exception as e:
        db.session.rollback()
        return error_response('Upload failed.', 500)

    return success_response(
        data={'filename': filename, 'url': get_upload_url(filename, 'avatars')},
        message='Profile photo updated.'
    )


# ── 4. Favorites ─────────────────────────────────────────────────

def get_favorites(current_user: dict):
    """GET /api/users/me/favorites — list favorite editors with full snippets."""
    user, profile, err = _require_client(current_user)
    if err:
        return err

    fav_ids = profile.favorite_editors or []
    if not fav_ids:
        return success_response(data={'favorites': [], 'total': 0}, message='No favorites yet.')

    profiles = EditorProfile.query.filter(EditorProfile.user_id.in_(fav_ids)).all()
    result = []
    for ep in profiles:
        if not ep.user or not ep.user.is_active:
            continue
        result.append({
            'user_id':        ep.user_id,
            'full_name':      ep.user.full_name,
            'username':       ep.username,
            'tagline':        ep.tagline,
            'category':       ep.category.value if ep.category else None,
            'profile_photo':  ep.profile_photo,
            'avg_rating':     float(ep.avg_rating) if ep.avg_rating else 0.0,
            'total_reviews':  ep.total_reviews,
            'hourly_rate':    float(ep.hourly_rate) if ep.hourly_rate else None,
            'availability':   ep.availability_status.value if ep.availability_status else 'available',
            'completed_projects': ep.completed_projects,
            'city':           ep.city,
            'country':        ep.country,
            'skills':         (ep.skills or [])[:5],
        })

    return success_response(data={'favorites': result, 'total': len(result)}, message='Favorites fetched.')


def add_favorite(current_user: dict, editor_id: int):
    """POST /api/users/me/favorites/<editor_id>"""
    user, profile, err = _require_client(current_user)
    if err:
        return err

    # Verify editor exists
    editor = User.query.get(editor_id)
    if not editor or editor.role != UserRole.EDITOR or not editor.is_active:
        return error_response('Editor not found.', 404)

    favs = list(profile.favorite_editors or [])
    if editor_id in favs:
        return success_response(data={'favorite_editors': favs}, message='Already in favorites.')

    if len(favs) >= 50:
        return error_response('Maximum 50 favorite editors allowed.', 422)

    favs.append(editor_id)
    profile.favorite_editors = favs

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error_response('Could not add favorite.', 500)

    return success_response(
        data={'favorite_editors': favs, 'total': len(favs)},
        message=f'{editor.full_name} added to favorites!',
        status_code=201
    )


def remove_favorite(current_user: dict, editor_id: int):
    """DELETE /api/users/me/favorites/<editor_id>"""
    user, profile, err = _require_client(current_user)
    if err:
        return err

    favs = list(profile.favorite_editors or [])
    if editor_id not in favs:
        return error_response('Editor not in favorites.', 404)

    favs.remove(editor_id)
    profile.favorite_editors = favs

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error_response('Could not remove favorite.', 500)

    return success_response(data={'favorite_editors': favs}, message='Removed from favorites.')


# ── 5. Notifications ─────────────────────────────────────────────

def get_notifications(current_user: dict):
    """GET /api/users/me/notifications"""
    user, profile, err = _require_client(current_user)
    if err:
        return err

    # Seed welcome notification for new accounts
    notifs = list(profile.notifications or [])
    if not notifs:
        notifs = [
            {
                'id':         str(uuid.uuid4()),
                'type':       'welcome',
                'title':      'Welcome to ClipConnect!',
                'message':    'Your account is set up. Browse editors and find your perfect match.',
                'read':       False,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'icon':       'celebration',
            }
        ]
        profile.notifications = notifs
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    unread = sum(1 for n in notifs if not n.get('read'))
    return success_response(
        data={'notifications': list(reversed(notifs)), 'unread_count': unread},
        message='Notifications fetched.'
    )


def mark_notification_read(current_user: dict, notif_id: str):
    """PATCH /api/users/me/notifications/<notif_id>"""
    user, profile, err = _require_client(current_user)
    if err:
        return err

    notifs = list(profile.notifications or [])
    found  = False
    for n in notifs:
        if n.get('id') == notif_id:
            n['read'] = True
            found = True
            break

    if not found:
        return error_response('Notification not found.', 404)

    profile.notifications = notifs
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error_response('Could not update notification.', 500)

    return success_response(message='Notification marked as read.')


def mark_all_notifications_read(current_user: dict):
    """POST /api/users/me/notifications/read-all"""
    user, profile, err = _require_client(current_user)
    if err:
        return err

    notifs = list(profile.notifications or [])
    for n in notifs:
        n['read'] = True
    profile.notifications = notifs

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error_response('Could not mark all read.', 500)

    return success_response(message='All notifications marked as read.')


def update_notification_prefs(current_user: dict):
    """PUT /api/users/me/notifications/prefs"""
    user, profile, err = _require_client(current_user)
    if err:
        return err

    data = request.get_json(silent=True) or {}
    for pref in ['notif_email', 'notif_projects', 'notif_messages']:
        if pref in data:
            setattr(profile, pref, bool(data[pref]))

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error_response('Could not save preferences.', 500)

    return success_response(data=profile.to_dict(), message='Notification preferences saved.')
