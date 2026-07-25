"""
============================================================
ClipConnect - Revision Controller
============================================================
Why this file exists:
  Provides controller logic for managing project revision requests between
  clients and editors.

What it does:
  - `request_revision()`: Allows clients to submit a revision request with comments and reference files.
  - `get_project_revisions()`: Retrieves all revision requests and history for a project.
  - `update_revision()`: Allows editors to respond to revision requests, upload updated work files,
    and mark revisions as completed.

How it integrates with the rest of the application:
  - Linked to `Project`, `RevisionRequest`, and `Notification` models.
  - Invoked by routes in `project_routes.py`.
  - Dispatches notifications to client and editor on state transitions.
============================================================
"""

from flask import request, current_app
from database import db
from models.project_model import Project, ProjectStatus
from models.revision_model import RevisionRequest
from utils.response_helper import success_response, error_response
from utils.notification_helper import create_notification


def request_revision(current_user: dict, project_id: int):
    """
    POST /api/projects/<project_id>/revisions
    Client submits a revision request.
    """
    if current_user.get('role') != 'client':
        return error_response(message="Only clients can request revisions.", status_code=403)

    project = Project.query.get(project_id)
    if not project or project.status == ProjectStatus.DELETED:
        return error_response(message="Project not found.", status_code=404)

    if project.client_id != current_user['user_id']:
        return error_response(message="You can only request revisions on your own projects.", status_code=403)

    if not project.hired_editor_id:
        return error_response(message="No editor assigned to this project.", status_code=400)

    data = request.get_json(silent=True) or {}
    comments = (data.get('comments') or '').strip()
    if not comments:
        return error_response(message="Revision comments are required.", status_code=422)

    title = (data.get('title') or 'Revision Request').strip()
    reference_files = data.get('reference_files') or []

    revision = RevisionRequest(
        project_id=project_id,
        client_id=current_user['user_id'],
        editor_id=project.hired_editor_id,
        title=title,
        comments=comments,
        reference_files=reference_files,
        status='pending'
    )

    try:
        # Update project status and timeline
        project.status = ProjectStatus.REVISION_REQUESTED
        project.add_timeline_event(
            status_str='revision_requested',
            title='Revision Requested',
            note=comments[:100] + '...' if len(comments) > 100 else comments
        )

        db.session.add(revision)
        db.session.commit()

        # Notify editor
        create_notification(
            user_id=project.hired_editor_id,
            title="🔄 Revision Requested",
            message=f"Client requested a revision for '{project.title}'.",
            type_str="revision_requested",
            related_project_id=project_id
        )

        return success_response(
            data={'revision': revision.to_dict(), 'project': project.to_dict()},
            message="Revision request submitted successfully.",
            status_code=201
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Request revision error: {e}")
        return error_response(message=f"Failed to submit revision request: {str(e)}", status_code=500)


def get_project_revisions(current_user: dict, project_id: int):
    """
    GET /api/projects/<project_id>/revisions
    Fetch revision history for a project. Accessible by client or hired editor.
    """
    project = Project.query.get(project_id)
    if not project or project.status == ProjectStatus.DELETED:
        return error_response(message="Project not found.", status_code=404)

    user_id = current_user['user_id']
    if project.client_id != user_id and project.hired_editor_id != user_id:
        return error_response(message="You do not have access to this project's revisions.", status_code=403)

    revisions = RevisionRequest.query.filter_by(project_id=project_id).order_by(RevisionRequest.created_at.desc()).all()
    rev_data = [r.to_dict() for r in revisions]

    return success_response(data={'revisions': rev_data}, message=f"Fetched {len(rev_data)} revisions.")


def update_revision(current_user: dict, project_id: int, revision_id: int):
    """
    PUT /api/projects/<project_id>/revisions/<revision_id>
    Editor submits updated work files, notes, or marks revision completed.
    """
    if current_user.get('role') != 'editor':
        return error_response(message="Only editors can update revision requests.", status_code=403)

    revision = RevisionRequest.query.get(revision_id)
    if not revision or revision.project_id != project_id:
        return error_response(message="Revision request not found.", status_code=404)

    if revision.editor_id != current_user['user_id']:
        return error_response(message="You are not assigned to this revision.", status_code=403)

    data = request.get_json(silent=True) or {}
    status_val = (data.get('status') or '').strip().lower()
    editor_notes = data.get('editor_notes')
    updated_files = data.get('updated_work_files')

    if editor_notes is not None:
        revision.editor_notes = editor_notes.strip()

    if updated_files is not None and isinstance(updated_files, list):
        revision.updated_work_files = updated_files

    if status_val in ('pending', 'in_progress', 'completed'):
        revision.status = status_val

    try:
        project = Project.query.get(project_id)
        if revision.status == 'completed' and project:
            project.status = ProjectStatus.UNDER_REVIEW
            project.add_timeline_event(
                status_str='under_review',
                title='Revision Completed / Submitted for Review',
                note=revision.editor_notes or 'Updated work uploaded.'
            )

            # Add updated files to project_files
            if revision.updated_work_files:
                pfiles = list(project.project_files or [])
                pfiles.extend(revision.updated_work_files)
                project.project_files = pfiles

            # Notify client
            create_notification(
                user_id=project.client_id,
                title="✅ Revision Updated",
                message=f"Editor uploaded updated work for project '{project.title}'.",
                type_str="general",
                related_project_id=project_id
            )

        db.session.commit()

        return success_response(
            data={'revision': revision.to_dict()},
            message="Revision updated successfully."
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update revision error: {e}")
        return error_response(message=f"Failed to update revision: {str(e)}", status_code=500)
