"""
============================================================
ClipConnect - Admin Controller
============================================================
Why this file exists:
  Provides controller logic for the complete Admin Control Panel, including system analytics,
  user moderation (verify/suspend/delete), project supervision, and financial audit logs.

What it does:
  - `get_admin_dashboard_stats()`: Computes total users, clients, editors, projects, revenue,
    active vs completed projects, monthly growth rate, and category popularity distribution.
  - `list_all_users()`: Returns paginated user listing with role and status filtering.
  - `update_user_status()`: Modifies user account status (active, suspended, verified, deleted).
  - `list_all_projects()`: Provides admin oversight of all platform project postings.
  - `list_all_payments()`: Provides admin financial ledger oversight for deposits, escrows, and releases.

How it integrates with the rest of the application:
  - Exposed via `/api/admin/*` endpoints in `admin_routes.py`.
  - Requires Admin role authorization.
  - Consumed by `admin-dashboard.html` and `admin.js`.
============================================================
"""

from datetime import datetime, timezone, timedelta
from flask import request, current_app

from database import db
from models.user_model import User, UserRole
from models.editor_profile_model import EditorProfile, EditorCategory
from models.client_profile_model import ClientProfile
from models.project_model import Project, ProjectStatus
from models.payment_model import Payment, Transaction
from models.review_model import Review
from utils.response_helper import success_response, error_response, paginated_response


def _require_admin(current_user: dict):
    user = User.query.get(current_user['user_id'])
    if not user or user.role != UserRole.ADMIN:
        return None, error_response(message="Admin authorization required.", status_code=403)
    return user, None


def get_admin_dashboard_stats(current_user: dict):
    """
    GET /api/admin/dashboard
    Returns complete platform analytics and statistics.
    """
    _, err = _require_admin(current_user)
    if err:
        return err

    total_users    = User.query.count()
    total_clients  = User.query.filter_by(role=UserRole.CLIENT).count()
    total_editors  = User.query.filter_by(role=UserRole.EDITOR).count()

    total_projects     = Project.query.filter(Project.status != ProjectStatus.DELETED).count()
    active_projects    = Project.query.filter(Project.status.in_([ProjectStatus.IN_PROGRESS, ProjectStatus.UNDER_REVIEW, ProjectStatus.REVISION_REQUESTED])).count()
    completed_projects = Project.query.filter_by(status=ProjectStatus.COMPLETED).count()

    # Financial stats
    payments = Payment.query.filter(Payment.status.in_(['escrow_held', 'released'])).all()
    total_revenue = sum(float(p.amount) for p in payments)

    # Growth rate (users created in past 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    new_users_30d   = User.query.filter(User.created_at >= thirty_days_ago).count()
    monthly_growth  = round((new_users_30d / max(1, total_users - new_users_30d)) * 100, 1)

    # Category Statistics
    category_stats = {}
    for cat in EditorCategory:
        count = EditorProfile.query.filter_by(category=cat).count()
        category_stats[cat.value] = count

    return success_response(
        data={
            'stats': {
                'total_users':         total_users,
                'total_clients':       total_clients,
                'total_editors':       total_editors,
                'total_projects':      total_projects,
                'active_projects':     active_projects,
                'completed_projects':  completed_projects,
                'total_revenue':       total_revenue,
                'monthly_growth_pct':  monthly_growth,
            },
            'category_distribution': category_stats,
        },
        message="Admin analytics dashboard loaded successfully."
    )


def list_all_users(current_user: dict):
    """
    GET /api/admin/users
    Lists users with role and search filters.
    """
    _, err = _require_admin(current_user)
    if err:
        return err

    page     = max(1, request.args.get('page', 1, type=int))
    per_page = min(100, max(1, request.args.get('per_page', 20, type=int)))
    role_filter = request.args.get('role', '').strip().lower()
    search_q    = request.args.get('search', '').strip()

    query = User.query

    if role_filter == 'client':
        query = query.filter_by(role=UserRole.CLIENT)
    elif role_filter == 'editor':
        query = query.filter_by(role=UserRole.EDITOR)

    if search_q:
        like = f"%{search_q}%"
        query = query.filter(User.full_name.ilike(like) | User.email.ilike(like))

    query = query.order_by(User.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    users_data = []
    for u in pagination.items:
        ud = u.to_dict()
        if u.role == UserRole.EDITOR and u.editor_profile:
            ud['is_verified'] = u.editor_profile.is_verified
        else:
            ud['is_verified'] = True
        users_data.append(ud)

    return paginated_response(
        items=users_data,
        total=pagination.total,
        page=page,
        per_page=per_page,
        message=f"Fetched {pagination.total} users."
    )


def update_user_status(current_user: dict, user_id: int):
    """
    PATCH /api/admin/users/<user_id>/status
    Body: { action: 'suspend' | 'activate' | 'verify' | 'delete' }
    """
    _, err = _require_admin(current_user)
    if err:
        return err

    target_user = User.query.get(user_id)
    if not target_user:
        return error_response(message="User not found.", status_code=404)

    data = request.get_json(silent=True) or {}
    action = (data.get('action') or '').strip().lower()

    try:
        if action == 'suspend':
            target_user.is_active = False
            msg = f"User {target_user.full_name} suspended."
        elif action == 'activate':
            target_user.is_active = True
            msg = f"User {target_user.full_name} activated."
        elif action == 'verify':
            if target_user.editor_profile:
                target_user.editor_profile.is_verified = True
            msg = f"Editor {target_user.full_name} verified."
        elif action == 'delete':
            db.session.delete(target_user)
            db.session.commit()
            return success_response(message=f"User {target_user.full_name} deleted.")
        else:
            return error_response(message="Invalid action. Must be 'suspend', 'activate', 'verify', or 'delete'.", status_code=422)

        db.session.commit()
        return success_response(message=msg)
    except Exception as e:
        db.session.rollback()
        return error_response(message=f"Failed to update user status: {str(e)}", status_code=500)


def list_all_projects(current_user: dict):
    """
    GET /api/admin/projects
    Admin view of all platform projects.
    """
    _, err = _require_admin(current_user)
    if err:
        return err

    projects = Project.query.order_by(Project.created_at.desc()).limit(100).all()
    p_data = [p.to_dict() for p in projects]

    return success_response(data={'projects': p_data}, message=f"Fetched {len(p_data)} projects.")


def list_all_payments(current_user: dict):
    """
    GET /api/admin/payments
    Admin view of financial ledger transactions and escrows.
    """
    _, err = _require_admin(current_user)
    if err:
        return err

    payments = Payment.query.order_by(Payment.created_at.desc()).limit(100).all()
    p_data = [p.to_dict() for p in payments]

    return success_response(data={'payments': p_data}, message=f"Fetched {len(p_data)} payment records.")
