"""
============================================================
ClipConnect - Project Controller
============================================================
Why this file exists:
  Provides controller logic for client project creation, editing, listing,
  publishing, draft saving, status management, timeline tracking, and soft deleting.

What it does:
  - `create_project()`: Validates inputs (title, budget, priority, experience, software),
    creates a Project record, and initializes timeline tracking.
  - `get_public_projects()`: Lists public published projects with pagination & filtering.
  - `get_my_projects()`: Lists client's own projects across all statuses.
  - `get_project_by_id()`: Fetches project details, proposal counts, and saved state.
  - `update_project()`: Modifies an existing project owned by current user.
  - `change_project_status()`: Manages status transitions and fires notifications.
  - `delete_project()`: Soft deletes (status = 'deleted') project.

How it integrates with the rest of the application:
  - Consumed by `project_routes.py`.
  - Interfaces with `models/project_model.py`, `models/user_model.py`, `models/proposal_model.py`.
  - Dispatches notifications via `utils/notification_helper.py`.
============================================================
"""

from datetime import datetime
from flask import request, current_app
from database import db
from models.user_model import User, UserRole
from models.editor_profile_model import EditorCategory
from models.project_model import Project, BudgetType, ProjectVisibility, ProjectPriority, ProjectStatus
from utils.response_helper import success_response, error_response, paginated_response
from utils.upload_helper import save_upload


def create_project(current_user: dict):
    """
    POST /api/projects
    Create a new project (Draft or Published).
    Only Clients can post projects.
    """
    if current_user.get('role') != 'client':
        return error_response(message="Only clients can post projects.", status_code=403)

    data = request.get_json(silent=True) or {}

    title = (data.get('title') or '').strip()
    description = (data.get('description') or '').strip()
    category_val = (data.get('category') or '').strip().lower()
    budget = data.get('budget')
    is_draft = data.get('is_draft', False)

    if not title:
        return error_response(message="Project title is required.", status_code=422)
    if not description:
        return error_response(message="Project description is required.", status_code=422)

    # Category validation
    category_enum = EditorCategory.YOUTUBE
    if category_val:
        try:
            category_enum = EditorCategory(category_val)
        except ValueError:
            valid = [e.value for e in EditorCategory]
            return error_response(message=f"Invalid category. Must be one of: {', '.join(valid)}", status_code=422)

    # Budget validation
    try:
        budget_num = float(budget) if budget is not None else 0.0
    except (ValueError, TypeError):
        return error_response(message="Budget must be a valid number.", status_code=422)

    # Budget type
    budget_type_val = (data.get('budget_type') or 'fixed').strip().lower()
    try:
        budget_type_enum = BudgetType(budget_type_val)
    except ValueError:
        budget_type_enum = BudgetType.FIXED

    # Visibility
    visibility_val = (data.get('visibility') or 'public').strip().lower()
    try:
        visibility_enum = ProjectVisibility(visibility_val)
    except ValueError:
        visibility_enum = ProjectVisibility.PUBLIC

    # Priority
    priority_val = (data.get('priority') or 'medium').strip().lower()
    try:
        priority_enum = ProjectPriority(priority_val)
    except ValueError:
        priority_enum = ProjectPriority.MEDIUM

    experience_required = (data.get('experience_required') or 'Intermediate').strip()

    # Deadline
    deadline_dt = None
    if data.get('deadline'):
        try:
            deadline_dt = datetime.fromisoformat(data['deadline'].replace('Z', '+00:00'))
        except ValueError:
            pass

    # Status
    status_enum = ProjectStatus.DRAFT if is_draft else ProjectStatus.PUBLISHED

    project = Project(
        client_id=current_user['user_id'],
        title=title,
        category=category_enum,
        description=description,
        reference_links=data.get('reference_links') or [],
        sample_files=data.get('sample_files') or [],
        budget=budget_num,
        budget_type=budget_type_enum,
        deadline=deadline_dt,
        required_skills=data.get('required_skills') or [],
        preferred_software=data.get('preferred_software') or [],
        experience_required=experience_required,
        priority=priority_enum,
        visibility=visibility_enum,
        editors_required=int(data.get('editors_required', 1)),
        status=status_enum
    )

    # Initialize timeline event
    initial_event_title = "Project Draft Saved" if is_draft else "Project Created & Published"
    project.add_timeline_event(
        status_str=status_enum.value,
        title=initial_event_title,
        note="Project created by client."
    )

    try:
        db.session.add(project)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create project error: {e}")
        return error_response(message="Failed to create project.", status_code=500)

    msg = "Project draft saved successfully." if is_draft else "Project published successfully!"
    return success_response(data={'project': project.to_dict()}, message=msg, status_code=201)


