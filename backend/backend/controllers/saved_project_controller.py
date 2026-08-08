"""
============================================================
ClipConnect - Saved Project Controller
============================================================
Handles saving, removing, and retrieving saved projects for Editors.
============================================================
"""

from database import db
from models.project_model import Project, ProjectStatus
from models.saved_project_model import SavedProject
from utils.response_helper import success_response, error_response

def save_project(current_user: dict, project_id: int):
    """
    POST /api/projects/<id>/save
    Save/Bookmark a project for an editor.
    """
    if current_user.get('role') != 'editor':
        return error_response(message="Only editors can save projects.", status_code=403)

    project = Project.query.get(project_id)
    if not project or project.status == ProjectStatus.DELETED:
        return error_response(message="Project not found.", status_code=404)

    existing = SavedProject.query.filter_by(
        editor_id=current_user['user_id'],
        project_id=project_id
    ).first()

    if existing:
        return success_response(data={'saved_project': existing.to_dict()}, message="Project is already saved.")

    saved_entry = SavedProject(
        editor_id=current_user['user_id'],
        project_id=project_id
    )

    try:
        db.session.add(saved_entry)
        db.session.commit()
        return success_response(data={'saved_project': saved_entry.to_dict()}, message="Project saved successfully.")
    except Exception as e:
        db.session.rollback()
        return error_response(message=f"Failed to save project: {str(e)}", status_code=500)


def unsave_project(current_user: dict, project_id: int):
    """
    DELETE /api/projects/<id>/save
    Remove a saved project for an editor.
    """
    if current_user.get('role') != 'editor':
        return error_response(message="Only editors can unsave projects.", status_code=403)

    existing = SavedProject.query.filter_by(
        editor_id=current_user['user_id'],
        project_id=project_id
    ).first()

    if not existing:
        return error_response(message="Project is not in your saved list.", status_code=404)

    try:
        db.session.delete(existing)
        db.session.commit()
        return success_response(message="Project removed from saved list.")
    except Exception as e:
        db.session.rollback()
        return error_response(message=f"Failed to remove saved project: {str(e)}", status_code=500)


def get_saved_projects(current_user: dict):
    """
    GET /api/projects/saved
    Get list of all projects saved by the logged-in editor.
    """
    if current_user.get('role') != 'editor':
        return error_response(message="Only editors have saved projects.", status_code=403)

    saved_entries = SavedProject.query.filter_by(editor_id=current_user['user_id']).order_by(SavedProject.created_at.desc()).all()
    
    projects = []
    for entry in saved_entries:
        if entry.project and entry.project.status != ProjectStatus.DELETED:
            p_dict = entry.project.to_dict()
            p_dict['saved_at'] = entry.created_at.isoformat() if entry.created_at else None
            p_dict['is_saved'] = True
            projects.append(p_dict)

    return success_response(data={'projects': projects}, message=f"Fetched {len(projects)} saved projects.")
