"""
============================================================
ClipConnect - Flask Application Entry Point
============================================================
Purpose:
    Creates, configures, and runs the Flask application.
    This is the MAIN file that starts the backend server.

Architecture:
    app.py uses the "Application Factory" pattern:
    - Config is loaded from config.py
    - SQLAlchemy db is initialized with the app (not at import time)
    - All blueprints/routes are registered here
    - Database tables are created if they don't exist

How to run:
    cd backend
    python app.py
    
    OR using Flask CLI:
    flask run --port=5000

API Base URL:
    http://localhost:5000/api

Available Endpoints (Week 1):
    GET  /                      --> API info
    GET  /api/health            --> Server health check
    POST /api/auth/register     --> User registration
    POST /api/auth/login        --> User login
    GET  /api/auth/me           --> Get current user (JWT required)
    GET  /api/auth/health       --> Auth service health
============================================================
"""

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables FIRST before any other imports
load_dotenv()

# Import our modules
from config import get_config
from database import db


# ============================================================
# Application Factory Function
# ============================================================

def create_app(config_class=None):
    """
    Application Factory: Creates and configures the Flask app.

    Using a factory function (instead of a global app object) allows:
        - Running multiple app instances with different configs
        - Easy testing with test configurations
        - Avoiding circular imports

    Args:
        config_class: Config class to use (auto-detected from FLASK_ENV if None)

    Returns:
        Flask: Configured Flask application instance
    """

    # --------------------------------------------------------
    # Step 1: Create Flask App
    # --------------------------------------------------------
    app = Flask(__name__)

    # --------------------------------------------------------
    # Step 2: Load Configuration
    # --------------------------------------------------------
    if config_class is None:
        config_class = get_config()  # Auto-selects based on FLASK_ENV

    app.config.from_object(config_class)

    # --------------------------------------------------------
    # Step 3: Configure Logging
    # --------------------------------------------------------
    if app.config.get('DEBUG'):
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s]: %(message)s'
        )

    app.logger.info(f"[START] Starting {app.config.get('APP_NAME')} v{app.config.get('APP_VERSION')}")
    app.logger.info(f"[ENV]   Environment: {os.environ.get('FLASK_ENV', 'development')}")

    # --------------------------------------------------------
    # Step 4: Initialize Extensions (bind to app instance)
    # --------------------------------------------------------

    # Initialize SQLAlchemy with this app
    # db was created in database/__init__.py without an app
    # This line binds it to our specific app instance
    db.init_app(app)
    app.logger.info("[OK]    SQLAlchemy initialized")

    # Initialize CORS (Cross-Origin Resource Sharing)
    # Allows frontend (different port) to call our backend API
    cors_origins = app.config.get('CORS_ORIGINS', ['*'])
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": cors_origins,
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
                "expose_headers": ["Content-Range", "X-Total-Count"]
            }
        },
        supports_credentials=True
    )
    app.logger.info(f"[OK]    CORS configured for origins: {cors_origins}")

    # --------------------------------------------------------
    # Step 5: Register Route Blueprints
    # --------------------------------------------------------
    with app.app_context():
        from routes import register_all_blueprints
        register_all_blueprints(app)
        app.logger.info("[OK]    All route blueprints registered")

    # --------------------------------------------------------
    # Step 6: Create Database Tables
    # --------------------------------------------------------
    with app.app_context():
        try:
            # Import all models so SQLAlchemy knows about them
            from models import User, EditorProfile, ClientProfile   # noqa: F401

            # Create all tables that don't exist yet
            # In production, use Flask-Migrate (flask db upgrade) instead
            db.create_all()
            app.logger.info("[OK]    Database tables created (or already exist)")

        except Exception as e:
            app.logger.error(f"[ERROR] Database setup failed: {str(e)}")
            app.logger.error("[HINT]  Make sure PostgreSQL is running and DATABASE_URL is correct in .env")
            # Don't crash the app — it might still work if tables already exist

    # --------------------------------------------------------
    # Step 7: Register Root Routes (health checks, info)
    # --------------------------------------------------------
    register_root_routes(app)

    # --------------------------------------------------------
    # Step 8: Register Global Error Handlers
    # --------------------------------------------------------
    register_error_handlers(app)

    return app


# ============================================================
# Root Routes (non-blueprint, attached directly to app)
# ============================================================

def register_root_routes(app):
    """Register top-level utility routes directly on the Flask app."""

    @app.route('/', methods=['GET'])
    def index():
        """
        GET /
        API root — returns project info.
        """
        return jsonify({
            "success": True,
            "app": app.config.get('APP_NAME', 'ClipConnect'),
            "version": app.config.get('APP_VERSION', '1.0.0'),
            "description": "ClipConnect API - Freelance Video Editor Marketplace",
            "status": "running",
            "endpoints": {
                "auth": "/api/auth",
                "health": "/api/health"
            },
            "docs": "API documentation coming soon"
        })

    @app.route('/api/health', methods=['GET'])
    def health_check():
        """
        GET /api/health
        Full health check — tests DB connection too.
        """
        db_status = "connected"
        try:
            # Test DB connection
            db.session.execute(db.text('SELECT 1'))
        except Exception as e:
            db_status = f"error: {str(e)}"

        return jsonify({
            "success": True,
            "status": "healthy",
            "app": app.config.get('APP_NAME'),
            "database": db_status,
            "environment": os.environ.get('FLASK_ENV', 'development')
        })

    @app.route('/uploads/<path:filepath>', methods=['GET'])
    def serve_uploads(filepath):
        """
        GET /uploads/<folder>/<filename>
        Serve uploaded files (avatars, banners, resumes, portfolio images).
        Example: GET /uploads/avatars/20240101_abc123.jpg
        """
        from flask import send_from_directory
        upload_base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
        return send_from_directory(upload_base, filepath)


# ============================================================
# Global Error Handlers
# ============================================================

def register_error_handlers(app):
    """
    Register global HTTP error handlers.
    These catch errors that aren't handled by route functions.
    Returns consistent JSON instead of HTML error pages.
    """

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({
            "success": False,
            "message": "Bad request. Please check the data you sent.",
            "status_code": 400
        }), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({
            "success": False,
            "message": "Authentication required. Please login.",
            "status_code": 401
        }), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({
            "success": False,
            "message": "You don't have permission to access this resource.",
            "status_code": 403
        }), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            "success": False,
            "message": f"The requested URL was not found on this server.",
            "status_code": 404
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({
            "success": False,
            "message": "HTTP method not allowed for this endpoint.",
            "status_code": 405
        }), 405

    @app.errorhandler(422)
    def unprocessable_entity(e):
        return jsonify({
            "success": False,
            "message": "Unprocessable entity. Validation error.",
            "status_code": 422
        }), 422

    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f"Internal Server Error: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Internal server error. Our team has been notified.",
            "status_code": 500
        }), 500


# ============================================================
# Application Entry Point
# ============================================================

# Create the Flask app instance
app = create_app()

if __name__ == '__main__':
    """
    Run the development server.
    In production, use gunicorn: gunicorn app:app --workers=4
    """
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

    print("\n" + "="*60)
    print(f"  ClipConnect API Server")
    print(f"  Running at: http://localhost:{port}")
    print(f"  Health check: http://localhost:{port}/api/health")
    print(f"  Auth API: http://localhost:{port}/api/auth")
    print(f"  Debug mode: {debug}")
    print("="*60 + "\n")

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
