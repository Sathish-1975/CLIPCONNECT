"""
============================================================
ClipConnect - AI Feature Routes
============================================================
Why this file exists:
  Exposes REST API endpoints for AI-assisted editor recommendations, automated job description
  generation, and natural language search query parsing.

Routes:
  POST /api/ai/recommend-editors  -> AI Smart Match algorithm
  POST /api/ai/generate-description -> AI Job Description generator
  GET  /api/ai/search               -> Natural language search parser

How it integrates with the rest of the application:
  - Registered under prefix `/api/ai` in `routes/__init__.py`.
  - Used by `ai-tools.js` on frontend forms and search bars.
============================================================
"""

from flask import Blueprint
from middleware.auth_middleware import token_required
import controllers.ai_controller as ai_ctrl

ai_bp = Blueprint('ai_bp', __name__)


@ai_bp.route('/recommend-editors', methods=['POST'])
def recommend_editors():
    """POST /api/ai/recommend-editors — Get AI editor recommendations."""
    return ai_ctrl.recommend_editors()


@ai_bp.route('/generate-description', methods=['POST'])
@token_required
def generate_description(current_user):
    """POST /api/ai/generate-description — Generate AI project description."""
    return ai_ctrl.generate_description()


@ai_bp.route('/search', methods=['GET'])
def natural_language_search():
    """GET /api/ai/search?q=... — Parse natural language search."""
    return ai_ctrl.natural_language_search()
