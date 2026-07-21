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


def register_all_blueprints(app):
    """
    Register all route blueprints with the Flask application.

    URL Prefixes:
        /api/auth   → auth_bp   (register, login, me)
        /api/users  → user_bp   (editor profiles, uploads, browse)

    Note: /uploads/* static serving is handled inside user_bp
          and registered at the app level in app.py.
    """
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')

    # Week 3+ (uncomment when ready):
    # from routes.gig_routes   import gig_bp
    # from routes.order_routes import order_bp
    # app.register_blueprint(gig_bp,   url_prefix='/api/gigs')
    # app.register_blueprint(order_bp, url_prefix='/api/orders')

    app.logger.info("[OK] All blueprints registered successfully.")
