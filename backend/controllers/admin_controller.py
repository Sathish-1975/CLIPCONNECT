"""
============================================================
ClipConnect - Admin Controller
============================================================
Why this file exists:
  Provides controller logic for the complete Admin Control Panel, including system analytics,
  user moderation (verify/suspend/delete), project supervision, and financial audit logs.

What it does:
  - `get_admin_dashboard_stats()`: Computes all required stats for dashboard cards, recent activity, revenue, notifications.
  - `list_all_users()`: Returns paginated user listing with role filtering, client activity stats, and editor response stats.
  - `update_user_status()`: Modifies user account status (active, suspended, verified, deleted).
  - `list_all_projects()`: Provides admin oversight of all platform project postings.
  - `list_all_payments()`: Provides admin financial ledger oversight for deposits, escrows, and releases.
  - `list_all_proposals()`: Provides admin oversight of all hire requests (proposals).

How it integrates with the rest of the application:
  - Exposed via `/api/admin/*` endpoints in `admin_routes.py`.
  - Requires Admin role authorization.
  - Consumed by `admin-dashboard.html` and `admin-dashboard.js`.
============================================================
"""

from datetime import datetime, timezone, timedelta
from flask import request, current_app

from database import db
from models.user_model import User, UserRole
from models.editor_profile_model import EditorProfile, EditorCategory, AvailabilityStatus
from models.client_profile_model import ClientProfile
from models.project_model import Project, ProjectStatus
from models.payment_model import Payment, Transaction
from models.review_model import Review
from models.proposal_model import Proposal
from models.notification_model import Notification
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
    active_editors = EditorProfile.query.filter(EditorProfile.availability_status != AvailabilityStatus.ON_VACATION).count()

    total_projects     = Project.query.filter(Project.status != ProjectStatus.DELETED).count()
    active_projects    = Project.query.filter(Project.status.in_([ProjectStatus.IN_PROGRESS, ProjectStatus.UNDER_REVIEW, ProjectStatus.REVISION_REQUESTED])).count()
    completed_projects = Project.query.filter_by(status=ProjectStatus.COMPLETED).count()
    cancelled_projects = Project.query.filter_by(status=ProjectStatus.CANCELLED).count()

    pending_hire_requests = Proposal.query.filter(Proposal.status.in_(['pending', 'invited'])).count()
    accepted_hire_requests = Proposal.query.filter_by(status='accepted').count()

    # Financial stats
    deposits = Transaction.query.filter_by(type='deposit', status='success').all()
    total_revenue = sum(float(tx.amount) for tx in deposits)
    
    payments = Payment.query.filter(Payment.status.in_(['escrow_held', 'paid', 'released'])).all()
    total_transactions = len(payments)

    today = datetime.utcnow().date()
    today_revenue = sum(float(tx.amount) for tx in deposits if tx.created_at and tx.created_at.date() == today)

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    monthly_revenue = sum(float(tx.amount) for tx in deposits if tx.created_at and tx.created_at >= thirty_days_ago)

    completed_payments = Payment.query.filter(Payment.status.in_(['paid', 'released'])).count()
    
    # Calculate pending payments as the sum of budgets of all active projects (accepted project money)
    active_projs = Project.query.filter(Project.status.in_([ProjectStatus.IN_PROGRESS, ProjectStatus.UNDER_REVIEW, ProjectStatus.REVISION_REQUESTED])).all()
    pending_payments = sum(float(p.budget) for p in active_projs if p.budget)

    refunds = Payment.query.filter_by(status='refunded').count()

    # Growth rate (users created in past 30 days)
    new_users_30d   = User.query.filter(User.created_at >= thirty_days_ago).count()
    monthly_growth  = round((new_users_30d / max(1, total_users - new_users_30d)) * 100, 1)

    # Recent Activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_projects_q = Project.query.order_by(Project.created_at.desc()).limit(5).all()
    recent_proposals = Proposal.query.order_by(Proposal.created_at.desc()).limit(5).all()

    activities = []
    for u in recent_users:
        activities.append({'type': f"New {u.role.value} registered", 'text': f"{u.full_name} joined the platform.", 'date': u.created_at})
    for p in recent_projects_q:
        activities.append({'type': "New project posted", 'text': f"{p.client.full_name if p.client else 'Someone'} posted '{p.title}'.", 'date': p.created_at})
        if p.status == ProjectStatus.COMPLETED:
            activities.append({'type': "Project completed", 'text': f"'{p.title}' was marked as completed.", 'date': p.updated_at or p.created_at})
    for pr in recent_proposals:
        if pr.status == 'invited':
            activities.append({'type': "Client hired an editor", 'text': f"Hire request sent for Project #{pr.project_id}.", 'date': pr.created_at})
        elif pr.status == 'accepted':
            activities.append({'type': "Editor accepted request", 'text': f"Editor accepted hire request for Project #{pr.project_id}.", 'date': pr.created_at})
        elif pr.status == 'rejected':
            activities.append({'type': "Editor declined request", 'text': f"Editor declined hire request for Project #{pr.project_id}.", 'date': pr.created_at})

    activities.sort(key=lambda x: (x['date'] or datetime.min).replace(tzinfo=timezone.utc).timestamp(), reverse=True)
    recent_activity = activities[:15]
    for act in recent_activity:
        if act['date']: act['date'] = act['date'].isoformat()

    # Category Statistics
    category_stats = {}
    for cat in EditorCategory:
        count = EditorProfile.query.filter_by(category=cat).count()
        category_stats[cat.value] = count
        
    # Admin Notifications (from system Notification table)
    admin_notifs = []
    recent_notifs = Notification.query.order_by(Notification.created_at.desc()).limit(15).all()
    for n in recent_notifs:
        admin_notifs.append({
            'title': n.title,
            'message': n.message,
            'created_at': n.created_at.isoformat() if n.created_at else None,
            'type': n.type,
            'is_read': n.is_read
        })

    return success_response(
        data={
            'stats': {
                'total_users':         total_users,
                'total_clients':       total_clients,
                'total_editors':       total_editors,
                'active_editors':      active_editors,
                'total_projects':      total_projects,
                'active_projects':     active_projects,
                'pending_hire_requests': pending_hire_requests,
                'accepted_hire_requests': accepted_hire_requests,
                'completed_projects':  completed_projects,
                'cancelled_projects':  cancelled_projects,
                'total_revenue':       total_revenue,
                'total_transactions':  total_transactions,
                'today_revenue':       today_revenue,
                'monthly_revenue':     monthly_revenue,
                'completed_payments':  completed_payments,
                'pending_payments':    pending_payments,
                'refunds':             refunds,
                'monthly_growth_pct':  monthly_growth,
            },
            'recent_activity': recent_activity,
            'admin_notifications': admin_notifs,
            'category_distribution': category_stats,
        },
        message="Admin analytics dashboard loaded successfully."
    )


