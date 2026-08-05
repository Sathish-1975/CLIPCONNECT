from flask import Blueprint, request
from controllers import invoice_controller
from middleware.auth_middleware import token_required

invoice_bp = Blueprint('invoices', __name__)

@invoice_bp.route('/<int:project_id>/download', methods=['GET'])
@token_required
def download_invoice(current_user, project_id):
    """
    GET /api/invoices/<project_id>/download
    Returns an HTML invoice for the specified project.
    """
    return invoice_controller.generate_invoice_html(current_user, project_id)
