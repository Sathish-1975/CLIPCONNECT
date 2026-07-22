"""
============================================================
ClipConnect - Routes Package Initialization
============================================================
Registers all Flask Blueprints with their URL prefixes.
Add each new feature blueprint here as the project grows.
============================================================
"""

from routes.auth_routes import auth_bp
from routes.user_routes import user_bp
from routes.api_routes import api_bp
from routes.project_routes import project_bp


def register_all_blueprints(app):
    """
    Register all route blueprints with the Flask application.

    URL Prefixes:
        /api/auth     → auth_bp      (register, login, me)
        /api/users    → user_bp      (editor profiles, uploads, browse)
        /api/projects → project_bp   (project posting system)
        /api          → api_bp       (simplified REST API endpoints)
    """
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(project_bp, url_prefix='/api/projects')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Week 3+ (uncomment when ready):
    # from routes.gig_routes   import gig_bp
    # from routes.order_routes import order_bp
    # app.register_blueprint(gig_bp,   url_prefix='/api/gigs')
    # app.register_blueprint(order_bp, url_prefix='/api/orders')

    app.logger.info("[OK] All blueprints registered successfully.")
