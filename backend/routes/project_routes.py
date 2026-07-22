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