def get_public_projects():
    """
    GET /api/projects
    Get all public published projects with filtering and pagination.
    """
    page = max(1, request.args.get('page', 1, type=int))
    per_page = min(50, max(1, request.args.get('per_page', 10, type=int)))

    query = Project.query.filter(
        Project.status == ProjectStatus.PUBLISHED,
        Project.visibility == ProjectVisibility.PUBLIC
    )

    # Filters
    category_val = request.args.get('category', '').strip().lower()
    if category_val:
        try:
            query = query.filter(Project.category == EditorCategory(category_val))
        except ValueError:
            pass

    search_q = request.args.get('search', '').strip()
    if search_q:
        like = f"%{search_q}%"
        query = query.filter(Project.title.ilike(like) | Project.description.ilike(like))

    query = query.order_by(Project.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    projects = [p.to_dict() for p in pagination.items]

    return paginated_response(
        items=projects,
        total=pagination.total,
        page=page,
        per_page=per_page,
        message=f"Found {pagination.total} projects."
    )


def get_my_projects(current_user: dict):
    """
    GET /api/projects/my
    Get client's own projects (all statuses).
    """
    if current_user.get('role') != 'client':
        return error_response(message="Only clients have posted projects.", status_code=403)

    status_filter = request.args.get('status', '').strip().lower()

    query = Project.query.filter(
        Project.client_id == current_user['user_id'],
        Project.status != ProjectStatus.DELETED
    )

    if status_filter:
        try:
            query = query.filter(Project.status == ProjectStatus(status_filter))
        except ValueError:
            pass

    query = query.order_by(Project.created_at.desc())
    projects = [p.to_dict() for p in query.all()]

    return success_response(data={'projects': projects}, message=f"Fetched {len(projects)} projects.")


def get_project_by_id(project_id: int):
    """
    GET /api/projects/<id>
    Get detailed information for a single project.
    """
    from models.proposal_model import Proposal
    from models.saved_project_model import SavedProject
    from utils.jwt_helper import decode_token

    project = Project.query.get(project_id)
    if not project or project.status == ProjectStatus.DELETED:
        return error_response(message="Project not found.", status_code=404)

    proposal_count = Proposal.query.filter_by(project_id=project_id).count()
    project_data = project.to_dict()
    project_data['proposal_count'] = proposal_count

    # Check if saved by current user
    auth_header = request.headers.get('Authorization')
    is_saved = False
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        decoded = decode_token(token)
        if decoded and decoded.get('role') == 'editor':
            is_saved = SavedProject.query.filter_by(
                editor_id=decoded['user_id'],
                project_id=project_id
            ).first() is not None

    project_data['is_saved'] = is_saved
    return success_response(data={'project': project_data}, message="Project details fetched.")


def update_project(current_user: dict, project_id: int):
    """
    PUT /api/projects/<id>
    Update an existing project owned by the client.
    """
    project = Project.query.get(project_id)
    if not project or project.status == ProjectStatus.DELETED:
        return error_response(message="Project not found.", status_code=404)

    if project.client_id != current_user['user_id']:
        return error_response(message="You can only edit your own projects.", status_code=403)

    data = request.get_json(silent=True) or {}

    if 'title' in data:
        t = data['title'].strip()
        if t: project.title = t

    if 'description' in data:
        d = data['description'].strip()
        if d: project.description = d

    if 'category' in data:
        try:
            project.category = EditorCategory(data['category'].strip().lower())
        except ValueError:
            pass

    if 'budget' in data:
        try:
            project.budget = float(data['budget'])
        except (ValueError, TypeError):
            pass

    if 'budget_type' in data:
        try:
            project.budget_type = BudgetType(data['budget_type'].strip().lower())
        except ValueError:
            pass

    if 'visibility' in data:
        try:
            project.visibility = ProjectVisibility(data['visibility'].strip().lower())
        except ValueError:
            pass

    if 'editors_required' in data:
        try:
            project.editors_required = int(data['editors_required'])
        except (ValueError, TypeError):
            pass

    if 'reference_links' in data and isinstance(data['reference_links'], list):
        project.reference_links = data['reference_links']

    if 'sample_files' in data and isinstance(data['sample_files'], list):
        project.sample_files = data['sample_files']

    if 'required_skills' in data and isinstance(data['required_skills'], list):
        project.required_skills = data['required_skills']

    if 'preferred_software' in data and isinstance(data['preferred_software'], list):
        project.preferred_software = data['preferred_software']

    if 'deadline' in data:
        if data['deadline']:
            try:
                project.deadline = datetime.fromisoformat(data['deadline'].replace('Z', '+00:00'))
            except ValueError:
                pass
        else:
            project.deadline = None

    if 'is_draft' in data:
        project.status = ProjectStatus.DRAFT if data['is_draft'] else ProjectStatus.PUBLISHED

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update project error: {e}")
        return error_response(message="Failed to update project.", status_code=500)

    return success_response(data={'project': project.to_dict()}, message="Project updated successfully.")


def change_project_status(current_user: dict, project_id: int):
    """
    PATCH /api/projects/<id>/status
    Update status (publish, close, draft, completed).
    """
    from utils.notification_helper import create_notification
    from datetime import timezone

    project = Project.query.get(project_id)
    if not project or project.status == ProjectStatus.DELETED:
        return error_response(message="Project not found.", status_code=404)

    if project.client_id != current_user['user_id']:
        return error_response(message="You can only manage your own projects.", status_code=403)

    data = request.get_json(silent=True) or {}
    new_status_str = (data.get('status') or '').strip().lower()

    try:
        new_status = ProjectStatus(new_status_str)
        project.status = new_status
        db.session.commit()

        # ── Notification: Project Completed ──────────────────────────────────
        if new_status == ProjectStatus.COMPLETED:
            # Notify the hired editor
            if project.hired_editor_id:
                create_notification(
                    user_id=project.hired_editor_id,
                    title="Project Completed 🎉",
                    message=f"Project '{project.title}' has been marked as completed. Great work!",
                    type_str="project_completed",
                    related_project_id=project_id
                )
            # Notify the client (self-confirmation)
            create_notification(
                user_id=project.client_id,
                title="Project Completed",
                message=f"You marked project '{project.title}' as completed.",
                type_str="project_completed",
                related_project_id=project_id
            )

        # ── Notification: Deadline Near (check on status change too) ─────────
        if project.deadline:
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
            deadline_aware = project.deadline if project.deadline.tzinfo else project.deadline.replace(tzinfo=timezone.utc)
            hours_left = (deadline_aware - now).total_seconds() / 3600
            if 0 < hours_left <= 48:
                # Notify the editor
                if project.hired_editor_id:
                    create_notification(
                        user_id=project.hired_editor_id,
                        title="⏰ Deadline Approaching",
                        message=f"Project '{project.title}' deadline is in {int(hours_left)} hours!",
                        type_str="deadline_near",
                        related_project_id=project_id
                    )
                # Notify the client
                create_notification(
                    user_id=project.client_id,
                    title="⏰ Deadline Approaching",
                    message=f"Project '{project.title}' deadline is in {int(hours_left)} hours.",
                    type_str="deadline_near",
                    related_project_id=project_id
                )

    except ValueError:
        valid = [s.value for s in ProjectStatus]
        return error_response(message=f"Invalid status. Must be one of: {', '.join(valid)}", status_code=422)
    except Exception as e:
        db.session.rollback()
        return error_response(message="Failed to update status.", status_code=500)

    return success_response(data={'project': project.to_dict()}, message=f"Project status updated to {new_status.value}.")


def delete_project(current_user: dict, project_id: int):
    """
    DELETE /api/projects/<id>
    Soft delete project.
    """
    project = Project.query.get(project_id)
    if not project or project.status == ProjectStatus.DELETED:
        return error_response(message="Project not found.", status_code=404)

    if project.client_id != current_user['user_id']:
        return error_response(message="You can only delete your own projects.", status_code=403)

    project.status = ProjectStatus.DELETED
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response(message="Failed to delete project.", status_code=500)

    return success_response(message="Project deleted successfully.")


def upload_sample_file(current_user: dict):
    """
    POST /api/projects/upload-sample
    Upload a sample project file.
    """
    if current_user.get('role') != 'client':
        return error_response(message="Only clients can upload project files.", status_code=403)

    file = request.files.get('file')
    if not file:
        return error_response(message="No file uploaded.", status_code=400)

    try:
        filename = save_upload(file, 'project_samples')
        return success_response(data={
            'filename': filename,
            'url': f"/uploads/project_samples/{filename}"
        }, message="Sample file uploaded successfully.")
    except Exception as e:
        return error_response(message=f"Upload failed: {str(e)}", status_code=422)


def apply_to_project(current_user: dict, project_id: int):
    """
    POST /api/projects/<id>/apply
    Apply to a project as an editor.
    """
    from models.proposal_model import Proposal

    if current_user.get('role') != 'editor':
        return error_response(message="Only editors can apply to projects.", status_code=403)

    project = Project.query.get(project_id)
    if not project or project.status == ProjectStatus.DELETED:
        return error_response(message="Project not found.", status_code=404)

    existing = Proposal.query.filter_by(project_id=project_id, editor_id=current_user['user_id']).first()
    if existing:
        return error_response(message="You have already applied to this project.", status_code=400)

    data = request.get_json(silent=True) or {}
    proposal = Proposal(
        project_id=project_id,
        editor_id=current_user['user_id'],
        cover_letter=data.get('cover_letter', 'Submitted application via project page.'),
        proposed_price=data.get('proposed_price', project.budget or 0),
        status='pending'
    )

    try:
        db.session.add(proposal)
        db.session.commit()

        # Trigger notification to client
        from utils.notification_helper import create_notification
        create_notification(
            user_id=project.client_id,
            title="New Proposal Submitted",
            message=f"An editor applied to your project '{project.title}'.",
            type_str="proposal_submitted",
            related_project_id=project_id
        )

        return success_response(data={'proposal': proposal.to_dict()}, message="Application submitted successfully.")
    except Exception as e:
        db.session.rollback()
        return error_response(message=f"Failed to submit application: {str(e)}", status_code=500)


def hire_editor(current_user: dict, project_id: int):
    """
    POST /api/projects/<id>/hire
    Client hires an editor for the project.
    Changes project status to IN_PROGRESS and sends notifications.
    """
    from models.proposal_model import Proposal
    from utils.notification_helper import create_notification

    if current_user.get('role') != 'client':
        return error_response(message="Only clients can hire editors.", status_code=403)

    project = Project.query.get(project_id)
    if not project or project.status == ProjectStatus.DELETED:
        return error_response(message="Project not found.", status_code=404)

    if project.client_id != current_user['user_id']:
        return error_response(message="You can only hire editors for your own projects.", status_code=403)

    data = request.get_json(silent=True) or {}
    editor_id = data.get('editor_id')
    if not editor_id:
        return error_response(message="editor_id is required.", status_code=400)

    proposal = Proposal.query.filter_by(project_id=project_id, editor_id=editor_id).first()
    if not proposal:
        return error_response(message="Proposal from this editor not found.", status_code=404)

    try:
        # Update project status and hired_editor_id
        project.hired_editor_id = editor_id
        project.status = ProjectStatus.IN_PROGRESS

        # Update proposals status
        proposal.status = 'accepted'

        other_proposals = Proposal.query.filter(
            Proposal.project_id == project_id,
            Proposal.id != proposal.id
        ).all()
        for p in other_proposals:
            p.status = 'rejected'
            create_notification(
                user_id=p.editor_id,
                title="Proposal Rejected",
                message=f"Your proposal for project '{project.title}' was not selected.",
                type_str="proposal_rejected",
                related_project_id=project_id
            )

        db.session.commit()

        # Notify hired editor
        create_notification(
            user_id=editor_id,
            title="Proposal Accepted / Project Assigned",
            message=f"Congratulations! You were hired for project '{project.title}'.",
            type_str="proposal_accepted",
            related_project_id=project_id
        )

        # Notify client
        create_notification(
            user_id=project.client_id,
            title="Project Assigned & In Progress",
            message=f"Project '{project.title}' status is now In Progress.",
            type_str="project_assigned",
            related_project_id=project_id
        )

        return success_response(data={'project': project.to_dict()}, message="Editor hired successfully. Project status updated to In Progress.")
    except Exception as e:
        db.session.rollback()
        return error_response(message=f"Failed to hire editor: {str(e)}", status_code=500)


def editor_update_progress(current_user: dict, project_id: int):
    """
    PATCH /api/projects/<id>/editor-progress
    Editor updates the project progress (e.g. pending, accepted, in_progress).
    """
    if current_user.get('role') != 'editor':
        return error_response(message="Only editors can update project progress.", status_code=403)

    project = Project.query.get(project_id)
    if not project or project.status == ProjectStatus.DELETED:
        return error_response(message="Project not found.", status_code=404)

    if project.hired_editor_id != current_user['user_id']:
        return error_response(message="You are not hired for this project.", status_code=403)

    data = request.get_json(silent=True) or {}
    new_status_str = (data.get('status') or '').strip().lower()

    # Editors should only switch between working statuses
    allowed_statuses = ['pending', 'accepted', 'in_progress']
    if new_status_str not in allowed_statuses:
        return error_response(message=f"Invalid status. Editors can only set: {', '.join(allowed_statuses)}", status_code=422)

    try:
        new_status = ProjectStatus(new_status_str)
        project.status = new_status
        project.add_timeline_event(new_status.value, f"Progress updated to {new_status.value}", "Updated by Editor")
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response(message="Failed to update progress.", status_code=500)

    return success_response(data={'project': project.to_dict()}, message=f"Project progress updated to {new_status.value}.")


def editor_submit_project(current_user: dict, project_id: int):
    """
    POST /api/projects/<id>/submit
    Editor submits completed files and notes. 
    Changes status to COMPLETED, notifies client, records revenue.
    """
    from utils.notification_helper import create_notification
    from utils.upload_helper import save_upload
    from models.payment_model import Payment, Transaction
    from datetime import datetime, timezone

    if current_user.get('role') != 'editor':
        return error_response(message="Only editors can submit projects.", status_code=403)
def upload_sample_file(current_user: dict):
    """
    POST /api/projects/upload-sample
    Upload a sample project file.
    """
    if current_user.get('role') != 'client':
        return error_response(message="Only clients can upload project files.", status_code=403)

    file = request.files.get('file')
    if not file:
        return error_response(message="No file uploaded.", status_code=400)

    try:
        filename = save_upload(file, 'project_samples')
        return success_response(data={
            'filename': filename,
            'url': f"/uploads/project_samples/{filename}"
        }, message="Sample file uploaded successfully.")
    except Exception as e:
        return error_response(message=f"Upload failed: {str(e)}", status_code=422)


def apply_to_project(current_user: dict, project_id: int):
    """
    POST /api/projects/<id>/apply
    Apply to a project as an editor.
    """
    from models.proposal_model import Proposal

    if current_user.get('role') != 'editor':
        return error_response(message="Only editors can apply to projects.", status_code=403)

    project = Project.query.get(project_id)
    if not project or project.status == ProjectStatus.DELETED:
        return error_response(message="Project not found.", status_code=404)

    existing = Proposal.query.filter_by(project_id=project_id, editor_id=current_user['user_id']).first()
    if existing:
        return error_response(message="You have already applied to this project.", status_code=400)

    data = request.get_json(silent=True) or {}
    proposal = Proposal(
        project_id=project_id,
        editor_id=current_user['user_id'],
        cover_letter=data.get('cover_letter', 'Submitted application via project page.'),
        proposed_price=data.get('proposed_price', project.budget or 0),
        status='pending'
    )

    try:
        db.session.add(proposal)
        db.session.commit()

        # Trigger notification to client
        from utils.notification_helper import create_notification
        create_notification(
            user_id=project.client_id,
            title="New Proposal Submitted",
            message=f"An editor applied to your project '{project.title}'.",
            type_str="proposal_submitted",
            related_project_id=project_id
        )

        return success_response(data={'proposal': proposal.to_dict()}, message="Application submitted successfully.")
    except Exception as e:
        db.session.rollback()
        return error_response(message=f"Failed to submit application: {str(e)}", status_code=500)


def hire_editor(current_user: dict, project_id: int):
    """
    POST /api/projects/<id>/hire
    Client hires an editor for the project.
    Changes project status to IN_PROGRESS and sends notifications.
    """
    from models.proposal_model import Proposal
    from utils.notification_helper import create_notification

    if current_user.get('role') != 'client':
        return error_response(message="Only clients can hire editors.", status_code=403)

    project = Project.query.get(project_id)
    if not project or project.status == ProjectStatus.DELETED:
        return error_response(message="Project not found.", status_code=404)

    if project.client_id != current_user['user_id']:
        return error_response(message="You can only hire editors for your own projects.", status_code=403)

    data = request.get_json(silent=True) or {}
    editor_id = data.get('editor_id')
    if not editor_id:
        return error_response(message="editor_id is required.", status_code=400)

    proposal = Proposal.query.filter_by(project_id=project_id, editor_id=editor_id).first()
    if not proposal:
        return error_response(message="Proposal from this editor not found.", status_code=404)

    try:
        # Update project status and hired_editor_id
        project.hired_editor_id = editor_id
        project.status = ProjectStatus.IN_PROGRESS

        # Update proposals status
        proposal.status = 'accepted'

        other_proposals = Proposal.query.filter(
            Proposal.project_id == project_id,
            Proposal.id != proposal.id
        ).all()
        for p in other_proposals:
            p.status = 'rejected'
            create_notification(
                user_id=p.editor_id,
                title="Proposal Rejected",
                message=f"Your proposal for project '{project.title}' was not selected.",
                type_str="proposal_rejected",
                related_project_id=project_id
            )

        db.session.commit()

        # Notify hired editor
        create_notification(
            user_id=editor_id,
            title="Proposal Accepted / Project Assigned",
            message=f"Congratulations! You were hired for project '{project.title}'.",
            type_str="proposal_accepted",
            related_project_id=project_id
        )

        # Notify client
        create_notification(
            user_id=project.client_id,
            title="Project Assigned & In Progress",
            message=f"Project '{project.title}' status is now In Progress.",
            type_str="project_assigned",
            related_project_id=project_id
        )

        return success_response(data={'project': project.to_dict()}, message="Editor hired successfully. Project status updated to In Progress.")
    except Exception as e:
        db.session.rollback()
        return error_response(message=f"Failed to hire editor: {str(e)}", status_code=500)


def editor_update_progress(current_user: dict, project_id: int):
    """
    PATCH /api/projects/<id>/editor-progress
    Editor updates the project progress (e.g. pending, accepted, in_progress).
    """
    if current_user.get('role') != 'editor':
        return error_response(message="Only editors can update project progress.", status_code=403)

    project = Project.query.get(project_id)
    if not project or project.status == ProjectStatus.DELETED:
        return error_response(message="Project not found.", status_code=404)

    if project.hired_editor_id != current_user['user_id']:
        return error_response(message="You are not hired for this project.", status_code=403)

    data = request.get_json(silent=True) or {}
    new_status_str = (data.get('status') or '').strip().lower()

    # Editors should only switch between working statuses
    allowed_statuses = ['pending', 'accepted', 'in_progress']
    if new_status_str not in allowed_statuses:
        return error_response(message=f"Invalid status. Editors can only set: {', '.join(allowed_statuses)}", status_code=422)

    try:
        new_status = ProjectStatus(new_status_str)
        project.status = new_status
        project.add_timeline_event(new_status.value, f"Progress updated to {new_status.value}", "Updated by Editor")
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return error_response(message="Failed to update progress.", status_code=500)

    return success_response(data={'project': project.to_dict()}, message=f"Project progress updated to {new_status.value}.")


def editor_submit_project(current_user: dict, project_id: int):
    """
    POST /api/projects/<id>/submit
    Editor submits completed files and notes. 
    Changes status to UNDER_REVIEW, notifies client.
    """
    from utils.notification_helper import create_notification
    from utils.upload_helper import save_upload
    from datetime import datetime, timezone

    if current_user.get('role') != 'editor':
        return error_response(message="Only editors can submit projects.", status_code=403)

    project = Project.query.get(project_id)
    if not project or project.status == ProjectStatus.DELETED:
        return error_response(message="Project not found.", status_code=404)

    if project.hired_editor_id != current_user['user_id']:
        return error_response(message="You are not hired for this project.", status_code=403)

    notes = request.form.get('notes', '')
    file = request.files.get('file')

    try:
        # Save file if provided
        file_info = None
        if file:
            filename = save_upload(file, 'project_submissions')
            file_info = {
                'filename': filename,
                'url': f"/uploads/project_submissions/{filename}",
                'uploaded_by': current_user['user_id'],
                'notes': notes,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            p_files = list(project.project_files or [])
            p_files.append(file_info)
            project.project_files = p_files

        # Update Timeline
        project.add_timeline_event('under_review', "Project Submitted", f"Editor submitted work for review. Notes: {notes}")
        project.status = ProjectStatus.UNDER_REVIEW
        project.payment_status = 'pending'

        db.session.commit()

        # Notify Client
        create_notification(
            user_id=project.client_id,
            title="Project Ready for Review",
            message=f"The editor has submitted work for '{project.title}'. Please review.",
            type_str="project_submitted",
            related_project_id=project_id
        )

        return success_response(data={'project': project.to_dict()}, message="Project submitted for review successfully.")

    except Exception as e:
        db.session.rollback()
        return error_response(message=f"Submission failed: {str(e)}", status_code=500)


def client_approve_project(current_user: dict, project_id: int):
    """
    POST /api/projects/<id>/approve
    Deprecated in favor of the payment flow.
    """
    return error_response(
        message="Direct approval is deprecated. Please use the payment checkout flow (/api/payments/create-order) to approve and pay for the project.",
        status_code=400
    )


