"""
============================================================
ClipConnect - Project Routes
============================================================
Why this file exists:
  Exposes REST API endpoints for client project management.

Routes:
  POST   /api/projects                -> Create project (Draft or Published)
  GET    /api/projects                -> List public published projects
  GET    /api/projects/my             -> List client's own projects
  GET    /api/projects/<id>           -> Get single project details
  PUT    /api/projects/<id>           -> Edit project details
  PATCH  /api/projects/<id>/status    -> Change status (Publish / Close / Draft)
  DELETE /api/projects/<id>           -> Delete project (Soft delete)
  POST   /api/projects/upload-sample  -> Upload sample reference file
============================================================
"""

from flask import Blueprint
from middleware.auth_middleware import token_required
import controllers.project_controller as project_ctrl

project_bp = Blueprint('project_bp', __name__)


@project_bp.route('', methods=['POST'])
@token_required
def create_project(current_user):
    """POST /api/projects — Create a project."""
    return project_ctrl.create_project(current_user)


@project_bp.route('', methods=['GET'])
def get_public_projects():
    """GET /api/projects — List public published projects."""
    return project_ctrl.get_public_projects()


@project_bp.route('/my', methods=['GET'])
@token_required
def get_my_projects(current_user):
    """GET /api/projects/my — List logged in client's projects."""
    return project_ctrl.get_my_projects(current_user)


@project_bp.route('/<int:project_id>', methods=['GET'])
def get_project_by_id(project_id):
    """GET /api/projects/<id> — Get project details."""
    return project_ctrl.get_project_by_id(project_id)


@project_bp.route('/<int:project_id>', methods=['PUT'])
@token_required
def update_project(current_user, project_id):
    """PUT /api/projects/<id> — Edit project details."""
    return project_ctrl.update_project(current_user, project_id)


@project_bp.route('/<int:project_id>/status', methods=['PATCH'])
@token_required
def change_project_status(current_user, project_id):
    """PATCH /api/projects/<id>/status — Change status (Draft/Publish/Close)."""
    return project_ctrl.change_project_status(current_user, project_id)


@project_bp.route('/<int:project_id>', methods=['DELETE'])
@token_required
def delete_project(current_user, project_id):
    """DELETE /api/projects/<id> — Delete project."""
    return project_ctrl.delete_project(current_user, project_id)


@project_bp.route('/upload-sample', methods=['POST'])
@token_required
def upload_sample(current_user):
    """POST /api/projects/upload-sample — Upload reference file."""
    return project_ctrl.upload_sample_file(current_user)


import controllers.saved_project_controller as saved_project_ctrl


@project_bp.route('/saved', methods=['GET'])
@token_required
def get_saved_projects(current_user):
    """GET /api/projects/saved — List saved projects for editor."""
    return saved_project_ctrl.get_saved_projects(current_user)


@project_bp.route('/<int:project_id>/save', methods=['POST'])
@token_required
def save_project(current_user, project_id):
    """POST /api/projects/<id>/save — Save project."""
    return saved_project_ctrl.save_project(current_user, project_id)


@project_bp.route('/<int:project_id>/save', methods=['DELETE'])
@token_required
def unsave_project(current_user, project_id):
    """DELETE /api/projects/<id>/save — Remove saved project."""
    return saved_project_ctrl.unsave_project(current_user, project_id)


@project_bp.route('/<int:project_id>/hire', methods=['POST'])
@token_required
def hire_editor(current_user, project_id):
    """POST /api/projects/<id>/hire — Hire editor for project."""
    return project_ctrl.hire_editor(current_user, project_id)


@project_bp.route('/<int:project_id>/apply', methods=['POST'])
@token_required
def apply_to_project(current_user, project_id):
    """POST /api/projects/<id>/apply — Editor applies to project."""
    return project_ctrl.apply_to_project(current_user, project_id)


import controllers.revision_controller as revision_ctrl


@project_bp.route('/<int:project_id>/revisions', methods=['POST'])
@token_required
def request_revision(current_user, project_id):
    """POST /api/projects/<id>/revisions — Submit a revision request."""
    return revision_ctrl.request_revision(current_user, project_id)


@project_bp.route('/<int:project_id>/revisions', methods=['GET'])
@token_required
def get_project_revisions(current_user, project_id):
    """GET /api/projects/<id>/revisions — List revision history."""
    return revision_ctrl.get_project_revisions(current_user, project_id)


@project_bp.route('/<int:project_id>/revisions/<int:revision_id>', methods=['PUT'])
@token_required
def update_revision(current_user, project_id, revision_id):
    """PUT /api/projects/<id>/revisions/<rev_id> — Update revision / upload updated work."""
    return revision_ctrl.update_revision(current_user, project_id, revision_id)



