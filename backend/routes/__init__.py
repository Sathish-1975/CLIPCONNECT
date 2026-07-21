"""
============================================================
ClipConnect - Routes Package Initialization
============================================================
Purpose:
    Collects all route blueprints and registers them in app.py.

What is a Flask Blueprint?
    A Blueprint is a way to organize routes into logical groups.
    Each feature area (auth, users, gigs, orders) gets its own Blueprint.
    app.py registers all blueprints with their URL prefixes.

Usage in app.py:
    from routes import register_all_blueprints
    register_all_blueprints(app)
============================================================
"""

from routes.auth_routes import auth_bp


def register_all_blueprints(app):
    """
    Register all route blueprints with the Flask application.
    
    Args:
        app: Flask application instance
    
    URL Prefixes:
        /api/auth   --> auth_bp   (registration, login, profile)
    """
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    # Future blueprints (Week 2+):
    # app.register_blueprint(user_bp,   url_prefix='/api/users')
    # app.register_blueprint(gig_bp,    url_prefix='/api/gigs')
    # app.register_blueprint(order_bp,  url_prefix='/api/orders')
    # app.register_blueprint(review_bp, url_prefix='/api/reviews')

    app.logger.info("[OK] All blueprints registered successfully.")