def list_all_users(current_user: dict):
    """
    GET /api/admin/users
    Lists users with role and search filters. Now includes extended client/editor activity stats.
    """
    _, err = _require_admin(current_user)
    if err:
        return err

    page     = max(1, request.args.get('page', 1, type=int))
    per_page = min(100, max(1, request.args.get('per_page', 50, type=int)))
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
        ud['is_verified'] = True
        
        # Extended stats for Client Activity and Editor Responses
        if u.role == UserRole.EDITOR:
            if u.editor_profile:
                ud['is_verified'] = u.editor_profile.is_verified
                ud['current_availability'] = u.editor_profile.availability_status.value if u.editor_profile.availability_status else 'unknown'
            
            proposals = Proposal.query.filter_by(editor_id=u.id).all()
            assigned = len(proposals)
            accepted = len([p for p in proposals if p.status == 'accepted'])
            declined = len([p for p in proposals if p.status == 'rejected'])
            completed = Project.query.filter_by(hired_editor_id=u.id, status=ProjectStatus.COMPLETED).count()
            
            ud['editor_stats'] = {
                'projects_assigned': assigned,
                'projects_accepted': accepted,
                'projects_declined': declined,
                'projects_completed': completed,
                'acceptance_rate': f"{round((accepted/assigned)*100, 1)}%" if assigned > 0 else "0%",
                'completion_rate': f"{round((completed/accepted)*100, 1)}%" if accepted > 0 else "0%",
            }
        elif u.role == UserRole.CLIENT:
            projects = Project.query.filter_by(client_id=u.id).all()
            posted = len(projects)
            active = len([p for p in projects if p.status in [ProjectStatus.IN_PROGRESS, ProjectStatus.UNDER_REVIEW, ProjectStatus.REVISION_REQUESTED]])
            completed = len([p for p in projects if p.status == ProjectStatus.COMPLETED])
            total_spent = sum(float(p.budget) for p in projects if p.status == ProjectStatus.COMPLETED and p.budget)
            
            ud['client_stats'] = {
                'projects_posted': posted,
                'projects_active': active,
                'projects_completed': completed,
                'total_amount_spent': total_spent,
            }
            
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
    Admin view of all platform projects, enriched with client/editor names and progress.
    """
    _, err = _require_admin(current_user)
    if err:
        return err

    projects = Project.query.order_by(Project.created_at.desc()).limit(200).all()
    p_data = []
    for p in projects:
        d = p.to_dict()
        d['client_name'] = p.client.full_name if p.client else 'Unknown'
        d['editor_name'] = 'Unknown'
        if p.hired_editor_id:
            editor = User.query.get(p.hired_editor_id)
            if editor: d['editor_name'] = editor.full_name
            
        d['completion_pct'] = 0
        if p.status == ProjectStatus.COMPLETED: d['completion_pct'] = 100
        elif p.status == ProjectStatus.UNDER_REVIEW: d['completion_pct'] = 90
        elif p.status == ProjectStatus.REVISION_REQUESTED: d['completion_pct'] = 75
        elif p.status == ProjectStatus.IN_PROGRESS: d['completion_pct'] = 50
        elif p.status == ProjectStatus.WAITING_FOR_EDITOR: d['completion_pct'] = 10
        
        # Safe format dates
        d['deadline'] = p.due_date.isoformat() if hasattr(p, 'due_date') and p.due_date else None
        p_data.append(d)

    return success_response(data={'projects': p_data}, message=f"Fetched {len(p_data)} projects.")


def list_all_proposals(current_user: dict):
    """
    GET /api/admin/proposals
    Admin view of all hire requests (proposals).
    """
    _, err = _require_admin(current_user)
    if err:
        return err
        
    proposals = Proposal.query.order_by(Proposal.created_at.desc()).limit(200).all()
    p_data = []
    for p in proposals:
        d = p.to_dict()
        d['client_name'] = p.project.client.full_name if (p.project and p.project.client) else 'Unknown'
        d['editor_name'] = p.editor.full_name if p.editor else 'Unknown'
        d['project_title'] = p.project.title if p.project else 'Unknown'
        d['sent_date'] = p.created_at.isoformat() if p.created_at else None
        
        is_acc = p.status == 'accepted'
        is_rej = p.status == 'rejected'
        # Approximate update date for accept/reject
        d['accepted_date'] = p.created_at.isoformat() if is_acc and p.created_at else None
        d['declined_date'] = p.created_at.isoformat() if is_rej and p.created_at else None
        
        d['current_progress'] = p.project.status.value if p.project and p.project.status else 'Unknown'
        p_data.append(d)

    return success_response(data={'proposals': p_data}, message=f"Fetched {len(p_data)} hire requests.")


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
