"""
============================================================
ClipConnect - Hire Controller
============================================================
Why this file exists:
  Provides controller logic for client-to-editor hire workflow: sending hire requests,
  accepting requests, and declining requests.

What it does:
  - `submit_hire_request()`: Client sends direct hire request for a project to an editor.
  - `accept_hire()`: Editor accepts hire request, project transitions to IN_PROGRESS,
    timeline event is added, and other proposals are auto-rejected.
  - `reject_hire()`: Editor rejects hire request with optional reason.

How it integrates with the rest of the application:
  - Exposed via `/api/hire`, `/api/hire/accept`, `/api/hire/reject` in `api_routes.py`.
  - Updates `Project` status, `Proposal` status, and appends `timeline` events.
  - Triggers real-time user notifications via `utils/notification_helper.py`.
============================================================
"""

from flask import request, current_app
from database import db
from models.user_model import User, UserRole
from models.project_model import Project, ProjectStatus
from models.proposal_model import Proposal
from utils.response_helper import success_response, error_response
from utils.notification_helper import create_notification


def submit_hire_request(current_user: dict):
    """
    POST /api/hire
    Body: { project_id, editor_id, message (optional) }
    Client sends a direct hire invitation to an editor for a project.
    Creates a proposal with status 'invited'.
    """
    if current_user.get('role') != 'client':
        return error_response(message="Only clients can send hire requests.", status_code=403)

    data = request.get_json(silent=True) or {}
    project_id = data.get('project_id')
    editor_id  = data.get('editor_id')
    message    = (data.get('message') or '').strip()

    if not project_id:
        return error_response(message="project_id is required.", status_code=422)
    if not editor_id:
        return error_response(message="editor_id is required.", status_code=422)

    # Validate project
    project = Project.query.get(project_id)
    if not project or project.status == ProjectStatus.DELETED:
        return error_response(message="Project not found.", status_code=404)
    if project.client_id != current_user['user_id']:
        return error_response(message="You can only hire editors for your own projects.", status_code=403)

    # Validate editor
    editor = User.query.get(editor_id)
    if not editor or editor.role != UserRole.EDITOR or not editor.is_active:
        return error_response(message="Editor not found.", status_code=404)

    # Check for existing proposal
    existing = Proposal.query.filter_by(project_id=project_id, editor_id=editor_id).first()
    if existing:
        return error_response(
            message=f"A proposal already exists for this editor (status: {existing.status}).",
            status_code=400
        )

    # Create an 'invited' proposal
    proposal = Proposal(
        project_id=project_id,
        editor_id=editor_id,
        cover_letter=message or f"Direct hire invitation for project: {project.title}",
        proposed_price=project.budget or 0,
        status='invited'
    )

    try:
        project.status = ProjectStatus.WAITING_FOR_EDITOR
        project.add_timeline_event(
            status_str='waiting_for_editor',
            title='Hire Invitation Sent',
            note=f"Client invited {editor.full_name} to work on this project."
        )

        db.session.add(proposal)
        db.session.commit()

        # Notify the editor
        create_notification(
            user_id=editor_id,
            title="🤝 Hire Invitation",
            message=f"You've been invited to work on project '{project.title}'.",
            type_str="project_assigned",
            related_project_id=project_id
        )

        # Notify the client (so they see it in their notification panel)
        create_notification(
            user_id=current_user['user_id'],
            title="📤 Hire Request Sent",
            message=f"You successfully invited {editor.full_name} to work on '{project.title}'.",
            type_str="proposal_submitted",
            related_project_id=project_id
        )

        return success_response(
            data={'proposal': proposal.to_dict()},
            message="Hire invitation sent successfully!",
            status_code=201
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Submit hire request error: {e}")
        return error_response(message=f"Failed to send hire request: {str(e)}", status_code=500)


def accept_hire(current_user: dict):
    """
    PUT /api/hire/accept
    Body: { proposal_id }
    Editor accepts a hire invitation / proposal.
    """
    if current_user.get('role') != 'editor':
        return error_response(message="Only editors can accept hire requests.", status_code=403)

    data = request.get_json(silent=True) or {}
    proposal_id = data.get('proposal_id')
    if not proposal_id:
        return error_response(message="proposal_id is required.", status_code=422)

    proposal = Proposal.query.get(proposal_id)
    if not proposal:
        return error_response(message="Proposal not found.", status_code=404)

    if proposal.editor_id != current_user['user_id']:
        return error_response(message="This proposal is not for you.", status_code=403)

    if proposal.status not in ('pending', 'invited'):
        return error_response(message=f"Cannot accept a proposal with status '{proposal.status}'.", status_code=400)

    project = Project.query.get(proposal.project_id)
    if not project:
        return error_response(message="Associated project not found.", status_code=404)

    try:
        # Accept this proposal
        proposal.status = 'accepted'

        # Update project
        project.hired_editor_id = current_user['user_id']
        project.status = ProjectStatus.IN_PROGRESS
        project.add_timeline_event(
            status_str='in_progress',
            title='Project In Progress',
            note='Editor accepted project assignment.'
        )

        # Reject all other proposals for this project
        other_proposals = Proposal.query.filter(
            Proposal.project_id == project.id,
            Proposal.id != proposal.id,
            Proposal.status.in_(['pending', 'invited'])
        ).all()
        for p in other_proposals:
            p.status = 'rejected'
            create_notification(
                user_id=p.editor_id,
                title="Proposal Rejected",
                message=f"Your proposal for project '{project.title}' was not selected.",
                type_str="proposal_rejected",
                related_project_id=project.id
            )

        db.session.commit()

        # Notify client
        create_notification(
            user_id=project.client_id,
            title="✅ Hire Accepted",
            message=f"Editor accepted your hire request for project '{project.title}'.",
            type_str="proposal_accepted",
            related_project_id=project.id
        )

        # Notify editor (confirmation)
        create_notification(
            user_id=current_user['user_id'],
            title="Project Assigned 🎯",
            message=f"You accepted the project '{project.title}'. Time to get started!",
            type_str="project_assigned",
            related_project_id=project.id
        )

        return success_response(
            data={'proposal': proposal.to_dict(), 'project': project.to_dict()},
            message="Hire accepted! Project is now in progress."
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Accept hire error: {e}")
        return error_response(message=f"Failed to accept hire: {str(e)}", status_code=500)


def reject_hire(current_user: dict):
    """
    PUT /api/hire/reject
    Body: { proposal_id, reason (optional) }
    Editor rejects a hire invitation / proposal.
    """
    if current_user.get('role') != 'editor':
        return error_response(message="Only editors can reject hire requests.", status_code=403)

    data = request.get_json(silent=True) or {}
    proposal_id = data.get('proposal_id')
    reason      = (data.get('reason') or '').strip()

    if not proposal_id:
        return error_response(message="proposal_id is required.", status_code=422)

    proposal = Proposal.query.get(proposal_id)
    if not proposal:
        return error_response(message="Proposal not found.", status_code=404)

    if proposal.editor_id != current_user['user_id']:
        return error_response(message="This proposal is not for you.", status_code=403)

    if proposal.status not in ('pending', 'invited'):
        return error_response(message=f"Cannot reject a proposal with status '{proposal.status}'.", status_code=400)

    project = Project.query.get(proposal.project_id)

    try:
        proposal.status = 'rejected'
        db.session.commit()

        # Notify client
        if project:
            editor = User.query.get(current_user['user_id'])
            editor_name = editor.full_name if editor else 'An editor'
            msg = f"{editor_name} declined the invite for project '{project.title}'."
            if reason:
                msg += f" Reason: {reason}"
            create_notification(
                user_id=project.client_id,
                title="❌ Hire Declined",
                message=msg,
                type_str="proposal_rejected",
                related_project_id=project.id
            )

        return success_response(
            data={'proposal': proposal.to_dict()},
            message="Hire request declined."
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Reject hire error: {e}")
        return error_response(message=f"Failed to reject hire: {str(e)}", status_code=500)
