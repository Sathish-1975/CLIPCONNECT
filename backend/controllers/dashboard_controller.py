# backend/controllers/dashboard_controller.py
"""
Dashboard controller for ClipConnect.
Provides endpoints for:
- Client dashboard (draft, active, completed, cancelled, archived projects)
- Editor dashboard (applied proposals, active projects, completed projects, rejected/withdrawn proposals, saved projects placeholder)
"""

from flask import request
from utils.response_helper import success_response, error_response
from models.project_model import Project, ProjectStatus
from models.proposal_model import Proposal
from database import db


def get_client_dashboard(current_user: dict):
    """Return a grouped view of a client's projects.
    Expected groups:
        draft, active, completed, cancelled, archived
    """
    if current_user.get('role') != 'client':
        return error_response(message='Only clients can view this dashboard.', status_code=403)

    projects = Project.query.filter_by(client_id=current_user['user_id']).all()
    grouped = {
        'draft': [],
        'active': [],
        'completed': [],
        'cancelled': [],
        'archived': []
    }
    for p in projects:
        status = p.status.value if hasattr(p.status, 'value') else str(p.status)
        if status == ProjectStatus.DRAFT.value:
            grouped['draft'].append(p.to_dict())
        elif status == ProjectStatus.IN_PROGRESS.value:
            grouped['active'].append(p.to_dict())
        elif status == ProjectStatus.CLOSED.value:
            grouped['completed'].append(p.to_dict())
        elif status == ProjectStatus.DELETED.value:
            grouped['archived'].append(p.to_dict())
        else:
            # Any other status treated as cancelled for now
            grouped['cancelled'].append(p.to_dict())
    return success_response(data=grouped, message='Client dashboard retrieved.')


def get_editor_dashboard(current_user: dict):
    """Return a grouped view of an editor's proposals and related projects.
    Expected groups:
        applied, active, completed, rejected, saved (placeholder)
    """
    if current_user.get('role') != 'editor':
        return error_response(message='Only editors can view this dashboard.', status_code=403)

    proposals = Proposal.query.filter_by(editor_id=current_user['user_id']).all()
    grouped = {
        'applied': [],   # pending or shortlisted proposals
        'active': [],    # accepted proposals where project is in progress
        'completed': [], # proposals whose project is closed
        'rejected': [],  # rejected or withdrawn proposals
        'saved': []      # placeholder for future saved projects feature
    }

    for prop in proposals:
        prop_dict = prop.to_dict()
        status = prop.status.lower() if isinstance(prop.status, str) else str(prop.status).lower()
        if status in ('pending', 'shortlisted'):
            grouped['applied'].append(prop_dict)
        elif status == 'accepted':
            # Ensure the linked project is still active
            if prop.project and prop.project.status == ProjectStatus.IN_PROGRESS:
                grouped['active'].append(prop_dict)
            else:
                grouped['applied'].append(prop_dict)
        elif status in ('rejected', 'withdrawn'):
            grouped['rejected'].append(prop_dict)
        else:
            grouped['applied'].append(prop_dict)

    # Completed proposals: those whose project status is CLOSED
    for prop in proposals:
        if prop.project and prop.project.status == ProjectStatus.CLOSED:
            grouped['completed'].append(prop.to_dict())

    return success_response(data=grouped, message='Editor dashboard retrieved.')
